import logging
from datetime import timedelta
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.email import send_password_reset_email, send_verification_email
from app.core.security import (
    EMAIL_VERIFICATION_TTL,
    RESET_TTL,
    SESSION_TTL,
    create_email_verification_token,
    create_reset_token,
    create_session_token,
    hash_password,
    hash_reset_token,
    read_session_claims,
    utc_naive_now,
    verify_password,
)
from app.db.session import get_db
from app.models import EmailVerificationToken, PasswordResetToken, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
    WorkspaceAccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")
SESSION_COOKIE = "almasi_session"
WORKSPACE_ROUTER = APIRouter(prefix="/workspaces")
GENERIC_RESET_MESSAGE = (
    "If an account matches that email, a password reset link will be sent."
)


def require_auth_secret(settings: Settings) -> str:
    if (
        not settings.auth_secret_key
        or len(settings.auth_secret_key.encode("utf-8")) < 32
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account services are not configured. Set AUTH_SECRET_KEY to at least 32 bytes.",
        )
    return settings.auth_secret_key


def require_trusted_origin(
    request: Request, settings: Settings = Depends(get_settings)
) -> None:
    if request.headers.get("origin") not in settings.cors_origin_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed.",
        )


def set_session_cookie(response: Response, user: User, settings: Settings) -> None:
    token = create_session_token(
        user.id, user.session_version, require_auth_secret(settings)
    )
    is_production = settings.app_env.lower() == "production"
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )


def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    secret = require_auth_secret(settings)
    token = request.cookies.get(SESSION_COOKIE)
    claims = read_session_claims(token, secret) if token else None
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required.")
    user_id, session_version = claims
    user = db.get(User, user_id)
    if (
        user is None
        or not user.is_active
        or user.email_verified_at is None
        or user.session_version != session_version
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required.")
    return user


def require_role(role: str | tuple[str, ...]):
    allowed_roles = (role,) if isinstance(role, str) else role

    def role_guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this workspace.",
            )
        return user

    return role_guard


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    _: None = Depends(require_trusted_origin),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    require_auth_secret(settings)
    user = User(
        name=data.name,
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        role="learner",
        created_at=utc_naive_now(),
        email_verified_at=None,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for that email address.",
        ) from exc
    user.email_verified_at = None
    db.commit()
    now = utc_naive_now()
    raw_token = create_email_verification_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_reset_token(raw_token),
            expires_at=now + EMAIL_VERIFICATION_TTL,
            created_at=now,
        )
    )
    db.commit()
    verification_url = (
        f"{settings.app_base_url.rstrip('/')}/auth?mode=verify"
        f"&token={quote(raw_token, safe='')}"
    )
    try:
        await send_verification_email(settings, user.email, user.name, verification_url)
    except (RuntimeError, httpx.HTTPError) as exc:
        logger.exception("Unable to deliver verification email for user id %s.", user.id)
        db.delete(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification email could not be sent. Please try again later.",
        ) from exc
    return user


@router.post("/login", response_model=UserResponse)
def login(
    data: LoginRequest,
    response: Response,
    _: None = Depends(require_trusted_origin),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    require_auth_secret(settings)
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user is not None and user.is_active and user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before signing in.",
        )
    if (
        user is None
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    set_session_cookie(response, user, settings)
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    _: None = Depends(require_trusted_origin),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    is_production = settings.app_env.lower() == "production"
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=is_production,
        httponly=True,
        samesite="none" if is_production else "lax",
    )
    return MessageResponse(message="Signed out.")


@router.get("/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    _: None = Depends(require_trusted_origin),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not settings.resend_api_key or not settings.resend_from_email:
        logger.error("Password reset requested before Resend email settings were configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery is not configured. Set RESEND_API_KEY and RESEND_FROM_EMAIL.",
        )

    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user is None:
        return MessageResponse(message=GENERIC_RESET_MESSAGE)

    now = utc_naive_now()
    recent_request = db.scalar(
        select(PasswordResetToken.id)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= now - timedelta(minutes=1),
        )
        .limit(1)
    )
    if recent_request is not None:
        return MessageResponse(message=GENERIC_RESET_MESSAGE)

    raw_token = create_reset_token()
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .values(used_at=now)
    )
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=now + RESET_TTL,
        used_at=None,
        created_at=now,
    )
    db.add(reset_record)
    db.commit()

    reset_url = (
        f"{settings.app_base_url.rstrip('/')}/auth?mode=reset"
        f"&token={quote(raw_token, safe='')}"
    )
    try:
        await send_password_reset_email(settings, user.email, user.name, reset_url)
    except (RuntimeError, httpx.HTTPError) as exc:
        logger.exception("Unable to deliver password reset email for user id %s.", user.id)
        db.delete(reset_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery email could not be sent. Please try again later.",
        ) from exc

    return MessageResponse(message=GENERIC_RESET_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    data: ResetPasswordRequest,
    _: None = Depends(require_trusted_origin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    now = utc_naive_now()
    reset_record = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == hash_reset_token(data.token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
    )
    if reset_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    user = db.get(User, reset_record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    user.password_hash = hash_password(data.password)
    user.session_version += 1
    reset_record.used_at = now
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_record.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.commit()
    return MessageResponse(message="Password updated. Please sign in again.")


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: Session = Depends(get_db)) -> MessageResponse:
    now = utc_naive_now()
    record = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_reset_token(token),
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )
    user.email_verified_at = now
    record.used_at = now
    db.commit()
    return MessageResponse(message="Email verified. You can now sign in.")


@WORKSPACE_ROUTER.get("/learner", response_model=WorkspaceAccessResponse)
def learner_workspace(
    user: User = Depends(require_role("learner")),
) -> WorkspaceAccessResponse:
    return WorkspaceAccessResponse(role=user.role, workspace="learner")


@WORKSPACE_ROUTER.get("/facilitator", response_model=WorkspaceAccessResponse)
def facilitator_workspace(
    user: User = Depends(require_role("facilitator")),
) -> WorkspaceAccessResponse:
    return WorkspaceAccessResponse(role=user.role, workspace="facilitator")


@WORKSPACE_ROUTER.get("/supervisor", response_model=WorkspaceAccessResponse)
def supervisor_workspace(
    user: User = Depends(require_role("supervisor")),
) -> WorkspaceAccessResponse:
    return WorkspaceAccessResponse(role=user.role, workspace="supervisor")


@WORKSPACE_ROUTER.get("/administrator", response_model=WorkspaceAccessResponse)
def administrator_workspace(
    user: User = Depends(require_role("administrator")),
) -> WorkspaceAccessResponse:
    return WorkspaceAccessResponse(role=user.role, workspace="administrator")

import argparse
import sys
from datetime import UTC, datetime
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import AuditLog, User
from app.schemas.auth import validate_password_strength

STAFF_ROLES = ("facilitator", "supervisor", "administrator")


def provision_staff_account(
    db: Session,
    *,
    name: str,
    email: str,
    role: str,
    password: str,
) -> User:
    if role not in STAFF_ROLES:
        raise ValueError("Only facilitator, supervisor, or administrator roles can be provisioned.")
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Name cannot be blank.")
    clean_email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    validate_password_strength(password)

    user = db.scalar(select(User).where(User.email == clean_email))
    now = datetime.now(UTC).replace(tzinfo=None)
    if user is None:
        user = User(
            name=clean_name,
            email=clean_email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            session_version=0,
            created_at=now,
        )
        db.add(user)
        db.flush()
    else:
        user.name = clean_name
        user.password_hash = hash_password(password)
        user.role = role
        user.is_active = True
        user.session_version += 1

    db.add(
        AuditLog(
            actor_id=None,
            action="staff_account_provisioned",
            entity_type="user",
            entity_id=user.id,
            affected_user_id=user.id,
            details={"role": role, "source": "provisioning_cli"},
            created_at=now,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Provision an authorized ALMASI staff account."
    )
    parser.add_argument("--name", required=True, help="Account holder's name")
    parser.add_argument("--email", required=True, help="Account email address")
    parser.add_argument("--role", required=True, choices=STAFF_ROLES)
    args = parser.parse_args()

    try:
        with SessionLocal() as db:
            clean_email = str(
                TypeAdapter(EmailStr).validate_python(args.email)
            ).lower()
            existing = db.scalar(select(User).where(User.email == clean_email))
            if existing is not None:
                confirmation = input(
                    "This account exists. Its role and password will be changed "
                    "and active sessions revoked. Continue? [y/N] "
                )
                if confirmation.strip().lower() != "y":
                    print("No changes were made.")
                    return 1

            password = getpass("New password: ")
            confirmation = getpass("Confirm password: ")
            if password != confirmation:
                print("Passwords do not match.", file=sys.stderr)
                return 1

            user = provision_staff_account(
                db,
                name=args.name,
                email=clean_email,
                role=args.role,
                password=password,
            )
    except (ValueError, ValidationError) as exc:
        print(f"Account was not provisioned: {exc}", file=sys.stderr)
        return 1
    except IntegrityError:
        print(
            "Account could not be provisioned because a conflicting database record exists.",
            file=sys.stderr,
        )
        return 1

    print(f"Provisioned {user.role} account for {user.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

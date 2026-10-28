import csv
from datetime import UTC, datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user, require_role
from app.core.security import utc_naive_now
from app.db.session import get_db
from app.models import (
    AssignmentSubmission,
    AuditLog,
    GroupFacilitator,
    GroupMembership,
    LearnerProgress,
    LearningModule,
    MentorshipGroup,
    MentorshipSession,
    ProgrammeAssignment,
    SessionAttendance,
    SessionReport,
    SubmissionFeedback,
    SubmissionRevision,
    User,
)
from app.schemas.programme import (
    AssignmentCreate,
    AssignmentResponse,
    AttendanceBatchUpdate,
    AttendanceResponse,
    FacilitatorGroupSummary,
    FacilitatorSubmissionResponse,
    FeedbackUpsert,
    GroupAssignmentsUpdate,
    GroupAssignmentsResponse,
    GroupCreate,
    GroupResponse,
    GroupStatusUpdate,
    GroupScheduleResponse,
    FacilitatorSessionReport,
    LearnerAttendanceResponse,
    ProgrammeRole,
    SessionCreate,
    SessionReportResponse,
    SessionReportUpsert,
    SessionStatusUpdate,
    SessionResponse,
    SubmissionUpsert,
    SupervisorProgrammeReport,
    UserAdminResponse,
    UserAdminUpdate,
)

learner_programme_router = APIRouter(prefix="/learner")
facilitator_router = APIRouter(prefix="/facilitator")
supervisor_programme_router = APIRouter(prefix="/supervisor")
administrator_router = APIRouter(prefix="/administrator")


def _audit(
    db: Session,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    affected_user_id: int | None = None,
    group_id: int | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            affected_user_id=affected_user_id,
            group_id=group_id,
            details=details or {},
            created_at=utc_naive_now(),
        )
    )


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _facilitator_has_group(db: Session, user_id: int, group_id: int) -> bool:
    return db.scalar(
        select(GroupFacilitator.id)
        .join(MentorshipGroup, MentorshipGroup.id == GroupFacilitator.group_id)
        .where(
            GroupFacilitator.facilitator_id == user_id,
            GroupFacilitator.group_id == group_id,
            GroupFacilitator.is_active.is_(True),
            MentorshipGroup.is_active.is_(True),
        )
    ) is not None


def _require_assigned_group(db: Session, user: User, group_id: int) -> MentorshipGroup:
    group = db.get(MentorshipGroup, group_id)
    if (
        group is None
        or not group.is_active
        or user.role != "facilitator"
        or not _facilitator_has_group(db, user.id, group_id)
    ):
        raise HTTPException(status_code=404, detail="Assigned group not found.")
    return group


def _require_assignment_member(
    db: Session, user_id: int, group_id: int
) -> bool:
    return db.scalar(
        select(GroupMembership.id)
        .join(MentorshipGroup, MentorshipGroup.id == GroupMembership.group_id)
        .where(
            GroupMembership.group_id == group_id,
            GroupMembership.learner_id == user_id,
            GroupMembership.is_active.is_(True),
            MentorshipGroup.is_active.is_(True),
        )
    ) is not None


def _session_response(
    db: Session, session: MentorshipSession
) -> SessionResponse:
    group = db.get(MentorshipGroup, session.group_id)
    module = db.get(LearningModule, session.module_id)
    return SessionResponse(
        id=session.id,
        group_id=session.group_id,
        group_name=group.name if group else "",
        module_id=session.module_id,
        module_title=module.title if module else "",
        title=session.title,
        facilitator_plan=session.facilitator_plan,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
    )


def _assignment_response(
    db: Session,
    assignment: ProgrammeAssignment,
    learner_id: int | None = None,
) -> AssignmentResponse:
    group = db.get(MentorshipGroup, assignment.group_id)
    module = db.get(LearningModule, assignment.module_id)
    submission = (
        db.scalar(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.learner_id == learner_id,
            )
        )
        if learner_id is not None
        else None
    )
    feedback = (
        db.scalar(
            select(SubmissionFeedback).where(
                SubmissionFeedback.submission_id == submission.id
            )
        )
        if submission is not None
        else None
    )
    return AssignmentResponse(
        id=assignment.id,
        group_id=assignment.group_id,
        group_name=group.name if group else "",
        module_id=assignment.module_id,
        module_title=module.title if module else "",
        session_id=assignment.session_id,
        title=assignment.title,
        instructions=assignment.instructions,
        due_at=assignment.due_at,
        status=assignment.status,
        submission_id=submission.id if submission else None,
        submission_status=submission.status if submission else None,
        submission_content=submission.content if submission else None,
        submitted_at=submission.submitted_at if submission else None,
        feedback=feedback.comments if feedback else None,
        score=feedback.score if feedback else None,
    )


def _group_response(db: Session, group: MentorshipGroup) -> GroupResponse:
    learner_count = db.scalar(
        select(func.count(GroupMembership.id)).where(
            GroupMembership.group_id == group.id,
            GroupMembership.is_active.is_(True),
        )
    ) or 0
    facilitator_names = db.scalars(
        select(User.name)
        .join(GroupFacilitator, GroupFacilitator.facilitator_id == User.id)
        .where(
            GroupFacilitator.group_id == group.id,
            GroupFacilitator.is_active.is_(True),
        )
        .order_by(User.name)
    ).all()
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        learner_count=learner_count,
        facilitator_names=list(facilitator_names),
    )


@learner_programme_router.get(
    "/assignments", response_model=list[AssignmentResponse]
)
def learner_assignments(
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> list[AssignmentResponse]:
    assignments = db.scalars(
        select(ProgrammeAssignment)
        .join(GroupMembership, GroupMembership.group_id == ProgrammeAssignment.group_id)
        .join(MentorshipGroup, MentorshipGroup.id == GroupMembership.group_id)
        .where(
            GroupMembership.learner_id == user.id,
            MentorshipGroup.is_active.is_(True),
            ProgrammeAssignment.status != "archived",
        )
        .order_by(ProgrammeAssignment.due_at, ProgrammeAssignment.id)
    ).all()
    return [_assignment_response(db, assignment, user.id) for assignment in assignments]


@learner_programme_router.put(
    "/assignments/{assignment_id}/submission",
    response_model=AssignmentResponse,
)
def save_learner_submission(
    assignment_id: int,
    data: SubmissionUpsert,
    submit: bool = Query(default=False),
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    assignment = db.get(ProgrammeAssignment, assignment_id)
    now = utc_naive_now()
    if (
        assignment is None
        or not _require_assignment_member(db, user.id, assignment.group_id)
    ):
        raise HTTPException(status_code=404, detail="Assignment not found.")
    if assignment.status != "open":
        raise HTTPException(status_code=409, detail="This assignment is not open.")
    if assignment.due_at is not None and _utc_naive(assignment.due_at) < now:
        raise HTTPException(status_code=409, detail="The assignment deadline has passed.")
    submission = db.scalar(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment.id,
            AssignmentSubmission.learner_id == user.id,
        )
    )
    if submission is not None and submission.status in ("locked", "submitted", "approved"):
        raise HTTPException(
            status_code=409,
            detail=(
                "This submission is awaiting review."
                if submission.status == "submitted"
                else "This submission has been approved and cannot be changed."
                if submission.status == "approved"
                else "This submission is locked."
            ),
        )
    is_resubmission = submission is not None and submission.status == "returned_for_improvement"
    if submission is None:
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            learner_id=user.id,
            content=data.content,
            status="submitted" if submit else "draft",
            submitted_at=now if submit else None,
            created_at=now,
            updated_at=now,
        )
        db.add(submission)
        db.flush()
    else:
        submission.content = data.content
        submission.status = "submitted" if submit else "draft"
        if submit:
            submission.submitted_at = now
        submission.updated_at = now
    db.add(
        SubmissionRevision(
            submission_id=submission.id,
            content=data.content,
            action=(
                "resubmitted"
                if submit and is_resubmission
                else "submitted"
                if submit
                else "saved"
            ),
            actor_id=user.id,
            created_at=now,
        )
    )
    _audit(
        db,
        user,
        "submission_saved",
        "submission",
        submission.id,
        affected_user_id=user.id,
        group_id=assignment.group_id,
        details={"submitted": submit},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="The submission changed at the same time. Reload and retry.",
        ) from exc
    db.refresh(assignment)
    return _assignment_response(db, assignment, user.id)


@learner_programme_router.get(
    "/attendance", response_model=list[LearnerAttendanceResponse]
)
def learner_attendance(
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> list[LearnerAttendanceResponse]:
    rows = db.execute(
        select(
            MentorshipSession,
            LearningModule.title,
            SessionAttendance.status,
        )
        .join(GroupMembership, GroupMembership.group_id == MentorshipSession.group_id)
        .join(LearningModule, LearningModule.id == MentorshipSession.module_id)
        .outerjoin(
            SessionAttendance,
            (SessionAttendance.session_id == MentorshipSession.id)
            & (SessionAttendance.learner_id == user.id),
        )
        .where(GroupMembership.learner_id == user.id)
        .order_by(MentorshipSession.starts_at.desc())
    ).all()
    return [
        LearnerAttendanceResponse(
            session_id=session.id,
            session_title=session.title,
            module_title=module_title,
            starts_at=session.starts_at,
            status=attendance_status,
        )
        for session, module_title, attendance_status in rows
    ]


@facilitator_router.get("/dashboard", response_model=GroupScheduleResponse)
def facilitator_dashboard(
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> GroupScheduleResponse:
    groups = db.scalars(
        select(MentorshipGroup)
        .join(GroupFacilitator, GroupFacilitator.group_id == MentorshipGroup.id)
        .where(
            GroupFacilitator.facilitator_id == user.id,
            GroupFacilitator.is_active.is_(True),
            MentorshipGroup.is_active.is_(True),
        )
        .order_by(MentorshipGroup.name)
    ).all()
    group_ids = [group.id for group in groups]
    if not group_ids:
        return GroupScheduleResponse(
            groups=[], sessions=[], assignments=[], submissions=[], reports=[]
        )

    session_rows = db.scalars(
        select(MentorshipSession)
        .where(
            MentorshipSession.group_id.in_(group_ids),
            MentorshipSession.status != "cancelled",
        )
        .order_by(MentorshipSession.starts_at)
    ).all()
    assignments = db.scalars(
        select(ProgrammeAssignment)
        .where(
            ProgrammeAssignment.group_id.in_(group_ids),
            ProgrammeAssignment.status != "archived",
        )
        .order_by(ProgrammeAssignment.due_at)
    ).all()
    submission_rows = db.execute(
        select(AssignmentSubmission, ProgrammeAssignment, User.name)
        .join(ProgrammeAssignment, ProgrammeAssignment.id == AssignmentSubmission.assignment_id)
        .join(User, User.id == AssignmentSubmission.learner_id)
        .where(
            ProgrammeAssignment.group_id.in_(group_ids),
            AssignmentSubmission.status.in_(("submitted", "approved", "returned_for_improvement", "locked")),
        )
        .order_by(AssignmentSubmission.submitted_at.desc())
    ).all()
    report_rows = db.execute(
        select(SessionReport, MentorshipSession.title, MentorshipGroup.name)
        .join(MentorshipSession, MentorshipSession.id == SessionReport.session_id)
        .join(MentorshipGroup, MentorshipGroup.id == SessionReport.group_id)
        .where(SessionReport.group_id.in_(group_ids))
        .order_by(MentorshipSession.starts_at.desc())
    ).all()
    responses = [
        FacilitatorSubmissionResponse(
            id=submission.id,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            group_id=assignment.group_id,
            learner_id=submission.learner_id,
            learner_name=learner_name,
            content=submission.content,
            status=submission.status,
            submitted_at=submission.submitted_at,
            feedback=(
                feedback.comments
                if (
                    feedback := db.scalar(
                        select(SubmissionFeedback).where(
                            SubmissionFeedback.submission_id == submission.id
                        )
                    )
                )
                else None
            ),
            score=feedback.score if feedback else None,
        )
        for submission, assignment, learner_name in submission_rows
    ]
    group_summaries = []
    for group in groups:
        learner_count = db.scalar(
            select(func.count(GroupMembership.id)).where(
                GroupMembership.group_id == group.id,
                GroupMembership.is_active.is_(True),
            )
        ) or 0
        upcoming_count = db.scalar(
            select(func.count(MentorshipSession.id)).where(
                MentorshipSession.group_id == group.id,
                MentorshipSession.status == "scheduled",
                MentorshipSession.starts_at >= utc_naive_now(),
            )
        ) or 0
        completed_count = db.scalar(
            select(func.count(distinct(LearnerProgress.id)))
            .join(GroupMembership, GroupMembership.learner_id == LearnerProgress.learner_id)
            .where(
                GroupMembership.group_id == group.id,
                GroupMembership.is_active.is_(True),
                LearnerProgress.is_completed.is_(True),
            )
        ) or 0
        published_module_count = db.scalar(
            select(func.count(LearningModule.id)).where(
                LearningModule.is_published.is_(True)
            )
        ) or 0
        eligible_module_count = learner_count * published_module_count
        past_session_count = db.scalar(
            select(func.count(MentorshipSession.id)).where(
                MentorshipSession.group_id == group.id,
                MentorshipSession.status != "cancelled",
                MentorshipSession.starts_at <= utc_naive_now(),
            )
        ) or 0
        attendance_count = db.scalar(
            select(func.count(SessionAttendance.id))
            .join(MentorshipSession, MentorshipSession.id == SessionAttendance.session_id)
            .where(
                MentorshipSession.group_id == group.id,
                MentorshipSession.status != "cancelled",
                MentorshipSession.starts_at <= utc_naive_now(),
            )
        ) or 0
        pending_count = db.scalar(
            select(func.count(AssignmentSubmission.id))
            .join(ProgrammeAssignment)
            .where(
                ProgrammeAssignment.group_id == group.id,
                AssignmentSubmission.status == "submitted",
            )
        ) or 0
        group_summaries.append(
            FacilitatorGroupSummary(
                id=group.id,
                name=group.name,
                learner_count=learner_count,
                upcoming_session_count=upcoming_count,
                pending_submission_count=pending_count,
                completed_module_records=completed_count,
                eligible_module_records=eligible_module_count,
                attendance_records=attendance_count,
                missing_attendance_records=max(
                    0, learner_count * past_session_count - attendance_count
                ),
            )
        )
    return GroupScheduleResponse(
        groups=group_summaries,
        sessions=[_session_response(db, session) for session in session_rows],
        assignments=[
            _assignment_response(db, assignment) for assignment in assignments
        ],
        submissions=responses,
        reports=[
            FacilitatorSessionReport(
                id=report.id,
                session_id=report.session_id,
                group_id=report.group_id,
                session_title=session_title,
                group_name=group_name,
                content=report.content,
                follow_up_actions=report.follow_up_actions,
                status=report.status,
                submitted_at=report.submitted_at,
            )
            for report, session_title, group_name in report_rows
        ],
    )


@facilitator_router.post(
    "/assignments", response_model=AssignmentResponse, status_code=201
)
def create_facilitator_assignment(
    data: AssignmentCreate,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    _require_assigned_group(db, user, data.group_id)
    if db.get(LearningModule, data.module_id) is None:
        raise HTTPException(status_code=404, detail="Module not found.")
    if data.session_id is not None:
        session = db.get(MentorshipSession, data.session_id)
        if (
            session is None
            or session.group_id != data.group_id
            or session.module_id != data.module_id
        ):
            raise HTTPException(status_code=404, detail="Assigned session not found.")
    now = utc_naive_now()
    assignment = ProgrammeAssignment(
        group_id=data.group_id,
        module_id=data.module_id,
        session_id=data.session_id,
        title=data.title,
        instructions=data.instructions,
        due_at=_utc_naive(data.due_at) if data.due_at else None,
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(assignment)
    db.flush()
    _audit(
        db,
        user,
        "assignment_created",
        "assignment",
        assignment.id,
        group_id=data.group_id,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create the assignment.") from exc
    db.refresh(assignment)
    return _assignment_response(db, assignment)


@facilitator_router.put("/assignments/{assignment_id}/lock")
def lock_assignment(
    assignment_id: int,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assignment = db.get(ProgrammeAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    _require_assigned_group(db, user, assignment.group_id)
    if assignment.status == "archived":
        raise HTTPException(status_code=409, detail="Archived assignments cannot be locked.")
    assignment.status = "locked"
    assignment.updated_at = utc_naive_now()
    _audit(
        db,
        user,
        "assignment_locked",
        "assignment",
        assignment.id,
        group_id=assignment.group_id,
    )
    db.commit()
    return {"assignment_id": assignment.id, "status": assignment.status}


@facilitator_router.put("/submissions/{submission_id}/lock")
def lock_submission(
    submission_id: int,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    submission = db.get(AssignmentSubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    assignment = db.get(ProgrammeAssignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    _require_assigned_group(db, user, assignment.group_id)
    if submission.status == "draft":
        raise HTTPException(status_code=409, detail="Draft submissions cannot be locked.")
    now = utc_naive_now()
    submission.status = "locked"
    submission.locked_at = now
    submission.locked_by_id = user.id
    submission.updated_at = now
    _audit(
        db,
        user,
        "submission_locked",
        "submission",
        submission.id,
        affected_user_id=submission.learner_id,
        group_id=assignment.group_id,
    )
    db.commit()
    return {"submission_id": submission.id, "status": submission.status}


@facilitator_router.put("/submissions/{submission_id}/feedback")
def review_submission(
    submission_id: int,
    data: FeedbackUpsert,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    submission = db.get(AssignmentSubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    assignment = db.get(ProgrammeAssignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    _require_assigned_group(db, user, assignment.group_id)
    if submission.status != "submitted":
        raise HTTPException(status_code=409, detail="Draft submissions cannot be reviewed.")
    now = utc_naive_now()
    feedback = db.scalar(
        select(SubmissionFeedback).where(
            SubmissionFeedback.submission_id == submission.id
        )
    )
    if feedback is None:
        feedback = SubmissionFeedback(
            submission_id=submission.id,
            facilitator_id=user.id,
            comments=data.comments,
            score=data.score,
            created_at=now,
            updated_at=now,
        )
        db.add(feedback)
    else:
        feedback.facilitator_id = user.id
        feedback.comments = data.comments
        feedback.score = data.score
        feedback.updated_at = now
    previous_status = submission.status
    if submission.status != "locked":
        submission.status = data.decision
    submission.reviewed_by_id = user.id
    submission.reviewed_at = now
    submission.updated_at = now
    _audit(
        db,
        user,
        "submission_feedback_saved",
        "submission",
        submission.id,
        affected_user_id=submission.learner_id,
        group_id=assignment.group_id,
        details={
            "previous_status": previous_status,
            "status": submission.status,
            "decision": data.decision,
        },
    )
    db.commit()
    return {
        "submission_id": submission.id,
        "status": submission.status,
        "reviewed_at": submission.reviewed_at,
    }


@facilitator_router.get(
    "/sessions/{session_id}/attendance",
    response_model=list[AttendanceResponse],
)
def get_group_attendance(
    session_id: int,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> list[AttendanceResponse]:
    session = db.get(MentorshipSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    _require_assigned_group(db, user, session.group_id)
    rows = db.execute(
        select(User.id, User.name, SessionAttendance.status, SessionAttendance.updated_at)
        .join(GroupMembership, GroupMembership.learner_id == User.id)
        .outerjoin(
            SessionAttendance,
            (SessionAttendance.learner_id == User.id)
            & (SessionAttendance.session_id == session.id),
        )
        .where(GroupMembership.group_id == session.group_id)
        .order_by(User.name)
    ).all()
    return [
        AttendanceResponse(
            learner_id=learner_id,
            learner_name=name,
            status=attendance_status,
            updated_at=updated_at,
        )
        for learner_id, name, attendance_status, updated_at in rows
    ]


@facilitator_router.put("/sessions/{session_id}/status")
def update_session_status(
    session_id: int,
    data: SessionStatusUpdate,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = db.get(MentorshipSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    _require_assigned_group(db, user, session.group_id)
    if data.status == "completed" and _utc_naive(session.ends_at) > utc_naive_now():
        raise HTTPException(status_code=409, detail="A future session cannot be marked completed.")
    session.status = data.status
    session.updated_at = utc_naive_now()
    _audit(
        db,
        user,
        "session_status_changed",
        "session",
        session.id,
        group_id=session.group_id,
        details={"status": session.status},
    )
    db.commit()
    return {"session_id": session.id, "status": session.status}


@facilitator_router.put(
    "/sessions/{session_id}/attendance",
    response_model=list[AttendanceResponse],
)
def update_group_attendance(
    session_id: int,
    data: AttendanceBatchUpdate,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> list[AttendanceResponse]:
    session = db.get(MentorshipSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    _require_assigned_group(db, user, session.group_id)
    learner_ids = {item.learner_id for item in data.records}
    members = set(
        db.scalars(
            select(GroupMembership.learner_id).where(
                GroupMembership.group_id == session.group_id,
                GroupMembership.learner_id.in_(learner_ids),
            )
        ).all()
    )
    if members != learner_ids:
        raise HTTPException(status_code=422, detail="Attendance contains a learner outside this group.")
    now = utc_naive_now()
    for item in data.records:
        record = db.scalar(
            select(SessionAttendance).where(
                SessionAttendance.session_id == session.id,
                SessionAttendance.learner_id == item.learner_id,
            )
        )
        previous_status = record.status if record else None
        if record is None:
            record = SessionAttendance(
                session_id=session.id,
                learner_id=item.learner_id,
                status=item.status,
                recorded_by_id=user.id,
                created_at=now,
                updated_at=now,
            )
            db.add(record)
        else:
            record.status = item.status
            record.recorded_by_id = user.id
            record.updated_at = now
        _audit(
            db,
            user,
            "attendance_recorded" if previous_status is None else "attendance_corrected",
            "attendance",
            record.id,
            affected_user_id=item.learner_id,
            group_id=session.group_id,
            details={"previous_status": previous_status, "status": item.status},
        )
    db.commit()
    return get_group_attendance(session.id, user, db)


@facilitator_router.put(
    "/sessions/{session_id}/report", response_model=SessionReportResponse
)
def save_session_report(
    session_id: int,
    data: SessionReportUpsert,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> SessionReportResponse:
    session = db.get(MentorshipSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    _require_assigned_group(db, user, session.group_id)
    now = utc_naive_now()
    report = db.scalar(
        select(SessionReport).where(SessionReport.session_id == session.id)
    )
    if report is None:
        report = SessionReport(
            session_id=session.id,
            group_id=session.group_id,
            facilitator_id=user.id,
            content=data.content,
            follow_up_actions=data.follow_up_actions,
            status="draft",
            submitted_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(report)
    elif report.status != "submitted":
        report.content = data.content
        report.follow_up_actions = data.follow_up_actions
        report.facilitator_id = user.id
        report.updated_at = now
    else:
        raise HTTPException(status_code=409, detail="This report has already been submitted.")
    db.flush()
    _audit(db, user, "session_report_saved", "session_report", report.id, group_id=session.group_id)
    db.commit()
    db.refresh(report)
    return SessionReportResponse.model_validate(report)


@facilitator_router.post("/sessions/{session_id}/report/submit")
def submit_session_report(
    session_id: int,
    user: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    report = db.scalar(
        select(SessionReport).where(SessionReport.session_id == session_id)
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Save a session report before submitting it.")
    _require_assigned_group(db, user, report.group_id)
    if report.status == "submitted":
        raise HTTPException(status_code=409, detail="This report has already been submitted.")
    if not report.content.strip():
        raise HTTPException(status_code=422, detail="A report must include session notes.")
    report.status = "submitted"
    report.submitted_at = utc_naive_now()
    report.updated_at = report.submitted_at
    _audit(db, user, "session_report_submitted", "session_report", report.id, group_id=report.group_id)
    db.commit()
    return {"report_id": report.id, "status": report.status, "submitted_at": report.submitted_at}


@supervisor_programme_router.get(
    "/reports", response_model=SupervisorProgrammeReport
)
def supervisor_programme_report(
    _: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
) -> SupervisorProgrammeReport:
    now = utc_naive_now()
    active_learners = db.scalar(
        select(func.count(User.id)).where(
            User.role == "learner",
            User.is_active.is_(True),
        )
    ) or 0
    active_facilitators = db.scalar(
        select(func.count(distinct(GroupFacilitator.facilitator_id)))
        .join(MentorshipGroup, MentorshipGroup.id == GroupFacilitator.group_id)
        .where(MentorshipGroup.is_active.is_(True))
    ) or 0
    active_groups = db.scalar(
        select(func.count(MentorshipGroup.id)).where(MentorshipGroup.is_active.is_(True))
    ) or 0
    published_modules = db.scalar(
        select(func.count(LearningModule.id)).where(LearningModule.is_published.is_(True))
    ) or 0
    completed_module_records = db.scalar(
        select(func.count(LearnerProgress.id)).where(LearnerProgress.is_completed.is_(True))
    ) or 0
    attendance_records = db.scalar(select(func.count(SessionAttendance.id))) or 0
    expected_attendance = db.scalar(
        select(func.count(GroupMembership.id))
        .select_from(MentorshipSession)
        .join(GroupMembership, GroupMembership.group_id == MentorshipSession.group_id)
        .where(
            MentorshipSession.status != "cancelled",
            MentorshipSession.starts_at <= now,
        )
    ) or 0
    attendance_recorded_for_past_sessions = db.scalar(
        select(func.count(SessionAttendance.id))
        .join(MentorshipSession, MentorshipSession.id == SessionAttendance.session_id)
        .where(
            MentorshipSession.status != "cancelled",
            MentorshipSession.starts_at <= now,
        )
    ) or 0
    submitted_assignments = db.scalar(
        select(func.count(AssignmentSubmission.id)).where(
            AssignmentSubmission.status.in_(("submitted", "approved", "returned_for_improvement", "locked"))
        )
    ) or 0
    awaiting_review = db.scalar(
        select(func.count(AssignmentSubmission.id)).where(
            AssignmentSubmission.status == "submitted"
        )
    ) or 0
    overdue_session_reports = db.scalar(
        select(func.count(MentorshipSession.id))
        .outerjoin(SessionReport, SessionReport.session_id == MentorshipSession.id)
        .where(
            MentorshipSession.status == "completed",
            MentorshipSession.ends_at <= now,
            (SessionReport.id.is_(None)) | (SessionReport.status != "submitted"),
        )
    ) or 0
    groups = db.scalars(
        select(MentorshipGroup)
        .where(MentorshipGroup.is_active.is_(True))
        .order_by(MentorshipGroup.name)
    ).all()
    completion_rows = db.execute(
        select(
            User.id,
            User.name,
            LearningModule.week_number,
            LearningModule.title,
            LearnerProgress.completed_at,
        )
        .join(LearnerProgress, LearnerProgress.learner_id == User.id)
        .join(LearningModule, LearningModule.id == LearnerProgress.module_id)
        .where(
            LearnerProgress.is_completed.is_(True),
            User.is_active.is_(True),
        )
        .order_by(LearnerProgress.completed_at.desc())
        .limit(200)
    ).all()
    return SupervisorProgrammeReport(
        active_learners=active_learners,
        active_facilitators=active_facilitators,
        active_groups=active_groups,
        published_modules=published_modules,
        completed_module_records=completed_module_records,
        attendance_records=attendance_records,
        missing_attendance_records=max(
            0, expected_attendance - attendance_recorded_for_past_sessions
        ),
        submitted_assignments=submitted_assignments,
        awaiting_review=awaiting_review,
        overdue_session_reports=overdue_session_reports,
        groups=[_group_response(db, group) for group in groups],
        completion_records=[
            {
                "learner_id": learner_id,
                "learner_name": learner_name,
                "week_number": week_number,
                "module_title": module_title,
                "completed_at": completed_at,
            }
            for learner_id, learner_name, week_number, module_title, completed_at in completion_rows
        ],
    )


@supervisor_programme_router.get("/reports/export")
def export_supervisor_report(
    user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
) -> Response:
    report = supervisor_programme_report(user, db)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Learner ID", "Learner", "Week", "Module", "Completed at"]
    )

    def safe_cell(value: object) -> object:
        text = str(value) if value is not None else ""
        return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text

    for record in report.completion_records:
        writer.writerow(
            [
                safe_cell(record["learner_id"]),
                safe_cell(record["learner_name"]),
                safe_cell(record["week_number"]),
                safe_cell(record["module_title"]),
                safe_cell(record["completed_at"]),
            ]
        )
    _audit(db, user, "programme_report_exported", "programme_report", details={"rows": len(report.completion_records)})
    db.commit()
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="almasi-progress-report.csv"'},
    )


@administrator_router.get("/users", response_model=list[UserAdminResponse])
def administrator_users(
    _: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> list[UserAdminResponse]:
    return [
        UserAdminResponse.model_validate(user)
        for user in db.scalars(select(User).order_by(User.name)).all()
    ]


@administrator_router.patch(
    "/users/{user_id}", response_model=UserAdminResponse
)
def update_user_account(
    user_id: int,
    data: UserAdminUpdate,
    actor: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> UserAdminResponse:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    next_role: ProgrammeRole = data.role or target.role
    next_active = target.is_active if data.is_active is None else data.is_active
    if target.id == actor.id and (
        next_role != "administrator" or not next_active
    ):
        raise HTTPException(status_code=409, detail="You cannot deactivate or demote your own account.")
    if target.role == "administrator" and (
        next_role != "administrator" or not next_active
    ):
        remaining_admins = db.scalar(
            select(func.count(User.id)).where(
                User.role == "administrator",
                User.is_active.is_(True),
                User.id != target.id,
            )
        ) or 0
        if remaining_admins == 0:
            raise HTTPException(status_code=409, detail="At least one active administrator must remain.")
    if next_role != target.role:
        if target.role == "facilitator":
            db.query(GroupFacilitator).filter_by(facilitator_id=target.id).update(
                {"is_active": False}
            )
        if target.role == "learner":
            db.query(GroupMembership).filter_by(learner_id=target.id).update(
                {"is_active": False}
            )
        target.session_version += 1
        _audit(db, actor, "account_role_changed", "user", target.id, affected_user_id=target.id, details={"from": target.role, "to": next_role})
    if next_active != target.is_active:
        target.session_version += 1
        _audit(db, actor, "account_active_status_changed", "user", target.id, affected_user_id=target.id, details={"is_active": next_active})
    target.role = next_role
    target.is_active = next_active
    db.commit()
    db.refresh(target)
    return UserAdminResponse.model_validate(target)


@administrator_router.get("/groups", response_model=list[GroupResponse])
def administrator_groups(
    _: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> list[GroupResponse]:
    groups = db.scalars(select(MentorshipGroup).order_by(MentorshipGroup.name)).all()
    return [_group_response(db, group) for group in groups]


@administrator_router.post("/groups", response_model=GroupResponse, status_code=201)
def create_group(
    data: GroupCreate,
    user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> GroupResponse:
    now = utc_naive_now()
    group = MentorshipGroup(
        name=data.name,
        description=data.description,
        is_active=True,
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(group)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A group with that name already exists.") from exc
    _audit(db, user, "group_created", "group", group.id, group_id=group.id)
    db.commit()
    db.refresh(group)
    return _group_response(db, group)


@administrator_router.get(
    "/groups/{group_id}/assignments",
    response_model=GroupAssignmentsResponse,
)
def get_group_assignments(
    group_id: int,
    _: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> GroupAssignmentsResponse:
    if db.get(MentorshipGroup, group_id) is None:
        raise HTTPException(status_code=404, detail="Group not found.")
    return GroupAssignmentsResponse(
        group_id=group_id,
        facilitator_ids=list(
            db.scalars(
                select(GroupFacilitator.facilitator_id).where(
                    GroupFacilitator.group_id == group_id,
                    GroupFacilitator.is_active.is_(True),
                )
            ).all()
        ),
        learner_ids=list(
            db.scalars(
                select(GroupMembership.learner_id).where(
                    GroupMembership.group_id == group_id,
                    GroupMembership.is_active.is_(True),
                )
            ).all()
        ),
    )


@administrator_router.patch("/groups/{group_id}")
def update_group_status(
    group_id: int,
    data: GroupStatusUpdate,
    user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    group = db.get(MentorshipGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found.")
    group.is_active = data.is_active
    group.updated_at = utc_naive_now()
    _audit(
        db,
        user,
        "group_active_status_changed",
        "group",
        group.id,
        group_id=group.id,
        details={"is_active": data.is_active},
    )
    db.commit()
    return {"group_id": group.id, "is_active": group.is_active}


@administrator_router.put("/groups/{group_id}/assignments")
def update_group_assignments(
    group_id: int,
    data: GroupAssignmentsUpdate,
    user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    group = db.get(MentorshipGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found.")
    facilitators = db.scalars(
        select(User).where(
            User.id.in_(data.facilitator_ids or [-1]),
            User.role == "facilitator",
            User.is_active.is_(True),
        )
    ).all()
    learners = db.scalars(
        select(User).where(
            User.id.in_(data.learner_ids or [-1]),
            User.role == "learner",
            User.is_active.is_(True),
        )
    ).all()
    if {item.id for item in facilitators} != set(data.facilitator_ids):
        raise HTTPException(status_code=422, detail="Every assigned facilitator must be an active facilitator account.")
    if {item.id for item in learners} != set(data.learner_ids):
        raise HTTPException(status_code=422, detail="Every group member must be an active learner account.")
    now = utc_naive_now()
    existing_facilitators = {
        item.facilitator_id: item
        for item in db.scalars(
            select(GroupFacilitator).where(GroupFacilitator.group_id == group.id)
        ).all()
    }
    for facilitator_id, membership in existing_facilitators.items():
        membership.is_active = facilitator_id in set(data.facilitator_ids)
    for facilitator in facilitators:
        membership = existing_facilitators.get(facilitator.id)
        if membership is None:
            db.add(
                GroupFacilitator(
                    group_id=group.id,
                    facilitator_id=facilitator.id,
                    is_active=True,
                    created_at=now,
                )
            )
        else:
            membership.is_active = True
    existing_learners = {
        item.learner_id: item
        for item in db.scalars(
            select(GroupMembership).where(GroupMembership.group_id == group.id)
        ).all()
    }
    for learner_id, membership in existing_learners.items():
        membership.is_active = learner_id in set(data.learner_ids)
    for learner in learners:
        membership = existing_learners.get(learner.id)
        if membership is None:
            db.add(
                GroupMembership(
                    group_id=group.id,
                    learner_id=learner.id,
                    is_active=True,
                    created_at=now,
                )
            )
        else:
            membership.is_active = True
    group.updated_at = now
    _audit(
        db,
        user,
        "group_assignments_changed",
        "group",
        group.id,
        group_id=group.id,
        details={
            "facilitator_count": len(facilitators),
            "learner_count": len(learners),
        },
    )
    db.commit()
    return {
        "group_id": group.id,
        "facilitator_count": len(facilitators),
        "learner_count": len(learners),
    }


@administrator_router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> SessionResponse:
    group = db.get(MentorshipGroup, data.group_id)
    module = db.get(LearningModule, data.module_id)
    if group is None or not group.is_active:
        raise HTTPException(status_code=404, detail="Active group not found.")
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found.")
    start = _utc_naive(data.starts_at)
    end = _utc_naive(data.ends_at)
    if end <= start:
        raise HTTPException(status_code=422, detail="Session end must be after its start.")
    now = utc_naive_now()
    session = MentorshipSession(
        group_id=group.id,
        module_id=module.id,
        title=data.title.strip(),
        facilitator_plan=data.facilitator_plan,
        starts_at=start,
        ends_at=end,
        status="scheduled",
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.flush()
    _audit(db, user, "session_created", "session", session.id, group_id=group.id)
    db.commit()
    db.refresh(session)
    return _session_response(db, session)


@administrator_router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    data: SessionCreate,
    user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> SessionResponse:
    session = db.get(MentorshipSession, session_id)
    group = db.get(MentorshipGroup, data.group_id)
    module = db.get(LearningModule, data.module_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if group is None or not group.is_active or module is None:
        raise HTTPException(status_code=404, detail="Active group or module not found.")
    starts_at = _utc_naive(data.starts_at)
    ends_at = _utc_naive(data.ends_at)
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="Session end must be after its start.")
    session.group_id = group.id
    session.module_id = module.id
    session.title = data.title.strip()
    session.facilitator_plan = data.facilitator_plan
    session.starts_at = starts_at
    session.ends_at = ends_at
    session.updated_at = utc_naive_now()
    _audit(db, user, "session_updated", "session", session.id, group_id=group.id)
    db.commit()
    db.refresh(session)
    return _session_response(db, session)

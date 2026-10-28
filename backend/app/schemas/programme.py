from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


ProgrammeRole = Literal["learner", "facilitator", "supervisor", "administrator"]
AttendanceStatus = Literal["present", "absent", "late", "excused"]


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Group name cannot be blank.")
        return value


class GroupAssignmentsUpdate(BaseModel):
    facilitator_ids: list[int] = Field(default_factory=list, max_length=50)
    learner_ids: list[int] = Field(default_factory=list, max_length=500)

    @field_validator("facilitator_ids", "learner_ids")
    @classmethod
    def unique_ids(cls, values: list[int]) -> list[int]:
        if len(values) != len(set(values)) or any(value < 1 for value in values):
            raise ValueError("IDs must be positive and unique.")
        return values


class UserAdminUpdate(BaseModel):
    role: ProgrammeRole | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_an_update(self) -> "UserAdminUpdate":
        if self.role is None and self.is_active is None:
            raise ValueError("Provide a role or active-status change.")
        return self


class UserAdminResponse(BaseModel):
    id: int
    name: str
    email: str
    role: ProgrammeRole
    is_active: bool

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    learner_count: int
    facilitator_names: list[str] = Field(default_factory=list)

class GroupAssignmentsResponse(BaseModel):
    group_id: int
    facilitator_ids: list[int]
    learner_ids: list[int]


class GroupStatusUpdate(BaseModel):
    is_active: bool


class SessionCreate(BaseModel):
    group_id: int = Field(gt=0)
    module_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    facilitator_plan: str = Field(default="", max_length=20_000)
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Session times must include a timezone.")
        return value


class SessionResponse(BaseModel):
    id: int
    group_id: int
    group_name: str
    module_id: int
    module_title: str
    title: str
    facilitator_plan: str
    starts_at: datetime
    ends_at: datetime
    status: Literal["scheduled", "completed", "cancelled"]


class AssignmentCreate(BaseModel):
    group_id: int = Field(gt=0)
    module_id: int = Field(gt=0)
    session_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1, max_length=20_000)
    due_at: datetime | None = None

    @field_validator("title", "instructions")
    @classmethod
    def trim_required_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("due_at")
    @classmethod
    def require_timezone_for_deadline(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Assignment deadlines must include a timezone.")
        return value


class AssignmentResponse(BaseModel):
    id: int
    group_id: int
    group_name: str
    module_id: int
    module_title: str
    session_id: int | None
    title: str
    instructions: str
    due_at: datetime | None
    status: Literal["open", "locked", "archived"]
    submission_id: int | None = None
    submission_status: Literal["draft", "submitted", "approved", "returned_for_improvement", "locked"] | None = None
    submission_content: str | None = None
    submitted_at: datetime | None = None
    feedback: str | None = None
    score: int | None = None


class SubmissionUpsert(BaseModel):
    content: str = Field(min_length=1, max_length=40_000)

    @field_validator("content")
    @classmethod
    def trim_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Submission content cannot be blank.")
        return value


class FeedbackUpsert(BaseModel):
    comments: str = Field(min_length=1, max_length=20_000)
    score: int | None = Field(default=None, ge=0, le=100)
    decision: Literal["approved", "returned_for_improvement"] = "approved"

    @field_validator("comments")
    @classmethod
    def trim_comments(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Feedback cannot be blank.")
        return value


class FacilitatorSubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    assignment_title: str
    group_id: int
    learner_id: int
    learner_name: str
    content: str
    status: Literal["draft", "submitted", "approved", "returned_for_improvement", "locked"]
    submitted_at: datetime | None
    feedback: str | None
    score: int | None


class AttendanceInput(BaseModel):
    learner_id: int = Field(gt=0)
    status: AttendanceStatus


class AttendanceBatchUpdate(BaseModel):
    records: list[AttendanceInput] = Field(min_length=1, max_length=500)

    @field_validator("records")
    @classmethod
    def unique_learners(cls, values: list[AttendanceInput]) -> list[AttendanceInput]:
        ids = [record.learner_id for record in values]
        if len(ids) != len(set(ids)):
            raise ValueError("Attendance may include each learner only once.")
        return values


class AttendanceResponse(BaseModel):
    learner_id: int
    learner_name: str
    status: AttendanceStatus | None
    updated_at: datetime | None


class LearnerAttendanceResponse(BaseModel):
    session_id: int
    session_title: str
    module_title: str
    starts_at: datetime
    status: AttendanceStatus | None


class SessionReportUpsert(BaseModel):
    content: str = Field(default="", max_length=20_000)
    follow_up_actions: str = Field(default="", max_length=10_000)

class SessionStatusUpdate(BaseModel):
    status: Literal["completed", "cancelled"]


class SessionReportResponse(BaseModel):
    id: int
    session_id: int
    group_id: int
    content: str
    follow_up_actions: str
    status: Literal["draft", "submitted"]
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


class FacilitatorSessionReport(BaseModel):
    id: int
    session_id: int
    group_id: int
    session_title: str
    group_name: str
    content: str
    follow_up_actions: str
    status: Literal["draft", "submitted"]
    submitted_at: datetime | None


class FacilitatorGroupSummary(BaseModel):
    id: int
    name: str
    learner_count: int
    upcoming_session_count: int
    pending_submission_count: int
    completed_module_records: int
    eligible_module_records: int
    attendance_records: int
    missing_attendance_records: int


class SupervisorProgrammeReport(BaseModel):
    active_learners: int
    active_facilitators: int
    active_groups: int
    published_modules: int
    completed_module_records: int
    attendance_records: int
    missing_attendance_records: int
    submitted_assignments: int
    awaiting_review: int
    overdue_session_reports: int
    groups: list[GroupResponse]
    completion_records: list[dict[str, object]]


class GroupScheduleResponse(BaseModel):
    groups: list[FacilitatorGroupSummary]
    sessions: list[SessionResponse]
    assignments: list[AssignmentResponse]
    submissions: list[FacilitatorSubmissionResponse]
    reports: list[FacilitatorSessionReport]

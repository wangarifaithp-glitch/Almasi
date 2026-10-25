from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ModuleQuestionResponse(BaseModel):
    id: int
    position: int
    kind: Literal["case_study", "assignment", "quiz"]
    prompt: str

    model_config = {"from_attributes": True}


class ModuleProgressResponse(BaseModel):
    id: int
    week_number: int
    title: str
    is_published: bool
    is_completed: bool
    submitted_at: datetime | None


class LearnerContentResponse(BaseModel):
    id: int
    week_number: int
    title: str
    content_markdown: str
    learning_objectives: list[str]
    reflection_prompts: list[str]
    questions: list[ModuleQuestionResponse]
    note: str
    note_updated_at: datetime | None
    reflection: str
    reflection_updated_at: datetime | None
    answers: dict[int, str]
    is_completed: bool
    submitted_at: datetime | None


class PrivateTextUpsert(BaseModel):
    content: str = Field(max_length=20_000)


class PrivateTextResponse(BaseModel):
    content: str
    updated_at: datetime


class LearnerAnswerInput(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(max_length=10_000)


class ModuleAnswerSaveRequest(BaseModel):
    answers: list[LearnerAnswerInput] = Field(min_length=1, max_length=100)

    @field_validator("answers")
    @classmethod
    def unique_question_ids(
        cls, values: list[LearnerAnswerInput]
    ) -> list[LearnerAnswerInput]:
        question_ids = [value.question_id for value in values]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each question can appear only once.")
        return values


class ModuleAnswerSaveResponse(BaseModel):
    module_id: int
    saved_answer_count: int
    is_completed: bool


class ModuleSubmissionRequest(BaseModel):
    answers: list[LearnerAnswerInput] = Field(min_length=1, max_length=100)

    @field_validator("answers")
    @classmethod
    def answers_must_not_be_blank(
        cls, values: list[LearnerAnswerInput]
    ) -> list[LearnerAnswerInput]:
        if any(not value.answer.strip() for value in values):
            raise ValueError("Answers cannot be blank.")
        question_ids = [value.question_id for value in values]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each question can appear only once.")
        return values


class ModuleSubmissionResponse(BaseModel):
    module_id: int
    is_completed: bool
    submitted_at: datetime
    confirmation: str


class DraftQuestionInput(BaseModel):
    position: int = Field(ge=1, le=100)
    kind: Literal["case_study", "assignment", "quiz"] = "case_study"
    prompt: str = Field(min_length=1, max_length=2000)

    @field_validator("prompt")
    @classmethod
    def trim_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question prompt cannot be blank.")
        return value


class DraftModuleCreate(BaseModel):
    week_number: int = Field(ge=1, le=12)
    title: str = Field(min_length=1, max_length=200)
    content_markdown: str = Field(default="", max_length=100_000)
    learning_objectives: list[str] = Field(default_factory=list, max_length=30)
    reflection_prompts: list[str] = Field(default_factory=list, max_length=20)
    questions: list[DraftQuestionInput] = Field(default_factory=list, max_length=100)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Module title cannot be blank.")
        return value

    @field_validator("learning_objectives")
    @classmethod
    def trim_objectives(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Learning objectives cannot be blank.")
        return cleaned

    @field_validator("reflection_prompts")
    @classmethod
    def trim_reflection_prompts(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Reflection prompts cannot be blank.")
        return cleaned

    @field_validator("questions")
    @classmethod
    def unique_question_positions(
        cls, values: list[DraftQuestionInput]
    ) -> list[DraftQuestionInput]:
        positions = [value.position for value in values]
        if len(positions) != len(set(positions)):
            raise ValueError("Question positions must be unique.")
        return values


class ModulePublicationResponse(BaseModel):
    id: int
    week_number: int
    title: str
    is_published: bool
    reviewed_at: datetime | None
    question_count: int


class SupervisorModuleResponse(BaseModel):
    id: int
    week_number: int
    title: str
    content_markdown: str
    learning_objectives: list[str]
    reflection_prompts: list[str]
    questions: list[ModuleQuestionResponse]
    is_published: bool
    reviewed_at: datetime | None
    reviewed_by_id: int | None


class ModuleReviewResponse(BaseModel):
    id: int
    is_reviewed: bool
    reviewed_at: datetime
    reviewed_by_id: int


class ModuleReviewRequest(BaseModel):
    confirm_review: bool

    @field_validator("confirm_review")
    @classmethod
    def require_explicit_review(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Confirm that you reviewed the learner-facing module.")
        return value

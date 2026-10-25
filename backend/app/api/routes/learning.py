from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.routes.auth import require_role
from app.core.security import utc_naive_now
from app.db.session import get_db
from app.models import (
    LearnerModuleNote,
    LearnerModuleReflection,
    LearnerModuleSubmission,
    LearnerProgress,
    LearnerQuestionAnswer,
    LearningModule,
    ModuleQuestion,
    User,
)
from app.schemas.learning import (
    DraftModuleCreate,
    ModuleAnswerSaveRequest,
    ModuleAnswerSaveResponse,
    LearnerContentResponse,
    ModuleProgressResponse,
    ModulePublicationResponse,
    ModuleReviewRequest,
    ModuleReviewResponse,
    ModuleSubmissionRequest,
    ModuleSubmissionResponse,
    PrivateTextResponse,
    PrivateTextUpsert,
    SupervisorModuleResponse,
)

learner_router = APIRouter(prefix="/learner/modules")
supervisor_router = APIRouter(prefix="/supervisor/modules")


@supervisor_router.get("", response_model=list[SupervisorModuleResponse])
def list_supervisor_modules(
    _: User = Depends(require_role(("supervisor", "administrator"))),
    db: Session = Depends(get_db),
) -> list[SupervisorModuleResponse]:
    modules = db.scalars(
        select(LearningModule)
        .options(selectinload(LearningModule.questions))
        .order_by(LearningModule.week_number)
    ).all()
    return [
        SupervisorModuleResponse(
            id=module.id,
            week_number=module.week_number,
            title=module.title,
            content_markdown=module.content_markdown,
            learning_objectives=module.learning_objectives,
            reflection_prompts=module.reflection_prompts,
            questions=module.questions,
            is_published=module.is_published,
            reviewed_at=module.reviewed_at,
            reviewed_by_id=module.reviewed_by_id,
        )
        for module in modules
    ]


def published_module(db: Session, module_id: int) -> LearningModule:
    module = db.scalar(
        select(LearningModule)
        .options(selectinload(LearningModule.questions))
        .where(
            LearningModule.id == module_id,
            LearningModule.is_published.is_(True),
        )
    )
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published module not found.",
        )
    return module


@learner_router.get("", response_model=list[ModuleProgressResponse])
def list_published_modules(
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> list[ModuleProgressResponse]:
    modules = db.scalars(
        select(LearningModule)
        .where(LearningModule.is_published.is_(True))
        .order_by(LearningModule.week_number)
    ).all()
    submissions = db.scalars(
        select(LearnerModuleSubmission).where(
            LearnerModuleSubmission.learner_id == user.id
        )
    ).all()
    submitted_by_module = {
        submission.module_id: submission
        for submission in submissions
        if submission.submitted_at is not None
    }
    return [
        ModuleProgressResponse(
            id=module.id,
            week_number=module.week_number,
            title=module.title,
            is_published=True,
            is_completed=module.id in submitted_by_module,
            submitted_at=(
                submitted_by_module[module.id].submitted_at
                if module.id in submitted_by_module
                else None
            ),
        )
        for module in modules
    ]


@learner_router.get("/{module_id}", response_model=LearnerContentResponse)
def get_module(
    module_id: int,
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> LearnerContentResponse:
    module = published_module(db, module_id)
    note = db.scalar(
        select(LearnerModuleNote).where(
            LearnerModuleNote.learner_id == user.id,
            LearnerModuleNote.module_id == module.id,
        )
    )
    reflection = db.scalar(
        select(LearnerModuleReflection).where(
            LearnerModuleReflection.learner_id == user.id,
            LearnerModuleReflection.module_id == module.id,
        )
    )
    submission = db.scalar(
        select(LearnerModuleSubmission)
        .options(selectinload(LearnerModuleSubmission.answers))
        .where(
            LearnerModuleSubmission.learner_id == user.id,
            LearnerModuleSubmission.module_id == module.id,
        )
    )
    return LearnerContentResponse(
        id=module.id,
        week_number=module.week_number,
        title=module.title,
        content_markdown=module.content_markdown,
        learning_objectives=module.learning_objectives,
        reflection_prompts=module.reflection_prompts,
        questions=module.questions,
        note=note.content if note else "",
        note_updated_at=note.updated_at if note else None,
        reflection=reflection.content if reflection else "",
        reflection_updated_at=reflection.updated_at if reflection else None,
        answers=(
            {answer.question_id: answer.answer for answer in submission.answers}
            if submission
            else {}
        ),
        is_completed=submission is not None and submission.submitted_at is not None,
        submitted_at=(
            submission.submitted_at
            if submission and submission.submitted_at is not None
            else None
        ),
    )


def save_private_text(
    *,
    content: str,
    module_id: int,
    learner_id: int,
    model: type[LearnerModuleNote] | type[LearnerModuleReflection],
    db: Session,
) -> PrivateTextResponse:
    published_module(db, module_id)
    record = db.scalar(
        select(model).where(
            model.learner_id == learner_id,
            model.module_id == module_id,
        )
    )
    now = utc_naive_now()
    if record is None:
        record = model(learner_id=learner_id, module_id=module_id, content=content, updated_at=now)
        db.add(record)
    else:
        record.content = content
        record.updated_at = now
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This record changed at the same time. Please reload and retry.",
        ) from exc
    return PrivateTextResponse(content=record.content, updated_at=record.updated_at)


@learner_router.put("/{module_id}/notes", response_model=PrivateTextResponse)
def save_note(
    module_id: int,
    data: PrivateTextUpsert,
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> PrivateTextResponse:
    return save_private_text(
        content=data.content,
        module_id=module_id,
        learner_id=user.id,
        model=LearnerModuleNote,
        db=db,
    )


@learner_router.put("/{module_id}/reflections", response_model=PrivateTextResponse)
def save_reflection(
    module_id: int,
    data: PrivateTextUpsert,
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> PrivateTextResponse:
    return save_private_text(
        content=data.content,
        module_id=module_id,
        learner_id=user.id,
        model=LearnerModuleReflection,
        db=db,
    )


@learner_router.put("/{module_id}/answers", response_model=ModuleAnswerSaveResponse)
def save_answer_draft(
    module_id: int,
    data: ModuleAnswerSaveRequest,
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> ModuleAnswerSaveResponse:
    module = published_module(db, module_id)
    question_ids = {question.id for question in module.questions}
    submitted_ids = {item.question_id for item in data.answers}
    if not submitted_ids.issubset(question_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Answers must belong to questions in this module.",
        )

    submission = db.scalar(
        select(LearnerModuleSubmission)
        .options(selectinload(LearnerModuleSubmission.answers))
        .where(
            LearnerModuleSubmission.learner_id == user.id,
            LearnerModuleSubmission.module_id == module.id,
        )
    )
    if submission is not None and submission.submitted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This module has already been submitted.",
        )
    if submission is None:
        submission = LearnerModuleSubmission(
            learner_id=user.id,
            module_id=module.id,
            submitted_at=None,
            answers=[],
        )
        db.add(submission)
        db.flush()

    answers_by_question = {answer.question_id: answer for answer in submission.answers}
    for item in data.answers:
        answer = answers_by_question.get(item.question_id)
        if not item.answer.strip():
            if answer is not None:
                submission.answers.remove(answer)
        elif answer is None:
            submission.answers.append(
                LearnerQuestionAnswer(
                    question_id=item.question_id,
                    answer=item.answer,
                )
            )
        else:
            answer.answer = item.answer
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your answers changed at the same time. Please reload and retry.",
        ) from exc
    return ModuleAnswerSaveResponse(
        module_id=module.id,
        saved_answer_count=len(submission.answers),
        is_completed=False,
    )


@learner_router.post(
    "/{module_id}/submit",
    response_model=ModuleSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_module(
    module_id: int,
    data: ModuleSubmissionRequest,
    user: User = Depends(require_role("learner")),
    db: Session = Depends(get_db),
) -> ModuleSubmissionResponse:
    module = published_module(db, module_id)
    if not module.questions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This module is not ready for submission.",
        )
    question_ids = {question.id for question in module.questions}
    answer_ids = [answer.question_id for answer in data.answers]
    if len(answer_ids) != len(set(answer_ids)) or set(answer_ids) != question_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide one answer for every question in this module.",
        )
    submission = db.scalar(
        select(LearnerModuleSubmission)
        .options(selectinload(LearnerModuleSubmission.answers))
        .where(
            LearnerModuleSubmission.learner_id == user.id,
            LearnerModuleSubmission.module_id == module.id,
        )
    )
    if submission is not None and submission.submitted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This module has already been submitted.",
        )
    now = utc_naive_now()
    if submission is None:
        submission = LearnerModuleSubmission(
            learner_id=user.id,
            module_id=module.id,
            submitted_at=now,
            answers=[
                LearnerQuestionAnswer(
                    question_id=item.question_id,
                    answer=item.answer,
                )
                for item in data.answers
            ],
        )
        db.add(submission)
    else:
        submission.submitted_at = now
        answer_map = {answer.question_id: answer for answer in submission.answers}
        for item in data.answers:
            answer = answer_map.get(item.question_id)
            if answer is None:
                submission.answers.append(
                    LearnerQuestionAnswer(
                        question_id=item.question_id,
                        answer=item.answer,
                    )
                )
            else:
                answer.answer = item.answer
    progress = db.scalar(
        select(LearnerProgress).where(
            LearnerProgress.learner_id == user.id,
            LearnerProgress.module_id == module.id,
        )
    )
    if progress is None:
        db.add(
            LearnerProgress(
                learner_id=user.id,
                module_id=module.id,
                is_completed=True,
                completed_at=now,
                updated_at=now,
            )
        )
    else:
        progress.is_completed = True
        progress.completed_at = now
        progress.updated_at = now
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This module has already been submitted.",
        ) from exc
    return ModuleSubmissionResponse(
        module_id=module.id,
        is_completed=True,
        submitted_at=submission.submitted_at,
        confirmation="Your answers have been submitted and this module is complete.",
    )


def replace_draft_questions(
    module: LearningModule, data: DraftModuleCreate, db: Session
) -> None:
    module.week_number = data.week_number
    module.title = data.title
    module.content_markdown = data.content_markdown
    module.learning_objectives = data.learning_objectives
    module.reflection_prompts = data.reflection_prompts
    module.reviewed_at = None
    module.reviewed_by_id = None
    module.updated_at = utc_naive_now()
    db.execute(delete(ModuleQuestion).where(ModuleQuestion.module_id == module.id))
    db.flush()
    module.questions = [
        ModuleQuestion(
            position=question.position,
            kind=question.kind,
            prompt=question.prompt,
        )
        for question in data.questions
    ]


@supervisor_router.post(
    "",
    response_model=ModulePublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_module_draft(
    data: DraftModuleCreate,
    _: User = Depends(require_role(("supervisor", "administrator"))),
    db: Session = Depends(get_db),
) -> ModulePublicationResponse:
    module = LearningModule(
        week_number=data.week_number,
        title=data.title,
        content_markdown=data.content_markdown,
        learning_objectives=data.learning_objectives,
        is_published=False,
        reflection_prompts=data.reflection_prompts,
        reviewed_at=None,
        reviewed_by_id=None,
        created_at=utc_naive_now(),
        updated_at=utc_naive_now(),
        questions=[
            ModuleQuestion(
                position=question.position,
                kind=question.kind,
                prompt=question.prompt,
            )
            for question in data.questions
        ],
    )
    db.add(module)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A module already exists for that week.",
        ) from exc
    db.refresh(module)
    return ModulePublicationResponse(
        id=module.id,
        week_number=module.week_number,
        title=module.title,
        is_published=module.is_published,
        reviewed_at=module.reviewed_at,
        question_count=len(module.questions),
    )


@supervisor_router.put("/{module_id}", response_model=ModulePublicationResponse)
def update_module_draft(
    module_id: int,
    data: DraftModuleCreate,
    _: User = Depends(require_role(("supervisor", "administrator"))),
    db: Session = Depends(get_db),
) -> ModulePublicationResponse:
    module = db.get(LearningModule, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found.")
    if module.is_published:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Published modules cannot be edited through the draft endpoint.",
        )
    replace_draft_questions(module, data, db)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A module already exists for that week.",
        ) from exc
    return ModulePublicationResponse(
        id=module.id,
        week_number=module.week_number,
        title=module.title,
        is_published=False,
        reviewed_at=None,
        question_count=len(module.questions),
    )


@supervisor_router.post("/{module_id}/review", response_model=ModuleReviewResponse)
def review_module(
    module_id: int,
    data: ModuleReviewRequest,
    user: User = Depends(require_role(("supervisor", "administrator"))),
    db: Session = Depends(get_db),
) -> ModuleReviewResponse:
    if not data.confirm_review:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Confirm that you reviewed the learner-facing module.",
        )
    module = db.scalar(
        select(LearningModule)
        .options(selectinload(LearningModule.questions))
        .where(LearningModule.id == module_id)
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found.")
    if module.is_published:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Published modules cannot be reviewed through the draft endpoint.",
        )
    if (
        not module.content_markdown.strip()
        or not module.learning_objectives
        or not module.reflection_prompts
        or not module.questions
        or not any(question.kind == "case_study" for question in module.questions)
        or not any(question.kind == "assignment" for question in module.questions)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lesson content, objectives, reflection prompts, case studies, and assignments are required for review.",
        )
    if any(
        not value.strip()
        for value in module.learning_objectives + module.reflection_prompts
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Objectives and reflection prompts cannot be blank.",
        )
    module.reviewed_at = utc_naive_now()
    module.reviewed_by_id = user.id
    module.updated_at = module.reviewed_at
    db.commit()
    return ModuleReviewResponse(
        id=module.id,
        is_reviewed=True,
        reviewed_at=module.reviewed_at,
        reviewed_by_id=user.id,
    )


@supervisor_router.post(
    "/{module_id}/publish", response_model=ModulePublicationResponse
)
def publish_module(
    module_id: int,
    _: User = Depends(require_role(("supervisor", "administrator"))),
    db: Session = Depends(get_db),
) -> ModulePublicationResponse:
    module = db.scalar(
        select(LearningModule)
        .options(selectinload(LearningModule.questions))
        .where(LearningModule.id == module_id)
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found.")
    if module.reviewed_at is None or module.reviewed_by_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A supervisor must review this module before it can be published.",
        )
    if not module.content_markdown.strip() or not module.learning_objectives:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A module needs approved content and learning objectives before publishing.",
        )
    if any(not objective.strip() for objective in module.learning_objectives):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Learning objectives cannot be blank.",
        )
    if not module.questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A module needs at least one question before publishing.",
        )
    module.is_published = True
    module.updated_at = utc_naive_now()
    db.commit()
    return ModulePublicationResponse(
        id=module.id,
        week_number=module.week_number,
        title=module.title,
        is_published=True,
        reviewed_at=module.reviewed_at,
        question_count=len(module.questions),
    )

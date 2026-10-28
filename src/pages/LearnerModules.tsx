import { useEffect, useState, type CSSProperties } from "react";
import { ApiError, apiFetch } from "../lib/api";

type ModuleProgress = {
  id: number;
  week_number: number;
  title: string;
  is_published: boolean;
  is_completed: boolean;
  submitted_at: string | null;
};

type ModuleQuestion = {
  id: number;
  position: number;
  kind: "case_study" | "assignment" | "quiz";
  prompt: string;
};

type ModuleQuizQuestion = {
  id: number;
  position: number;
  prompt: string;
  options: string[];
};

type QuizAttempt = {
  id: number;
  answers: Record<number, number>;
  score: number;
  total_questions: number;
  feedback: string;
  submitted_at: string;
};

type LearnerModule = {
  id: number;
  week_number: number;
  title: string;
  image_url: string;
  image_alt: string;
  content_markdown: string;
  learning_objectives: string[];
  reflection_prompts: string[];
  questions: ModuleQuestion[];
  quiz_questions: ModuleQuizQuestion[];
  quiz_attempts: QuizAttempt[];
  note: string;
  note_updated_at: string | null;
  reflection: string;
  reflection_updated_at: string | null;
  answers: Record<number, string>;
  is_completed: boolean;
  submitted_at: string | null;
};

type SaveState = "idle" | "saving" | "saved" | "error";

function requestErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) {
    return "This module is no longer available.";
  }
  if (error instanceof ApiError && error.status === 401) {
    return "Your sign-in has expired. Please sign in again.";
  }
  return "We couldn’t connect to the learning service. Please try again.";
}

export default function LearnerModules() {
  const [modules, setModules] = useState<ModuleProgress[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [module, setModule] = useState<LearnerModule | null>(null);
  const [listState, setListState] = useState<"loading" | "ready" | "error">("loading");
  const [detailState, setDetailState] = useState<"loading" | "ready" | "error">("loading");
  const [listRetry, setListRetry] = useState(0);
  const [detailRetry, setDetailRetry] = useState(0);
  const [note, setNote] = useState("");
  const [reflection, setReflection] = useState("");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({});
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizError, setQuizError] = useState("");
  const [noteState, setNoteState] = useState<SaveState>("idle");
  const [reflectionState, setReflectionState] = useState<SaveState>("idle");
  const [answerState, setAnswerState] = useState<SaveState>("idle");
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "error" | "done">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [learnerName, setLearnerName] = useState("Learner");

  const completedModules = modules.filter((item) => item.is_completed).length;
  const progressPercent = modules.length
    ? Math.round((completedModules / modules.length) * 100)
    : 0;
  const quizAttempts = modules.reduce(
    (total, item) => total + (item.id === module?.id ? module.quiz_attempts.length : 0),
    0,
  );

  useEffect(() => {
    let active = true;
    apiFetch("auth/me")
      .then((response) => response.json() as Promise<{ name?: string }>)
      .then((user) => {
        if (active && user.name?.trim()) setLearnerName(user.name.trim());
      })
      .catch(() => {
        // ProtectedRoute has already verified the session; the dashboard remains usable if this display-only request fails.
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setListState("loading");
    apiFetch("learner/modules")
      .then((response) => response.json() as Promise<ModuleProgress[]>)
      .then((data) => {
        if (!active) return;
        setModules(data);
        setListState("ready");
        setSelectedId((current) =>
          current !== null && data.some((item) => item.id === current)
            ? current
            : data[0]?.id ?? null,
        );
      })
      .catch((error: unknown) => {
        if (!active) return;
        setErrorMessage(requestErrorMessage(error));
        setListState("error");
      });
    return () => {
      active = false;
    };
  }, [listRetry]);

  useEffect(() => {
    if (selectedId === null) {
      setModule(null);
      return;
    }
    let active = true;
    setDetailState("loading");
    setSubmitState("idle");
    apiFetch(`learner/modules/${selectedId}`)
      .then((response) => response.json() as Promise<LearnerModule>)
      .then((data) => {
        if (!active) return;
        setModule(data);
        setNote(data.note);
        setReflection(data.reflection);
        setAnswers(data.answers);
        setQuizAnswers(data.quiz_attempts[0]?.answers ?? {});
        setQuizError("");
        setNoteState(data.note_updated_at ? "saved" : "idle");
        setReflectionState(data.reflection_updated_at ? "saved" : "idle");
        setAnswerState(Object.keys(data.answers).length > 0 ? "saved" : "idle");
        setDetailState("ready");
      })
      .catch((error: unknown) => {
        if (!active) return;
        setErrorMessage(requestErrorMessage(error));
        setDetailState("error");
      });
    return () => {
      active = false;
    };
  }, [selectedId, detailRetry]);

  async function savePrivateText(
    kind: "notes" | "reflections",
    content: string,
    setState: (state: SaveState) => void,
  ) {
    if (selectedId === null) return;
    setState("saving");
    setErrorMessage("");
    try {
      await apiFetch(`learner/modules/${selectedId}/${kind}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      setState("saved");
    } catch (error) {
      setErrorMessage(requestErrorMessage(error));
      setState("error");
    }
  }

  async function submitAnswers() {
    if (!module) return;
    setSubmitState("submitting");
    setErrorMessage("");
    try {
      await apiFetch(`learner/modules/${module.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answers: module.questions.map((question) => ({
            question_id: question.id,
            answer: answers[question.id] ?? "",
          })),
        }),
      });
      setSubmitState("done");
      setAnswerState("saved");
      setModule({ ...module, is_completed: true });
      setModules((current) =>
        current.map((item) =>
          item.id === module.id ? { ...item, is_completed: true } : item,
        ),
      );
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError && error.status === 409
          ? "This module has already been submitted or is not ready for submission."
          : requestErrorMessage(error),
      );
      setSubmitState("error");
    }
  }

  async function saveAnswers() {
    if (!module) return;
    setAnswerState("saving");
    setErrorMessage("");
    try {
      await apiFetch(`learner/modules/${module.id}/answers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answers: module.questions.map((question) => ({
            question_id: question.id,
            answer: answers[question.id] ?? "",
          })),
        }),
      });
      setAnswerState("saved");
    } catch (error) {
      setErrorMessage(requestErrorMessage(error));
      setAnswerState("error");
    }
  }

  async function submitQuiz() {
    if (!module) return;
    setQuizSubmitting(true);
    setQuizError("");
    try {
      const response = await apiFetch(`learner/modules/${module.id}/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answers: module.quiz_questions.map((question) => ({
            question_id: question.id,
            selected_option: quizAnswers[question.id],
          })),
        }),
      });
      const attempt = (await response.json()) as QuizAttempt;
      setModule((current) =>
        current
          ? {
              ...current,
              quiz_attempts: [
                attempt,
                ...current.quiz_attempts.filter((item) => item.id !== attempt.id),
              ],
            }
          : current,
      );
    } catch (requestError) {
      setQuizError(
        requestError instanceof ApiError && requestError.status === 422
          ? "Please select one answer for every quiz question."
          : requestErrorMessage(requestError),
      );
    } finally {
      setQuizSubmitting(false);
    }
  }

  return (
    <>
      <section className="workspace-intro">
        <span className="eyebrow">Your ALMASI journey</span>
        <h2>Welcome back, {learnerName}.</h2>
        <p>
          Continue your approved lessons, keep your reflections private, and
          complete each activity at your own pace.
        </p>
      </section>

      <section className="dashboard-hero dashboard-hero--learner">
        <div>
          <span className="dashboard-hero__eyebrow">LEARNER DASHBOARD</span>
          <h3>{modules.find((item) => !item.is_completed)?.title ?? "Your learning journey is complete."}</h3>
          <p>
            {modules.find((item) => !item.is_completed)
              ? "Pick up where you left off. Your lessons, reflections, and quiz results are saved to your private learning record."
              : "You have completed every published module. Take a moment to celebrate your progress."}
          </p>
          {modules.length > 0 && (
            <button
              className="button button--primary dashboard-hero__action"
              onClick={() => {
                const nextModule = modules.find((item) => !item.is_completed) ?? modules[0];
                setSelectedId(nextModule.id);
                window.setTimeout(() => {
                  document.getElementById("module-workspace")?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }, 0);
              }}
              type="button"
            >
              {completedModules ? "Continue learning" : "Start learning"}
              <span aria-hidden="true">→</span>
            </button>
          )}
        </div>
        <div className="dashboard-progress" aria-label={`${progressPercent}% module progress`}>
          <div
            className="dashboard-progress__ring"
            style={{ "--progress": `${progressPercent * 3.6}deg` } as CSSProperties}
          >
            <strong>{progressPercent}%</strong>
            <span>progress</span>
          </div>
        </div>
      </section>

      <section className="dashboard-stat-grid" aria-label="Learning summary">
        <article className="dashboard-stat">
          <span>Modules completed</span>
          <strong>{completedModules}<small>/{modules.length || 12}</small></strong>
          <p>Keep moving through your learning path.</p>
        </article>
        <article className="dashboard-stat">
          <span>Modules remaining</span>
          <strong>{Math.max((modules.length || 12) - completedModules, 0)}</strong>
          <p>Published lessons ready when you are.</p>
        </article>
        <article className="dashboard-stat">
          <span>Selected module attempts</span>
          <strong>{quizAttempts}</strong>
          <p>Your saved scores and feedback.</p>
        </article>
        <article className="dashboard-stat dashboard-stat--accent">
          <span>Next step</span>
          <strong>{modules.find((item) => !item.is_completed)?.title ?? "Celebrate"}</strong>
          <p>{modules.find((item) => !item.is_completed) ? "Continue your learning journey." : "You have completed every published module."}</p>
        </article>
      </section>

      {errorMessage && <p className="workspace-alert" role="alert">{errorMessage}</p>}

      {listState === "loading" ? (
        <p className="workspace-message" role="status">Loading your published modules…</p>
      ) : listState === "error" ? (
        <section className="workspace-message" role="alert">
          <h1>We couldn’t load your modules.</h1>
          <p>{errorMessage}</p>
          <button
            className="button button--primary"
            onClick={() => setListRetry((attempt) => attempt + 1)}
            type="button"
          >
            Try again
          </button>
        </section>
      ) : modules.length === 0 ? (
        <section className="workspace-message">
          <h1>No modules have been published yet.</h1>
          <p>
            The learner lessons are awaiting supervisor review. Your notes and
            reflections will be available when modules are approved and published.
          </p>
        </section>
      ) : (
        <>
          <section className="workspace-card">
            <div className="workspace-card__heading">
              <div>
                <span className="workspace-kicker">LEARNING PATH</span>
                <h3>Published modules</h3>
              </div>
              <span className="workspace-count">
                {modules.filter((item) => item.is_completed).length} of {modules.length} complete
              </span>
            </div>
            <div className="workspace-modules">
              {modules.map((item) => (
                <button
                  aria-current={selectedId === item.id ? "true" : undefined}
                  className={`workspace-module workspace-module--button${selectedId === item.id ? " workspace-module--selected" : ""}`}
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  type="button"
                >
                  <span className="workspace-module__number">
                    {String(item.week_number).padStart(2, "0")}
                  </span>
                  <span className="workspace-module__copy">
                    <strong>{item.title}</strong>
                    <span>Week {item.week_number}</span>
                  </span>
                  <span className="workspace-module__status">
                    {item.is_completed ? "Complete" : "Not started"}
                  </span>
                </button>
              ))}
            </div>
          </section>

          {selectedId !== null && detailState === "loading" && (
            <p className="workspace-message" role="status">Loading module…</p>
          )}
          {selectedId !== null && detailState === "error" && (
            <section className="workspace-message" role="alert">
              <h1>We couldn’t load this module.</h1>
              <p>{errorMessage}</p>
              <button
                className="button button--primary"
                onClick={() => setDetailRetry((attempt) => attempt + 1)}
                type="button"
              >
                Try again
              </button>
            </section>
          )}
          {module && detailState === "ready" && (
            <article className="workspace-card learner-module-content" id="module-workspace">
              <span className="workspace-kicker">WEEK {module.week_number}</span>
              <h3>{module.title}</h3>
              <div className="learner-module-image">
                <img
                  src={module.image_url}
                  alt={module.image_alt}
                  loading="lazy"
                  onError={(event) => {
                    event.currentTarget.hidden = true;
                    event.currentTarget.parentElement?.classList.add(
                      "learner-module-image--fallback",
                    );
                  }}
                />
                <span aria-hidden="true">ALMASI learning illustration</span>
              </div>

              <nav className="learner-module-nav" aria-label="Module sections">
                <a href="#module-objectives">Objectives</a>
                <a href="#module-content">Lesson</a>
                <a href="#module-quiz-title">Quiz</a>
                <a href="#module-activities">Activities</a>
                <a href="#module-reflection">Reflection</a>
                <a href="#module-submit">Submit</a>
              </nav>

              <section className="learner-module-section" id="module-objectives">
                <h4>Learning objectives</h4>
                <ul>
                  {module.learning_objectives.map((objective) => (
                    <li key={objective}>{objective}</li>
                  ))}
                </ul>
              </section>

              <section className="learner-module-section" id="module-content">
                <h4>Module content</h4>
                <div className="learner-module-prose">{module.content_markdown}</div>
              </section>

              <section className="learner-module-section" aria-labelledby="module-quiz-title">
                <h4 id="module-quiz-title">Module quiz</h4>
                <p>
                  Choose one answer for each question. Your score and feedback are
                  saved to your learning record. You can try the quiz again.
                </p>
                {module.quiz_questions.map((question) => (
                  <fieldset className="learner-question" key={question.id}>
                    <legend>
                      <span className="learner-question__kind">Question {question.position}</span>
                      {question.prompt}
                    </legend>
                    {question.options.map((option, optionIndex) => (
                      <label className="learner-quiz-option" key={option}>
                        <input
                          checked={quizAnswers[question.id] === optionIndex}
                          name={`quiz-question-${question.id}`}
                          onChange={() => {
                            setQuizAnswers((current) => ({
                              ...current,
                              [question.id]: optionIndex,
                            }));
                            setQuizError("");
                          }}
                          type="radio"
                          value={optionIndex}
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </fieldset>
                ))}
                {quizError && <p className="workspace-alert" role="alert">{quizError}</p>}
                <button
                  className="button button--primary"
                  disabled={
                    quizSubmitting ||
                    module.quiz_questions.length < 5 ||
                    module.quiz_questions.some(
                      (question) => quizAnswers[question.id] === undefined,
                    )
                  }
                  onClick={() => void submitQuiz()}
                  type="button"
                >
                  {quizSubmitting ? "Submitting quiz…" : "Submit quiz"}
                </button>
                {module.quiz_attempts.map((attempt, index) => (
                  <article className="learner-completion" key={attempt.id}>
                    <strong>
                      {index === 0 ? "Latest result: " : "Previous attempt: "}
                      {attempt.score} / {attempt.total_questions}
                    </strong>
                    <p>{new Date(attempt.submitted_at).toLocaleString()}</p>
                    <ul>
                      {attempt.feedback.split("\n").map((line) => (
                        <li key={line}>{line}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </section>

              <section className="learner-module-section" id="module-activities">
                <h4>Case studies and assignments</h4>
                <p>
                  These are fictional situations. Answer about the examples, not
                  personal experiences. Do not enter names, contact details, or
                  private safety-plan information. Your answers are private to you.
                </p>
                {module.questions.map((question) => (
                  <label className="learner-question" htmlFor={`question-${question.id}`} key={question.id}>
                    <span className="learner-question__kind">
                      {question.kind === "case_study"
                        ? "Case study"
                        : question.kind === "assignment"
                          ? "Assignment"
                          : "Quiz"}
                    </span>
                    <span>{question.prompt}</span>
                    <textarea
                      disabled={module.is_completed}
                      id={`question-${question.id}`}
                      maxLength={10_000}
                      onChange={(event) => {
                        setAnswers((current) => ({
                          ...current,
                          [question.id]: event.target.value,
                        }));
                        setAnswerState("idle");
                      }}
                      rows={3}
                      value={answers[question.id] ?? ""}
                    />
                  </label>
                ))}
                {!module.is_completed && (
                  <>
                    <button
                      className="button button--primary"
                      disabled={answerState === "saving"}
                      onClick={() => void saveAnswers()}
                      type="button"
                    >
                      {answerState === "saving" ? "Saving answers…" : "Save answers"}
                    </button>
                    {answerState === "saved" && (
                      <span className="learner-save-status" role="status">
                        Answers saved. You can return and continue later.
                      </span>
                    )}
                    {answerState === "error" && (
                      <span className="learner-save-status" role="alert">
                        Answers were not saved. Please retry.
                      </span>
                    )}
                  </>
                )}
              </section>

              <section className="learner-module-section">
                <label htmlFor="learner-module-note">Personal notes</label>
                <p>Only you can access your notes.</p>
                <textarea
                  id="learner-module-note"
                  maxLength={20_000}
                  onChange={(event) => {
                    setNote(event.target.value);
                    setNoteState("idle");
                  }}
                  rows={5}
                  value={note}
                />
                <button
                  className="button button--primary"
                  disabled={noteState === "saving"}
                  onClick={() => void savePrivateText("notes", note, setNoteState)}
                  type="button"
                >
                  {noteState === "saving" ? "Saving…" : "Save notes"}
                </button>
                {noteState === "saved" && <span className="learner-save-status" role="status">Notes saved.</span>}
                {noteState === "error" && <span className="learner-save-status" role="alert">Notes were not saved. Please retry.</span>}
              </section>

              <section className="learner-module-section" id="module-reflection">
                <label htmlFor="learner-module-reflection">Private reflection</label>
                <ul className="learner-reflection-prompts">
                  {module.reflection_prompts.map((prompt) => (
                    <li key={prompt}>{prompt}</li>
                  ))}
                </ul>
                <p>Reflections are private and are not available to facilitators or supervisors.</p>
                <textarea
                  id="learner-module-reflection"
                  maxLength={20_000}
                  onChange={(event) => {
                    setReflection(event.target.value);
                    setReflectionState("idle");
                  }}
                  rows={5}
                  value={reflection}
                />
                <button
                  className="button button--primary"
                  disabled={reflectionState === "saving"}
                  onClick={() => void savePrivateText("reflections", reflection, setReflectionState)}
                  type="button"
                >
                  {reflectionState === "saving" ? "Saving…" : "Save reflection"}
                </button>
                {reflectionState === "saved" && <span className="learner-save-status" role="status">Reflection saved privately.</span>}
                {reflectionState === "error" && <span className="learner-save-status" role="alert">Reflection was not saved. Please retry.</span>}
              </section>

              <section className="learner-module-section" id="module-submit">
                <h4>Submit your completed module</h4>
                <p>Save an answer for every case study and assignment before submitting.</p>
                {module.is_completed ? (
                  <p className="learner-completion" role="status">
                    Your answers have been submitted. This module is complete.
                  </p>
                ) : (
                  <button
                    className="button button--primary"
                    disabled={
                      submitState === "submitting" ||
                      answerState !== "saved" ||
                      module.questions.some((question) => !(answers[question.id] ?? "").trim())
                    }
                    onClick={() => void submitAnswers()}
                    type="button"
                  >
                    {submitState === "submitting" ? "Submitting…" : "Submit answers"}
                  </button>
                )}
                {submitState === "done" && (
                  <p className="learner-completion" role="status">
                    Submission confirmed. Your module is complete.
                  </p>
                )}
              </section>
            </article>
          )}
        </>
      )}
    </>
  );
}

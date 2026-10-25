import { useEffect, useState } from "react";
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

type LearnerModule = {
  id: number;
  week_number: number;
  title: string;
  content_markdown: string;
  learning_objectives: string[];
  reflection_prompts: string[];
  questions: ModuleQuestion[];
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
  const [noteState, setNoteState] = useState<SaveState>("idle");
  const [reflectionState, setReflectionState] = useState<SaveState>("idle");
  const [answerState, setAnswerState] = useState<SaveState>("idle");
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "error" | "done">("idle");
  const [errorMessage, setErrorMessage] = useState("");

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

  return (
    <>
      <section className="workspace-intro">
        <span className="eyebrow">Your ALMASI journey</span>
        <h2>Your learning space</h2>
        <p>
          Work through approved modules, keep your notes and reflections private,
          and submit your answers when you are ready.
        </p>
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
            <article className="workspace-card learner-module-content">
              <span className="workspace-kicker">WEEK {module.week_number}</span>
              <h3>{module.title}</h3>

              <section className="learner-module-section">
                <h4>Learning objectives</h4>
                <ul>
                  {module.learning_objectives.map((objective) => (
                    <li key={objective}>{objective}</li>
                  ))}
                </ul>
              </section>

              <section className="learner-module-section">
                <h4>Module content</h4>
                <div className="learner-module-prose">{module.content_markdown}</div>
              </section>

              <section className="learner-module-section">
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

              <section className="learner-module-section">
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

              <section className="learner-module-section">
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

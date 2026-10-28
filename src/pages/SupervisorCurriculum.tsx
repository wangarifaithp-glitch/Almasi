import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type ModuleQuestion = {
  id: number;
  position: number;
  kind: "case_study" | "assignment" | "quiz";
  prompt: string;
};

type QuizQuestion = {
  id: number;
  position: number;
  prompt: string;
  options: string[];
  correct_option: number;
  explanation: string;
};

type SessionSegment = {
  minutes: number;
  segment: string;
  facilitator_notes: string;
};

type FacilitatorGuide = {
  review_status: string;
  session_length_minutes: number;
  facilitator_objective: string;
  preparation: string[];
  teaching_notes: string[];
  discussion_questions: string[];
  practical_activities: string[];
  session_structure: SessionSegment[];
  safeguarding: string[];
};

type SupervisorModule = {
  id: number;
  week_number: number;
  title: string;
  image_url: string;
  image_alt: string;
  content_markdown: string;
  learning_objectives: string[];
  reflection_prompts: string[];
  questions: ModuleQuestion[];
  quiz_questions: QuizQuestion[];
  facilitator_guide: FacilitatorGuide;
  is_published: boolean;
  reviewed_at: string | null;
  reviewed_by_id: number | null;
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Your sign-in has expired. Please sign in again.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "A supervisor or administrator account is required to review curriculum.";
  }
  return "We couldn’t connect to the curriculum service. Please try again.";
}

export default function SupervisorCurriculum() {
  const [modules, setModules] = useState<SupervisorModule[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [retry, setRetry] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [reviewConfirmed, setReviewConfirmed] = useState<Record<number, boolean>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    setStatus("loading");
    apiFetch("supervisor/modules")
      .then((response) => response.json() as Promise<SupervisorModule[]>)
      .then((data) => {
        if (!active) return;
        setModules(data);
        setStatus("ready");
      })
      .catch((requestError: unknown) => {
        if (!active) return;
        setError(errorMessage(requestError));
        setStatus("error");
      });
    return () => {
      active = false;
    };
  }, [retry]);

  async function reviewOrPublish(module: SupervisorModule) {
    const action = module.reviewed_at ? "publish" : "review";
    setBusyId(module.id);
    setError("");
    setNotice("");
    try {
      await apiFetch(`supervisor/modules/${module.id}/${action}`, {
        method: "POST",
        ...(action === "review"
          ? {
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ confirm_review: true }),
            }
          : {}),
      });
      setNotice(
        action === "review"
          ? `${module.title} has been reviewed. It can now be published if approved.`
          : `${module.title} is now published to learners.`,
      );
      setRetry((attempt) => attempt + 1);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="workspace-card supervisor-curriculum">
      <div className="workspace-card__heading">
        <div>
          <span className="workspace-kicker">CURRICULUM REVIEW</span>
          <h3>12-week learner modules</h3>
        </div>
        <span className="workspace-count">
          {modules.filter((module) => module.is_published).length} published
        </span>
      </div>
      <div className="supervisor-curriculum__content">
        {error && <p className="workspace-alert" role="alert">{error}</p>}
        {notice && <p className="learner-completion" role="status">{notice}</p>}
        {status === "loading" ? (
          <p className="workspace-message" role="status">Loading curriculum drafts…</p>
        ) : status === "error" ? (
          <button
            className="button button--primary"
            onClick={() => setRetry((attempt) => attempt + 1)}
            type="button"
          >
            Try again
          </button>
        ) : modules.length === 0 ? (
          <p className="workspace-message">No curriculum drafts are available.</p>
        ) : (
          modules.map((module) => (
            <article className="supervisor-curriculum__module" key={module.id}>
              <div className="supervisor-curriculum__module-heading">
                <div>
                  <span className="workspace-kicker">
                    WEEK {String(module.week_number).padStart(2, "0")}
                  </span>
                  <h4>{module.title}</h4>
                </div>
                <span className="workspace-module__status">
                  {module.is_published
                    ? "Published"
                    : module.reviewed_at
                      ? "Reviewed"
                      : "Awaiting review"}
                </span>
              </div>
              <details>
                <summary>Review learner lesson, quiz, answer key and facilitator guide</summary>
                <div className="supervisor-curriculum__lesson">
                  <h5>Learner lesson</h5>
                  <div className="learner-module-prose">{module.content_markdown}</div>
                  <h5>Learning objectives</h5>
                  <ul>
                    {module.learning_objectives.map((objective) => (
                      <li key={objective}>{objective}</li>
                    ))}
                  </ul>
                  <h5>Private reflection prompts</h5>
                  <ul>
                    {module.reflection_prompts.map((prompt) => (
                      <li key={prompt}>{prompt}</li>
                    ))}
                  </ul>
                  <h5>Case studies and assignments</h5>
                  <ol>
                    {module.questions.map((question) => (
                      <li key={question.id}>
                        <strong>
                          {question.kind === "case_study" ? "Case study" : "Assignment"}:
                        </strong>{" "}
                        {question.prompt}
                      </li>
                    ))}
                  </ol>
                  <h5>Separate learner quiz and answer key</h5>
                  <ol>
                    {module.quiz_questions.map((question) => (
                      <li key={question.id}>
                        <strong>{question.prompt}</strong>
                        <ul>
                          {question.options.map((option, index) => (
                            <li key={option}>
                              {option}{index === question.correct_option ? " (answer key)" : ""}
                            </li>
                          ))}
                        </ul>
                        <p>{question.explanation}</p>
                      </li>
                    ))}
                  </ol>
                  <h5>Facilitator-only teaching guide</h5>
                  <p className="workspace-alert" role="note">{module.facilitator_guide.review_status}</p>
                  <p><strong>Session objective:</strong> {module.facilitator_guide.facilitator_objective}</p>
                  <p><strong>Suggested session length:</strong> {module.facilitator_guide.session_length_minutes} minutes</p>
                  <h6>Preparation</h6>
                  <ul>{module.facilitator_guide.preparation.map((item) => <li key={item}>{item}</li>)}</ul>
                  <h6>Teaching notes</h6>
                  <ul>{module.facilitator_guide.teaching_notes.map((item) => <li key={item}>{item}</li>)}</ul>
                  <h6>Discussion questions</h6>
                  <ul>{module.facilitator_guide.discussion_questions.map((item) => <li key={item}>{item}</li>)}</ul>
                  <h6>Practical activities</h6>
                  <ul>{module.facilitator_guide.practical_activities.map((item) => <li key={item}>{item}</li>)}</ul>
                  <h6>Session structure</h6>
                  <ol>
                    {module.facilitator_guide.session_structure.map((segment, index) => (
                      <li key={`${module.id}-${index}-${segment.minutes}-${segment.segment}`}>
                        <strong>{segment.minutes} min · {segment.segment}.</strong>{" "}
                        {segment.facilitator_notes}
                      </li>
                    ))}
                  </ol>
                  <h6>Safeguarding</h6>
                  <ul>{module.facilitator_guide.safeguarding.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              </details>
              {!module.is_published && (
                <>
                  {!module.reviewed_at && (
                    <label className="supervisor-curriculum__confirmation">
                      <input
                        checked={reviewConfirmed[module.id] ?? false}
                        onChange={(event) =>
                          setReviewConfirmed((current) => ({
                            ...current,
                            [module.id]: event.target.checked,
                          }))
                        }
                        type="checkbox"
                      />
                      I reviewed the learner lesson, quiz and answer key, plus
                      the separate staff guide and safeguarding notes.
                    </label>
                  )}
                  <button
                    className="button button--primary"
                    disabled={
                      busyId === module.id ||
                      (!module.reviewed_at && !reviewConfirmed[module.id])
                    }
                    onClick={() => void reviewOrPublish(module)}
                    type="button"
                  >
                    {busyId === module.id
                      ? "Saving…"
                      : module.reviewed_at
                        ? "Publish module"
                        : "Mark reviewed"}
                  </button>
                </>
              )}
            </article>
          ))
        )}
      </div>
    </section>
  );
}

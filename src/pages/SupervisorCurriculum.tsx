import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type ModuleQuestion = {
  id: number;
  position: number;
  kind: "case_study" | "assignment" | "quiz";
  prompt: string;
};

type SupervisorModule = {
  id: number;
  week_number: number;
  title: string;
  content_markdown: string;
  learning_objectives: string[];
  reflection_prompts: string[];
  questions: ModuleQuestion[];
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
                <summary>Read learner lesson, objectives, prompts and questions</summary>
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
                      I reviewed this learner-facing content and confirmed it
                      contains no facilitator-only material.
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

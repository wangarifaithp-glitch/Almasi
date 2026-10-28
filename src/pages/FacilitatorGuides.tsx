import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

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

type GuideModule = {
  id: number;
  week_number: number;
  title: string;
  facilitator_guide: FacilitatorGuide;
};

function messageFor(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return "Facilitator access is required to view teaching guides.";
  }
  return "The facilitator guide service is unavailable. Try again when the API is ready.";
}

export default function FacilitatorGuides() {
  const [modules, setModules] = useState<GuideModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    apiFetch("facilitator/guides")
      .then((response) => response.json() as Promise<GuideModule[]>)
      .then((data) => {
        if (!active) return;
        setModules(data);
        setError("");
      })
      .catch((requestError: unknown) => {
        if (active) setError(messageFor(requestError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);

  return (
    <section className="workspace-card">
      <div className="workspace-card__heading">
        <div>
          <span className="workspace-kicker">FACILITATOR-ONLY RESOURCES</span>
          <h3>Teaching guides</h3>
        </div>
        <span className="workspace-count">{modules.length} available</span>
      </div>
      <p>These teaching notes are staff resources and are not shown in learner modules.</p>
      {error && <p className="workspace-alert" role="alert">{error}</p>}
      {loading ? (
        <p className="workspace-message" role="status">Loading facilitator guides…</p>
      ) : error && modules.length === 0 ? (
        <button
          className="button button--primary"
          onClick={() => setRetry((value) => value + 1)}
          type="button"
        >
          Try again
        </button>
      ) : modules.length === 0 ? (
        <p className="workspace-message">No published module guides are available yet.</p>
      ) : (
        modules.map(({ id, week_number, title, facilitator_guide: guide }) => (
          <details className="supervisor-curriculum__module" key={id}>
            <summary>
              Week {week_number}: {title} · {guide.session_length_minutes} minutes
            </summary>
            <p className="workspace-alert" role="note">{guide.review_status}</p>
            <h4>Session objective</h4>
            <p>{guide.facilitator_objective}</p>
            <h4>Preparation</h4>
            <ul>{guide.preparation.map((item) => <li key={item}>{item}</li>)}</ul>
            <h4>Teaching notes</h4>
            <ul>{guide.teaching_notes.map((item) => <li key={item}>{item}</li>)}</ul>
            <h4>Discussion questions</h4>
            <ul>{guide.discussion_questions.map((item) => <li key={item}>{item}</li>)}</ul>
            <h4>Practical activities</h4>
            <ul>{guide.practical_activities.map((item) => <li key={item}>{item}</li>)}</ul>
            <h4>Suggested session structure (3–4 hours)</h4>
            <ol>
              {guide.session_structure.map((segment) => (
                <li key={`${segment.minutes}-${segment.segment}`}>
                  <strong>{segment.minutes} min · {segment.segment}.</strong>{" "}
                  {segment.facilitator_notes}
                </li>
              ))}
            </ol>
            <h4>Safeguarding reminders</h4>
            <ul>{guide.safeguarding.map((item) => <li key={item}>{item}</li>)}</ul>
          </details>
        ))
      )}
    </section>
  );
}

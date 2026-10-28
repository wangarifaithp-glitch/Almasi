import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type LearnerAssignment = {
  id: number;
  group_id: number;
  group_name: string;
  module_id: number;
  module_title: string;
  title: string;
  instructions: string;
  due_at: string | null;
  status: "open" | "locked" | "archived";
  submission_id: number | null;
  submission_status:
    | "draft"
    | "submitted"
    | "approved"
    | "returned_for_improvement"
    | "locked"
    | null;
  submission_content: string | null;
  submitted_at: string | null;
  feedback: string | null;
  score: number | null;
};

type AttendanceRecord = {
  session_id: number;
  session_title: string;
  module_title: string;
  starts_at: string;
  status: "present" | "absent" | "late" | "excused" | null;
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Your session expired. Sign in again to view your programme.";
  }
  return "We couldn’t load your assignments or attendance. Please retry.";
}

function formatDate(value: string | null): string {
  if (!value) return "No deadline";
  return new Date(value).toLocaleString();
}

function formatSubmissionStatus(
  status: LearnerAssignment["submission_status"],
): string {
  if (status === "returned_for_improvement") return "Return for improvement";
  if (status === "approved") return "Approved";
  if (status === "submitted") return "Submitted — awaiting review";
  if (status === "locked") return "Locked";
  if (status === "draft") return "Draft";
  return "Not started";
}

export default function LearnerProgramme() {
  const [assignments, setAssignments] = useState<LearnerAssignment[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      apiFetch("learner/assignments").then(
        (response) => response.json() as Promise<LearnerAssignment[]>,
      ),
      apiFetch("learner/attendance").then(
        (response) => response.json() as Promise<AttendanceRecord[]>,
      ),
    ])
      .then(([assignmentData, attendanceData]) => {
        if (!active) return;
        setAssignments(assignmentData);
        setAttendance(attendanceData);
        setDrafts(
          Object.fromEntries(
            assignmentData.map((assignment) => [
              assignment.id,
              assignment.submission_content ?? "",
            ]),
          ),
        );
        setError("");
      })
      .catch((requestError: unknown) => {
        if (!active) return;
        setError(getErrorMessage(requestError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);

  async function saveSubmission(assignment: LearnerAssignment, submit: boolean) {
    setBusyId(assignment.id);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch(
        `learner/assignments/${assignment.id}/submission?submit=${submit}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: drafts[assignment.id] ?? "" }),
        },
      );
      const saved = (await response.json()) as LearnerAssignment;
      setAssignments((current) =>
        current.map((item) => (item.id === saved.id ? saved : item)),
      );
      setNotice(
        submit
          ? `${assignment.title} was submitted and saved.`
          : `${assignment.title} draft was saved.`,
      );
    } catch (requestError) {
      setError(
        requestError instanceof ApiError && requestError.status === 409
          ? "This assignment is past its deadline or has been locked. Your changes were not saved."
          : getErrorMessage(requestError),
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="workspace-card">
      <div className="workspace-card__heading">
        <div>
          <span className="workspace-kicker">YOUR PROGRAMME</span>
          <h3>Assignments and attendance</h3>
        </div>
        <span className="workspace-count">{assignments.length} assignments</span>
      </div>
      {error && <p className="workspace-alert" role="alert">{error}</p>}
      {notice && <p className="learner-completion" role="status">{notice}</p>}
      {loading ? (
        <p className="workspace-message" role="status">Loading your programme records…</p>
      ) : error ? (
        <button
          className="button button--primary"
          onClick={() => setRetry((attempt) => attempt + 1)}
          type="button"
        >
          Try again
        </button>
      ) : (
        <>
          <section className="learner-module-section">
            <h4>Your assignments</h4>
            {assignments.length === 0 ? (
              <p>No group assignments are available yet.</p>
            ) : (
              assignments.map((assignment) => {
                const locked =
                  assignment.status !== "open" ||
                  (assignment.submission_status !== null &&
                    !["draft", "returned_for_improvement"].includes(
                      assignment.submission_status,
                    )) ||
                  (assignment.due_at !== null &&
                    Date.parse(assignment.due_at) < Date.now());
                return (
                  <article className="supervisor-curriculum__module" key={assignment.id}>
                    <span className="workspace-kicker">
                      {assignment.group_name} · {assignment.module_title}
                    </span>
                    <h4>{assignment.title}</h4>
                    <p>{assignment.instructions}</p>
                    <p>
                      Due: {formatDate(assignment.due_at)} · Status:{" "}
                      {formatSubmissionStatus(assignment.submission_status)}
                    </p>
                    {assignment.feedback && (
                      <p className="learner-completion">
                        Facilitator feedback{assignment.score !== null ? ` · Score ${assignment.score}/100` : ""}:{" "}
                        {assignment.feedback}
                      </p>
                    )}
                    {!locked && (
                      <>
                        <label className="learner-question">
                          <span>Your assignment response</span>
                          <textarea
                            maxLength={40_000}
                            onChange={(event) =>
                              setDrafts((current) => ({
                                ...current,
                                [assignment.id]: event.target.value,
                              }))
                            }
                            rows={5}
                            value={drafts[assignment.id] ?? ""}
                          />
                        </label>
                        <div className="workspace-header__actions">
                          <button
                            className="button button--primary"
                            disabled={busyId === assignment.id}
                            onClick={() => void saveSubmission(assignment, false)}
                            type="button"
                          >
                            {busyId === assignment.id ? "Saving…" : "Save draft"}
                          </button>
                          <button
                            className="button button--secondary"
                            disabled={busyId === assignment.id}
                            onClick={() => void saveSubmission(assignment, true)}
                            type="button"
                          >
                            Submit assignment
                          </button>
                        </div>
                      </>
                    )}
                  </article>
                );
              })
            )}
          </section>
          <section className="learner-module-section">
            <h4>Your attendance</h4>
            {attendance.length === 0 ? (
              <p>No sessions or attendance records are available yet.</p>
            ) : (
              <ul>
                {attendance.map((record) => (
                  <li key={record.session_id}>
                    {new Date(record.starts_at).toLocaleString()} · {record.session_title}{" "}
                    ({record.module_title}) · {record.status ?? "Not recorded"}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}

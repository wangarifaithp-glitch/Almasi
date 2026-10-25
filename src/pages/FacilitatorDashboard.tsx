import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type GroupSummary = {
  id: number;
  name: string;
  learner_count: number;
  upcoming_session_count: number;
  pending_submission_count: number;
  completed_module_records: number;
  eligible_module_records: number;
  attendance_records: number;
  missing_attendance_records: number;
};

type Session = {
  id: number;
  group_id: number;
  group_name: string;
  module_id: number;
  module_title: string;
  title: string;
  facilitator_plan: string;
  starts_at: string;
  ends_at: string;
  status: string;
};

type Assignment = {
  id: number;
  group_id: number;
  group_name: string;
  title: string;
  instructions: string;
  due_at: string | null;
  status: string;
};

type Submission = {
  id: number;
  assignment_id: number;
  assignment_title: string;
  group_id: number;
  learner_id: number;
  learner_name: string;
  content: string;
  status: "submitted" | "reviewed" | "locked";
  submitted_at: string | null;
  feedback: string | null;
  score: number | null;
};

type Attendance = {
  learner_id: number;
  learner_name: string;
  status: "present" | "absent" | "late" | "excused" | null;
  updated_at: string | null;
};

type SessionReport = {
  id: number;
  session_id: number;
  group_id: number;
  session_title: string;
  group_name: string;
  content: string;
  follow_up_actions: string;
  status: "draft" | "submitted";
  submitted_at: string | null;
};

type DashboardData = {
  groups: GroupSummary[];
  sessions: Session[];
  assignments: Assignment[];
  submissions: Submission[];
  reports: SessionReport[];
};

const attendanceStatuses = ["present", "absent", "late", "excused"] as const;

function messageFor(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Your sign-in expired. Sign in again to continue.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "This action is not available for your account or assigned groups.";
  }
  return "The facilitator service is unavailable. Your change was not saved.";
}

export default function FacilitatorDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [attendanceSessionId, setAttendanceSessionId] = useState("");
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [attendanceDraft, setAttendanceDraft] = useState<Record<number, string>>({});
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentInstructions, setAssignmentInstructions] = useState("");
  const [assignmentDue, setAssignmentDue] = useState("");
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<number, string>>({});
  const [scoreDrafts, setScoreDrafts] = useState<Record<number, string>>({});
  const [reportDrafts, setReportDrafts] = useState<
    Record<number, { content: string; follow_up_actions: string }>
  >({});

  useEffect(() => {
    let active = true;
    setLoading(true);
    apiFetch("facilitator/dashboard")
      .then((response) => response.json() as Promise<DashboardData>)
      .then((dashboard) => {
        if (!active) return;
        setData(dashboard);
        setFeedbackDrafts(
          Object.fromEntries(
            dashboard.submissions.map((submission) => [
              submission.id,
              submission.feedback ?? "",
            ]),
          ),
        );
        setScoreDrafts(
          Object.fromEntries(
            dashboard.submissions.map((submission) => [
              submission.id,
              submission.score?.toString() ?? "",
            ]),
          ),
        );
        setReportDrafts(
          Object.fromEntries(
            dashboard.reports.map((report) => [
              report.session_id,
              {
                content: report.content,
                follow_up_actions: report.follow_up_actions,
              },
            ]),
          ),
        );
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

  async function refresh(message = "") {
    setNotice(message);
    setRetry((attempt) => attempt + 1);
  }

  async function loadAttendance(sessionId: string) {
    setAttendanceSessionId(sessionId);
    setAttendance([]);
    if (!sessionId) return;
    setError("");
    try {
      const response = await apiFetch(`facilitator/sessions/${sessionId}/attendance`);
      const records = (await response.json()) as Attendance[];
      setAttendance(records);
      setAttendanceDraft(
        Object.fromEntries(
          records.map((record) => [record.learner_id, record.status ?? ""]),
        ),
      );
    } catch (requestError) {
      setError(messageFor(requestError));
    }
  }

  async function saveAttendance() {
    setBusy(true);
    setError("");
    try {
      await apiFetch(`facilitator/sessions/${attendanceSessionId}/attendance`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          records: attendance
            .filter((record) => attendanceDraft[record.learner_id])
            .map((record) => ({
              learner_id: record.learner_id,
              status: attendanceDraft[record.learner_id],
            })),
        }),
      });
      await loadAttendance(attendanceSessionId);
      setNotice("Attendance records were saved.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function createAssignment() {
    const session = data?.sessions.find(
      (item) => item.id === Number(selectedSessionId),
    );
    if (!session) {
      setError("Choose one of your assigned sessions.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiFetch("facilitator/assignments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          group_id: session.group_id,
          module_id: session.module_id,
          session_id: session.id,
          title: assignmentTitle,
          instructions: assignmentInstructions,
          due_at: assignmentDue ? new Date(assignmentDue).toISOString() : null,
        }),
      });
      setAssignmentTitle("");
      setAssignmentInstructions("");
      setAssignmentDue("");
      await refresh("Assignment created.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function saveFeedback(submissionId: number) {
    setBusy(true);
    setError("");
    try {
      const rawScore = scoreDrafts[submissionId]?.trim() ?? "";
      await apiFetch(`facilitator/submissions/${submissionId}/feedback`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          comments: feedbackDrafts[submissionId] ?? "",
          score: rawScore ? Number(rawScore) : null,
        }),
      });
      await refresh("Feedback was saved and the submission was marked reviewed.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function lockSubmission(submissionId: number) {
    setBusy(true);
    setError("");
    try {
      await apiFetch(`facilitator/submissions/${submissionId}/lock`, {
        method: "PUT",
      });
      await refresh("Submission locked; the learner can no longer edit it.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function saveReport(sessionId: number, submit: boolean) {
    setBusy(true);
    setError("");
    const draft = reportDrafts[sessionId] ?? {
      content: "",
      follow_up_actions: "",
    };
    try {
      await apiFetch(`facilitator/sessions/${sessionId}/report`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (submit) {
        await apiFetch(`facilitator/sessions/${sessionId}/report/submit`, {
          method: "POST",
        });
      }
      await refresh(submit ? "Session report submitted." : "Session report saved as a draft.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {error && <p className="workspace-alert" role="alert">{error}</p>}
      {notice && <p className="learner-completion" role="status">{notice}</p>}
      {loading ? (
        <p className="workspace-message" role="status">Loading your assigned groups…</p>
      ) : error && !data ? (
        <section className="workspace-message" role="alert">
          <h1>We couldn’t load your facilitator dashboard.</h1>
          <p>{error}</p>
          <button className="button button--primary" onClick={() => setRetry((value) => value + 1)} type="button">
            Try again
          </button>
        </section>
      ) : (
        <>
          <section className="workspace-intro">
            <span className="eyebrow">ALMASI facilitator space</span>
            <h2>Support your assigned groups.</h2>
            <p>Only groups assigned to your facilitator account appear here.</p>
          </section>
          <section className="workspace-staff-grid">
            {data?.groups.map((group) => (
              <article className="workspace-card workspace-staff-card" key={group.id}>
                <span className="workspace-kicker">{group.learner_count} learners</span>
                <h3>{group.name}</h3>
                <p>
                  {group.completed_module_records} of {group.eligible_module_records} module records complete
                </p>
                <p>{group.pending_submission_count} submissions awaiting review</p>
                <p>
                  Attendance: {group.attendance_records} recorded ·{" "}
                  {group.missing_attendance_records} missing
                </p>
                <p>{group.upcoming_session_count} upcoming sessions</p>
              </article>
            ))}
            {!data?.groups.length && (
              <p className="workspace-message">No groups have been assigned to you yet.</p>
            )}
          </section>

          <section className="workspace-card">
            <div className="workspace-card__heading">
              <div><span className="workspace-kicker">SESSION PLANS</span><h3>Assigned sessions</h3></div>
              <span className="workspace-count">{data?.sessions.length ?? 0} sessions</span>
            </div>
            {data?.sessions.map((session) => {
              const report = data.reports.find((item) => item.session_id === session.id);
              return (
                <details className="supervisor-curriculum__module" key={session.id}>
                  <summary>
                    {session.group_name} · {session.title} · {new Date(session.starts_at).toLocaleString()}
                  </summary>
                  <p>{session.module_title}</p>
                  <div className="learner-module-prose">
                    {session.facilitator_plan || "No facilitator plan has been added for this session."}
                  </div>
                  <label className="learner-question">
                    <span>Session notes</span>
                    <textarea
                      disabled={report?.status === "submitted"}
                      maxLength={20_000}
                      onChange={(event) =>
                        setReportDrafts((current) => ({
                          ...current,
                          [session.id]: {
                            ...(current[session.id] ?? { content: "", follow_up_actions: "" }),
                            content: event.target.value,
                          },
                        }))
                      }
                      rows={3}
                      value={reportDrafts[session.id]?.content ?? ""}
                    />
                  </label>
                  <label className="learner-question">
                    <span>Follow-up actions</span>
                    <textarea
                      disabled={report?.status === "submitted"}
                      maxLength={10_000}
                      onChange={(event) =>
                        setReportDrafts((current) => ({
                          ...current,
                          [session.id]: {
                            ...(current[session.id] ?? { content: "", follow_up_actions: "" }),
                            follow_up_actions: event.target.value,
                          },
                        }))
                      }
                      rows={2}
                      value={reportDrafts[session.id]?.follow_up_actions ?? ""}
                    />
                  </label>
                  {report?.status === "submitted" ? (
                    <p className="learner-save-status">Report submitted.</p>
                  ) : (
                    <div className="workspace-header__actions">
                      <button className="button button--primary" disabled={busy} onClick={() => void saveReport(session.id, false)} type="button">
                        Save report
                      </button>
                      <button className="button button--secondary" disabled={busy} onClick={() => void saveReport(session.id, true)} type="button">
                        Submit report
                      </button>
                    </div>
                  )}
                </details>
              );
            })}
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">ASSIGNMENTS</span>
            <h3>Create an assignment for an assigned session</h3>
            <label className="learner-question">
              <span>Session</span>
              <select value={selectedSessionId} onChange={(event) => setSelectedSessionId(event.target.value)}>
                <option value="">Choose a session</option>
                {data?.sessions.map((session) => (
                  <option key={session.id} value={session.id}>
                    {session.group_name} · {session.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="learner-question">
              <span>Assignment title</span>
              <input maxLength={200} onChange={(event) => setAssignmentTitle(event.target.value)} value={assignmentTitle} />
            </label>
            <label className="learner-question">
              <span>Instructions</span>
              <textarea maxLength={20_000} onChange={(event) => setAssignmentInstructions(event.target.value)} rows={3} value={assignmentInstructions} />
            </label>
            <label className="learner-question">
              <span>Optional deadline</span>
              <input type="datetime-local" onChange={(event) => setAssignmentDue(event.target.value)} value={assignmentDue} />
            </label>
            <button className="button button--primary" disabled={busy || !selectedSessionId} onClick={() => void createAssignment()} type="button">
              Create assignment
            </button>
            {data?.assignments.map((assignment) => (
              <p key={assignment.id}>
                {assignment.group_name} · {assignment.title} · {assignment.status}
              </p>
            ))}
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">SUBMISSIONS</span>
            <h3>Review learner work</h3>
            {!data?.submissions.length && <p>No submitted work is awaiting review.</p>}
            {data?.submissions.map((submission) => (
              <article className="supervisor-curriculum__module" key={submission.id}>
                <h4>{submission.assignment_title} · {submission.learner_name}</h4>
                <div className="learner-module-prose">{submission.content}</div>
                <label className="learner-question">
                  <span>Feedback for this learner</span>
                  <textarea
                    maxLength={20_000}
                    onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [submission.id]: event.target.value }))}
                    rows={3}
                    value={feedbackDrafts[submission.id] ?? ""}
                  />
                </label>
                <label className="learner-question">
                  <span>Optional score (0–100)</span>
                  <input
                    max={100}
                    min={0}
                    onChange={(event) => setScoreDrafts((current) => ({ ...current, [submission.id]: event.target.value }))}
                    type="number"
                    value={scoreDrafts[submission.id] ?? ""}
                  />
                </label>
                <div className="workspace-header__actions">
                  <button className="button button--primary" disabled={busy} onClick={() => void saveFeedback(submission.id)} type="button">
                    Save feedback
                  </button>
                  {submission.status !== "locked" && (
                    <button className="button button--secondary" disabled={busy} onClick={() => void lockSubmission(submission.id)} type="button">
                      Lock submission
                    </button>
                  )}
                </div>
              </article>
            ))}
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">ATTENDANCE</span>
            <h3>Record or correct attendance</h3>
            <label className="learner-question">
              <span>Assigned session</span>
              <select value={attendanceSessionId} onChange={(event) => void loadAttendance(event.target.value)}>
                <option value="">Choose a session</option>
                {data?.sessions.map((session) => (
                  <option key={session.id} value={session.id}>
                    {session.group_name} · {session.title}
                  </option>
                ))}
              </select>
            </label>
            {attendance.map((record) => (
              <label className="learner-question" key={record.learner_id}>
                <span>{record.learner_name} · {record.status ?? "Not recorded"}</span>
                <select
                  onChange={(event) => setAttendanceDraft((current) => ({ ...current, [record.learner_id]: event.target.value }))}
                  value={attendanceDraft[record.learner_id] ?? ""}
                >
                  <option value="">Not recorded</option>
                  {attendanceStatuses.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
            ))}
            {attendance.length > 0 && (
              <button className="button button--primary" disabled={busy} onClick={() => void saveAttendance()} type="button">
                Save attendance
              </button>
            )}
          </section>
        </>
      )}
    </>
  );
}

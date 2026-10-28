import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type Group = {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  learner_count: number;
  facilitator_names: string[];
};

type CompletionRecord = {
  learner_id: number;
  learner_name: string;
  week_number: number;
  module_title: string;
  completed_at: string | null;
};

type ProgrammeReport = {
  active_learners: number;
  active_facilitators: number;
  active_groups: number;
  published_modules: number;
  completed_module_records: number;
  attendance_records: number;
  missing_attendance_records: number;
  submitted_assignments: number;
  awaiting_review: number;
  overdue_session_reports: number;
  groups: Group[];
  completion_records: CompletionRecord[];
};

const metrics: Array<[keyof ProgrammeReport, string]> = [
  ["active_learners", "Active learners"],
  ["active_facilitators", "Assigned facilitators"],
  ["active_groups", "Active groups"],
  ["published_modules", "Published modules"],
  ["completed_module_records", "Module completions"],
  ["attendance_records", "Attendance recorded"],
  ["missing_attendance_records", "Attendance not recorded"],
  ["submitted_assignments", "Submitted assignments"],
  ["awaiting_review", "Awaiting review"],
  ["overdue_session_reports", "Overdue session reports"],
];

function messageFor(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return "Supervisor access is required to view programme reports.";
  }
  return "Programme reporting is unavailable. Try again after the API and database are ready.";
}

export default function SupervisorDashboard() {
  const [report, setReport] = useState<ProgrammeReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    apiFetch("supervisor/reports")
      .then((response) => response.json() as Promise<ProgrammeReport>)
      .then((data) => {
        if (!active) return;
        setReport(data);
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

  async function exportReport() {
    setExporting(true);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch("supervisor/reports/export");
      const file = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = file;
      link.download = "almasi-progress-report.csv";
      link.click();
      URL.revokeObjectURL(file);
      setNotice("The authorised progress report was exported.");
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setExporting(false);
    }
  }

  return (
    <>
      <section className="workspace-intro">
        <span className="eyebrow">ALMASI Supervisor space</span>
        <h2>Programme overview.</h2>
        <p>
          Progress and attendance summaries are loaded from authorised
          programme records. Private learner reflections and notes are excluded.
        </p>
      </section>
      {error && <p className="workspace-alert" role="alert">{error}</p>}
      {notice && <p className="learner-completion" role="status">{notice}</p>}
      {loading ? (
        <p className="workspace-message" role="status">Loading programme records…</p>
      ) : error && !report ? (
        <section className="workspace-message" role="alert">
          <h1>We couldn’t load programme reports.</h1>
          <p>{error}</p>
          <button className="button button--primary" onClick={() => setRetry((value) => value + 1)} type="button">
            Try again
          </button>
        </section>
      ) : report ? (
        <>
          <section className="dashboard-hero dashboard-hero--supervisor">
            <div>
              <span className="dashboard-hero__eyebrow">SUPERVISOR DASHBOARD</span>
              <h3>See the whole programme at a glance.</h3>
              <p>
                Monitor learner progress, facilitator activity, attendance, and
                curriculum readiness using authorised programme records.
              </p>
            </div>
            <div className="dashboard-hero__illustration" aria-hidden="true">◒</div>
          </section>
          <section className="workspace-staff-grid">
            {metrics.map(([key, label]) => (
              <article className="workspace-card workspace-staff-card" key={key}>
                <span className="workspace-kicker">{label}</span>
                <strong className="workspace-count">{report[key] as number}</strong>
              </article>
            ))}
          </section>
          <section className="dashboard-insight-grid" aria-label="Supervisor insights">
            <article className="dashboard-insight">
              <div className="dashboard-insight__heading">
                <span>MODULE COMPLETION</span>
                <strong>
                  {report.published_modules
                    ? Math.round((report.completed_module_records / Math.max(report.published_modules * Math.max(report.active_learners, 1), 1)) * 100)
                    : 0}%
                </strong>
              </div>
              <div className="dashboard-bar">
                <span
                  style={{
                    width: `${Math.min(
                      100,
                      report.published_modules
                        ? Math.round((report.completed_module_records / Math.max(report.published_modules * Math.max(report.active_learners, 1), 1)) * 100)
                        : 0,
                    )}%`,
                  }}
                />
              </div>
              <p>Completed module records across active learners.</p>
            </article>
            <article className="dashboard-insight">
              <div className="dashboard-insight__heading">
                <span>REVIEW QUEUE</span>
                <strong>{report.awaiting_review}</strong>
              </div>
              <p>
                Submitted assignments awaiting facilitator review. Use the
                facilitator workspace to resolve feedback.
              </p>
            </article>
          </section>
          <section className="workspace-card">
            <div className="workspace-card__heading">
              <div>
                <span className="workspace-kicker">GROUP OVERVIEW</span>
                <h3>Attendance and module progress</h3>
              </div>
              <button className="button button--primary" disabled={exporting} onClick={() => void exportReport()} type="button">
                {exporting ? "Preparing…" : "Export progress CSV"}
              </button>
            </div>
            {report.groups.length === 0 ? (
              <p>No active groups are configured.</p>
            ) : (
              report.groups.map((group) => (
                <article className="supervisor-curriculum__module" key={group.id}>
                  <h4>{group.name}</h4>
                  <p>{group.learner_count} learners · Facilitators: {group.facilitator_names.join(", ") || "None assigned"}</p>
                  <p>{group.description || "No group description."}</p>
                </article>
              ))
            )}
          </section>
          <section className="workspace-card">
            <span className="workspace-kicker">COMPLETION RECORDS</span>
            <h3>Recent completed modules</h3>
            {report.completion_records.length === 0 ? (
              <p>No module completion records have been saved yet.</p>
            ) : (
              <ul>
                {report.completion_records.map((record, index) => (
                  <li key={`${record.learner_id}-${record.week_number}-${index}`}>
                    {record.learner_name} · Week {record.week_number}: {record.module_title} ·{" "}
                    {record.completed_at
                      ? new Date(record.completed_at).toLocaleString()
                      : "Completion time unavailable"}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </>
  );
}

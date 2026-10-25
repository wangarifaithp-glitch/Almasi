import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Brand from "../components/Brand";
import { ApiError, apiFetch } from "../lib/api";
import LearnerModules from "./LearnerModules";
import LearnerProgramme from "./LearnerProgramme";
import FacilitatorDashboard from "./FacilitatorDashboard";
import SupervisorDashboard from "./SupervisorDashboard";
import AdministratorDashboard from "./AdministratorDashboard";
import SupervisorCurriculum from "./SupervisorCurriculum";

type WorkspaceRole = "learner" | "facilitator" | "supervisor" | "administrator";

type WorkspaceAccess = {
  role: WorkspaceRole;
  workspace: WorkspaceRole;
};

const roleLabels: Record<WorkspaceRole, string> = {
  learner: "Learner",
  facilitator: "Facilitator",
  supervisor: "Supervisor",
  administrator: "Administrator",
};

function LearnerWorkspace() {
  return (
    <>
      <LearnerModules />
      <LearnerProgramme />
    </>
  );
}

export default function WorkspacePage({ role }: { role: WorkspaceRole }) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "ready" | "forbidden" | "error">("loading");
  const [signOutError, setSignOutError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    apiFetch(`workspaces/${role}`)
      .then((response) => response.json() as Promise<WorkspaceAccess>)
      .then((access) => {
        if (!active) return;
        if (access.role !== role || access.workspace !== role) {
          setStatus("forbidden");
          return;
        }
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (!active) return;
        setStatus(error instanceof ApiError && error.status === 403 ? "forbidden" : "error");
      });
    return () => {
      active = false;
    };
  }, [retry, role]);

  async function signOut() {
    try {
      await apiFetch("auth/logout", { method: "POST" });
      navigate("/auth", { replace: true });
    } catch (error) {
      setSignOutError(
        error instanceof ApiError
          ? "We couldn’t sign you out. Please retry."
          : "The account service is unavailable. Please retry signing out.",
      );
    }
  }

  return (
    <main className="workspace-page">
      <header className="workspace-header">
        <Brand />
        <div className="workspace-header__actions">
          <span>{roleLabels[role]}</span>
          <button className="workspace-signout" onClick={signOut} type="button">
            Sign out
          </button>
        </div>
      </header>
      <div className="workspace-content">
        {signOutError && <p className="workspace-alert" role="alert">{signOutError}</p>}
        {status === "loading" ? (
          <p className="workspace-message" role="status">Verifying your workspace access…</p>
        ) : status === "forbidden" ? (
          <section className="workspace-message" role="alert">
            <h1>That workspace is not available for this account.</h1>
            <p>Your account does not have permission to open this area.</p>
            <Link className="button button--primary" to="/auth">Return to sign in</Link>
          </section>
        ) : status === "error" ? (
          <section className="workspace-message" role="alert">
            <h1>We couldn’t load your workspace.</h1>
            <p>The account service may be unavailable. Please try again.</p>
            <button
              className="button button--primary"
              onClick={() => {
                setStatus("loading");
                setRetry((attempt) => attempt + 1);
              }}
            >
              Try again
            </button>
          </section>
        ) : (
          <>
            {role !== "learner" && (
              <div className="workspace-banner" role="status">
                Workspace access is verified. Only records allowed for your
                assigned role are shown.
              </div>
            )}
            {role === "learner" ? (
              <LearnerWorkspace />
            ) : role === "facilitator" ? (
              <FacilitatorDashboard />
            ) : role === "supervisor" ? (
              <>
                <SupervisorDashboard />
                <SupervisorCurriculum />
              </>
            ) : (
              <>
                <AdministratorDashboard />
                <SupervisorCurriculum />
              </>
            )}
            <p className="workspace-boundary">
                    Private learner reflections and notes are not displayed in staff workspaces.
            </p>
          </>
        )}
      </div>
      <footer className="workspace-footer">
        <Link to="/">← Return to the ALMASI website</Link>
        <span>Refined in Faith, Growing in Confidence</span>
      </footer>
    </main>
  );
}

import { useEffect, useState, type ReactNode } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { ApiError, apiFetch } from "../lib/api";

type Role = "learner" | "facilitator" | "supervisor" | "administrator";

type ProtectedRouteProps = {
  children: ReactNode;
  requiredRole: Role;
};

const workspacePaths: Record<Role, string> = {
  learner: "/app/learner",
  facilitator: "/app/facilitator",
  supervisor: "/app/supervisor",
  administrator: "/app/administrator",
};

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const location = useLocation();
  const [role, setRole] = useState<Role | "unauthenticated" | "error" | "checking">("checking");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;

    apiFetch("auth/me")
      .then(async (response) => {
        const user: { role?: unknown } = await response.json();
        if (!active) return;
        if (
          user.role === "learner" ||
          user.role === "facilitator" ||
          user.role === "supervisor" ||
          user.role === "administrator"
        ) {
          setRole(user.role);
        } else {
          setRole("error");
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          setRole("unauthenticated");
        } else {
          setRole("error");
        }
      });

    return () => {
      active = false;
    };
  }, [retry]);

  if (role === "checking") {
    return <main className="placeholder-page" aria-live="polite">Checking your account…</main>;
  }

  if (role === requiredRole) {
    return <>{children}</>;
  }

  if (role === "unauthenticated") {
    return (
      <Navigate
        to="/auth"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  if (role !== "error" && role !== requiredRole) {
    return <Navigate to={workspacePaths[role]} replace />;
  }

  return (
    <main className="placeholder-page">
      <div className="placeholder-card">
        <span className="eyebrow">Connection issue</span>
        <h1>We couldn’t check your account.</h1>
        <p>Please check your connection and try again.</p>
        <button className="button button--primary" onClick={() => {
          setRole("checking");
          setRetry((attempt) => attempt + 1);
        }}>
          Try again
        </button>
        <p><Link className="text-link" to="/auth">Return to sign in</Link></p>
      </div>
    </main>
  );
}

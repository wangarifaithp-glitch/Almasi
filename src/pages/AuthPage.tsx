import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import Brand from "../components/Brand";
import { ApiError, apiFetch } from "../lib/api";

type AuthMode = "login" | "signup" | "forgot" | "reset" | "verify";

const passwordChecks = [
  { label: "At least 8 characters", test: (value: string) => value.length >= 8 },
  { label: "An uppercase and a lowercase letter", test: (value: string) => /[a-z]/.test(value) && /[A-Z]/.test(value) },
  { label: "A number", test: (value: string) => /\d/.test(value) },
  { label: "A special character", test: (value: string) => /[^A-Za-z0-9\s]/.test(value) },
];

function isStrongPassword(value: string): boolean {
  return passwordChecks.every(({ test }) => test(value));
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "That email and password combination wasn’t recognized, or the email has not been verified.";
    if (error.status === 403) return "Please verify your email address before signing in.";
    if (error.status === 409) return "An account already exists for that email address. Try signing in instead.";
    if (error.status === 422) return "Please check the details and password requirements, then try again.";
    if (error.status === 400) return "This password reset link is invalid or has expired. Request a new one.";
    if (error.status >= 500) return "The account service is temporarily unavailable. Please try again shortly.";
  }
  if (error instanceof TypeError) {
    return "We couldn’t reach ALMASI’s account service. Please try again after the API is running.";
  }
  return "We couldn’t connect to the account service. Please check your connection and try again.";
}

function getMode(value: string | null): AuthMode {
  return value === "signup" || value === "forgot" || value === "reset" || value === "verify" ? value : "login";
}

export default function AuthPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const mode = location.pathname === "/signup"
    ? "signup"
    : getMode(searchParams.get("mode"));
  const resetToken = searchParams.get("token") ?? "";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (mode !== "verify") return;
    void (async () => {
      try {
        const response = await apiFetch(`auth/verify-email?token=${encodeURIComponent(resetToken)}`);
        setMessage((await response.json() as { message: string }).message);
      } catch {
        setError("This verification link is invalid or has expired.");
      }
    })();
  }, [mode, resetToken]);

  function changeMode(nextMode: AuthMode) {
    setError("");
    setMessage("");
    setPassword("");
    setConfirmPassword("");
    navigate(nextMode === "signup" ? "/signup" : `/auth${nextMode === "login" ? "" : `?mode=${nextMode}`}`);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");

    if ((mode === "signup" || mode === "reset") && !isStrongPassword(password)) {
      setError("Choose a password that meets all the requirements below.");
      return;
    }
    if ((mode === "signup" || mode === "reset") && password !== confirmPassword) {
      setError("Your passwords don’t match.");
      return;
    }
    if (mode === "reset" && !resetToken) {
      setError("This password reset link is invalid or has expired. Request a new one.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === "signup") {
        await apiFetch("auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password }),
        });
        setMessage("Check your email for a verification link before signing in.");
        setPassword("");
        setConfirmPassword("");
        return;
      }
      if (mode === "login") {
        const response = await apiFetch("auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const user = (await response.json()) as { role?: string };
        const state = location.state;
        const rolePath: Record<string, string> = {
          learner: "/app/learner",
          facilitator: "/app/facilitator",
          supervisor: "/app/supervisor",
          administrator: "/app/administrator",
        };
        const returnTo =
          typeof state === "object" &&
          state !== null &&
          "from" in state &&
          typeof state.from === "string" &&
          state.from.startsWith("/app/")
            ? state.from
            : rolePath[user.role ?? ""] ?? "/app/learner";
        navigate(returnTo, { replace: true });
        return;
      }
      if (mode === "forgot") {
        await apiFetch("auth/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        setMessage("If an account matches that email, we’ve sent a password reset link. Please check your inbox.");
        return;
      }

      await apiFetch("auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: resetToken, password }),
      });
      setMessage("Your password has been updated. You can now sign in with your new password.");
      setPassword("");
      setConfirmPassword("");
      navigate("/auth", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  }

  const isPasswordForm = mode === "signup" || mode === "reset";
  const isVerification = mode === "verify";
  const title =
    mode === "verify"
      ? "Verify your email."
      : mode === "signup"
      ? "Begin your journey."
      : mode === "forgot"
        ? "Let’s get you back in."
        : mode === "reset"
          ? "Choose a new password."
          : "Welcome back.";
  const subtitle =
    mode === "verify"
      ? "Confirm your email address to activate your ALMASI account."
      : mode === "signup"
      ? "Create your ALMASI account and take your next step."
      : mode === "forgot"
        ? "Enter your email and we’ll send you a secure password reset link."
        : mode === "reset"
          ? "Set a strong password to secure your account."
          : "Sign in to continue your ALMASI journey.";

  return (
    <main className="auth-page">
      <section className="auth-story" aria-label="About ALMASI">
        <img className="auth-story__image" src="/almasi-mentorship.png" alt="" />
        <div className="auth-story__shade" />
        <div className="auth-story__content">
          <Brand light />
          <div className="auth-story__quote">
            <span className="eyebrow">Faith · Confidence · Becoming</span>
            <h1>A space to grow into who you’re created to be.</h1>
            <p>Refined in faith, growing in confidence.</p>
          </div>
          <span className="auth-story__caption">ALMASI MENTORSHIP</span>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel__top">
          <Brand />
          {mode === "reset" ? (
            <p><Link className="auth-text-button" to="/auth">Back to sign in</Link></p>
          ) : (
            <p>
              {mode === "signup"
                  ? "Already have an account?"
                  : mode === "forgot"
                    ? "Remember your password?"
                  : "New to ALMASI?"}{" "}
              {mode === "signup" || mode === "forgot"
                  ? <Link className="auth-text-button" to="/auth">Sign in</Link>
                  : <Link className="auth-text-button" to="/signup">Create an account</Link>}
            </p>
          )}
        </div>

        <div className="auth-form-wrap">
          <span className="eyebrow">Your next chapter starts here</span>
          <h2>{title}</h2>
          <p className="auth-form__subtitle">{subtitle}</p>
          {mode === "reset" && (
            <div className="auth-form__forgot">
              <button className="auth-text-button" type="button" onClick={() => changeMode("forgot")}>
                Need a new reset link?
              </button>
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            {isVerification ? (
              <p className="auth-alert" role="status">
                {message || error || "Verifying your email address…"}
              </p>
            ) : (
            <>
            {mode === "signup" && (
              <label className="auth-field">
                <span>Full name</span>
                <input
                  autoComplete="name"
                  maxLength={120}
                  name="name"
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Your name"
                  required
                  value={name}
                />
              </label>
            )}

            {mode !== "reset" && (
              <label className="auth-field">
                <span>Email address</span>
                <input
                  autoComplete="email"
                  name="email"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  required
                  type="email"
                  value={email}
                />
              </label>
            )}

            {mode !== "forgot" && (
              <label className="auth-field">
                <span>{mode === "reset" ? "New password" : "Password"}</span>
                <input
                  autoComplete={mode === "signup" ? "new-password" : mode === "reset" ? "new-password" : "current-password"}
                  name="password"
                  maxLength={128}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={mode === "reset" ? "Enter your new password" : "Enter your password"}
                  required
                  type="password"
                  value={password}
                />
              </label>
            )}

            {mode === "login" && (
              <div className="auth-form__forgot">
                <button className="auth-text-button" type="button" onClick={() => changeMode("forgot")}>
                  Forgot password?
                </button>
              </div>
            )}

            {isPasswordForm && (
              <>
                <ul className="password-rules" aria-label="Password requirements">
                  {passwordChecks.map(({ label, test }) => (
                    <li className={test(password) ? "is-met" : ""} key={label}>
                      <span aria-hidden="true">{test(password) ? "✓" : "○"}</span>
                      {label}
                    </li>
                  ))}
                </ul>
                <label className="auth-field">
                  <span>Confirm password</span>
                  <input
                    autoComplete="new-password"
                    name="confirm-password"
                    maxLength={128}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Enter your password again"
                    required
                    type="password"
                    value={confirmPassword}
                  />
                </label>
              </>
            )}

            {error && <p className="auth-alert auth-alert--error" role="alert">{error}</p>}
            {message && <p className="auth-alert auth-alert--success" role="status">{message}</p>}

            <button className="button button--primary auth-submit" disabled={isSubmitting} type="submit">
              {isSubmitting
                ? "Please wait…"
                : mode === "signup"
                  ? "Create account"
                  : mode === "forgot"
                    ? "Send reset link"
                    : mode === "reset"
                      ? "Update password"
                      : "Sign in"}
              {!isSubmitting && <span aria-hidden="true">→</span>}
            </button>
            </>
            )}
          </form>

          <p className="auth-privacy">
            Your information is handled with care. Read our{" "}
            <Link to="/privacy-policy">Privacy Policy</Link>.
          </p>
          <Link className="auth-back-link" to="/">← Back to ALMASI</Link>
        </div>
      </section>
    </main>
  );
}

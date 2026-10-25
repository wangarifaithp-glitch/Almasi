import { Link } from "react-router-dom";
import Brand from "../components/Brand";

type AppPlaceholderProps = {
  audience: "Learner" | "Facilitator" | "Supervisor";
};

export function AppPlaceholder({ audience }: AppPlaceholderProps) {
  return (
    <main className="placeholder-page">
      <div className="placeholder-card">
        <Brand />
        <span className="eyebrow">ALMASI {audience} space</span>
        <h1>This space is being thoughtfully prepared.</h1>
        <p>
          The {audience.toLowerCase()} workspace is not available yet. Access
          controls and its features will be added before this space opens.
        </p>
        <Link className="text-link" to="/">
          ← Back to the welcome page
        </Link>
      </div>
    </main>
  );
}

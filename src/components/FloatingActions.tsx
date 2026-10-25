import { useEffect, useState } from "react";
import {
  getContactDestination,
  getHttpsUrl,
} from "../lib/publicDestinations";

const contactUrl = getContactDestination(import.meta.env.VITE_CONTACT_URL);
const developerUrl =
  getHttpsUrl(import.meta.env.VITE_DEVELOPER_URL) ?? "/developer";

export default function FloatingActions() {
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const updateVisibility = () => setShowBackToTop(window.scrollY > 360);

    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });
    return () => window.removeEventListener("scroll", updateVisibility);
  }, []);

  return (
    <nav className="floating-actions" aria-label="Quick links">
      <a
        className="floating-action"
        href={contactUrl}
        aria-label="Contact ALMASI"
        title="Contact ALMASI"
      >
        <span aria-hidden="true">✉</span>
      </a>
      <a
        className="floating-action"
        href={developerUrl}
        aria-label="Developer and portfolio"
        title="Developer and portfolio"
        {...(developerUrl.startsWith("https://")
          ? { target: "_blank", rel: "noreferrer" }
          : {})}
      >
        <span aria-hidden="true">↗</span>
      </a>
      {showBackToTop && (
        <button
          className="floating-action floating-action--top"
          type="button"
          aria-label="Back to top"
          title="Back to top"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <span aria-hidden="true">↑</span>
        </button>
      )}
    </nav>
  );
}

import { Link } from "react-router-dom";
import Brand from "../components/Brand";
import { getHttpsUrl } from "../lib/publicDestinations";

const portfolioUrl = getHttpsUrl(import.meta.env.VITE_DEVELOPER_URL);

export default function DeveloperPage() {
  return (
    <main className="legal-page">
      <div className="container legal-page__container">
        <Brand />
        <Link className="legal-page__back" to="/">
          ← Back to ALMASI
        </Link>
        <article className="legal-document developer-document">
          <span className="eyebrow">About the developer</span>
          <h1>Built with care for the ALMASI community.</h1>
          {portfolioUrl ? (
            <>
              <p className="legal-document__intro">
                Visit the developer’s portfolio for more information about the
                work behind this site.
              </p>
              <a
                className="button button--primary"
                href={portfolioUrl}
                target="_blank"
                rel="noreferrer"
              >
                Visit developer portfolio <span aria-hidden="true">↗</span>
              </a>
            </>
          ) : (
            <p className="legal-document__intro">
              Developer portfolio details have not been configured yet. No
              personal developer information or portfolio URL is published on
              this page.
            </p>
          )}
          <p className="developer-document__note">
            For questions about ALMASI or privacy, use the{" "}
            <Link to="/#contact">ALMASI contact route</Link>.
          </p>
        </article>
      </div>
    </main>
  );
}

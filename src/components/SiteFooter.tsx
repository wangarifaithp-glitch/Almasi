import { Link } from "react-router-dom";
import Brand from "./Brand";
import { getHttpsUrl } from "../lib/publicDestinations";

const socialLinks = [
  { label: "Instagram", url: getHttpsUrl(import.meta.env.VITE_INSTAGRAM_URL) },
  { label: "Facebook", url: getHttpsUrl(import.meta.env.VITE_FACEBOOK_URL) },
  { label: "TikTok", url: getHttpsUrl(import.meta.env.VITE_TIKTOK_URL) },
  { label: "YouTube", url: getHttpsUrl(import.meta.env.VITE_YOUTUBE_URL) },
];

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__content">
        <div className="site-footer__brand">
          <Brand light />
          <p>Refined in Faith, Growing in Confidence.</p>
        </div>

        <nav className="site-footer__nav" aria-label="Footer navigation">
          <Link to="/#about-us">About Us</Link>
          <Link to="/#contact">Contact</Link>
          <Link to="/privacy-policy">Privacy Policy</Link>
          <Link to="/developer">Developer</Link>
        </nav>

        <div className="site-footer__social">
          <h2>Follow ALMASI</h2>
          <ul>
            {socialLinks.map(({ label, url }) => (
              <li key={label}>
                {url?.trim() ? (
                  <a href={url.trim()} target="_blank" rel="noreferrer">
                    {label}
                  </a>
                ) : (
                  <span className="social-placeholder">
                    {label} <small>URL not set</small>
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="site-footer__bottom">
        <div className="container site-footer__bottom-inner">
          <span>© {new Date().getFullYear()} ALMASI. All rights reserved.</span>
          <span>Faith. Confidence. Becoming.</span>
        </div>
      </div>
    </footer>
  );
}

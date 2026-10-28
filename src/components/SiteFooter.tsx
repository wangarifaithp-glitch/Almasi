import { Link } from "react-router-dom";
import Brand from "./Brand";
import { getHttpsUrl } from "../lib/publicDestinations";

const developerUrl = "https://github.com/wangarifaithp-glitch/My-Potifolio";

const socialLinks = [
  {
    label: "Instagram",
    icon: "/social/instagram.svg",
    url:
      getHttpsUrl(import.meta.env.VITE_INSTAGRAM_URL) ??
      "https://www.instagram.com/",
  },
  {
    label: "Facebook",
    icon: "/social/facebook.svg",
    url:
      getHttpsUrl(import.meta.env.VITE_FACEBOOK_URL) ??
      "https://www.facebook.com/",
  },
  {
    label: "TikTok",
    icon: "/social/tiktok.svg",
    url:
      getHttpsUrl(import.meta.env.VITE_TIKTOK_URL) ??
      "https://www.tiktok.com/",
  },
  {
    label: "YouTube",
    icon: "/social/youtube.svg",
    url:
      getHttpsUrl(import.meta.env.VITE_YOUTUBE_URL) ??
      "https://www.youtube.com/",
  },
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
          <a href={developerUrl} target="_blank" rel="noreferrer">
            Developer
          </a>
        </nav>

        <div className="site-footer__social">
          <h2>Follow ALMASI</h2>
          <ul>
            {socialLinks.map(({ label, icon, url }) => (
              <li key={label}>
                {url?.trim() ? (
                  <a
                    href={url.trim()}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Follow ALMASI on ${label}`}
                  >
                    <img src={icon} alt="" aria-hidden="true" />
                  </a>
                ) : (
                  <span
                    className="social-placeholder"
                    title={`${label} URL not set`}
                    aria-label={`${label} URL not set`}
                  >
                    <img src={icon} alt="" aria-hidden="true" />
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

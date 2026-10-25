import { Link } from "react-router-dom";
import Brand from "./Brand";

export default function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Brand />
        <nav className="site-nav" aria-label="Main navigation">
          <a href="#home">Home</a>
          <a href="#about-us">About Us</a>
          <a href="#programme">Programme</a>
          <a href="#contact">Contact</a>
        </nav>
        <div className="site-header__actions">
          <Link className="header-signin" to="/auth?mode=login">
            Sign In
          </Link>
          <Link className="button button--small button--header-cta" to="/signup">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

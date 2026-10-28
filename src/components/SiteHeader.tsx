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
          <Link className="header-auth-button header-auth-button--login" to="/auth?mode=login">
            <span>Log in</span>
            <span className="header-auth-button__icon" aria-hidden="true">↗</span>
          </Link>
          <Link className="header-auth-button header-auth-button--signup" to="/signup">
            <span>Sign up</span>
            <span className="header-auth-button__icon" aria-hidden="true">↗</span>
          </Link>
        </div>
      </div>
    </header>
  );
}

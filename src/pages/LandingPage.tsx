import { Link } from "react-router-dom";
import SiteHeader from "../components/SiteHeader";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <SiteHeader />
      <main>
        <section className="hero" id="home">
          <img
            className="hero__background"
            src="/almasi-girls.png"
            alt=""
            aria-hidden="true"
          />
          <div className="container hero__grid">
            <div className="hero__copy">
              <span className="eyebrow">
                Faith · Confidence · Becoming
              </span>
              <h1>
                Become who you are
                <br />
                <span>created to be.</span>
              </h1>
              <p className="hero__intro">
                A faith-centered mentorship journey for girls to discover
                their strengths, grow in confidence, and take their next steps
                with support.
              </p>
              <div className="hero__actions">
                <a className="button button--primary" href="#programme">
                  Explore the Programme <span aria-hidden="true">→</span>
                </a>
                <Link className="button button--hero-outline" to="/signup">
                  Create an Account
                </Link>
                <Link className="text-link" to="/auth?mode=login">
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="welcome-section about-section" id="about-us">
          <div className="container welcome-section__inner">
            <div className="section-kicker">
              <span className="section-kicker__line" />
              <span>About ALMASI</span>
            </div>
            <h2>
              A place to grow into
              <br />
              <span>your God-given potential.</span>
            </h2>
            <p className="welcome-section__body">
              ALMASI is a 12-week mentorship programme for girls aged 12–16.
              Through faith, supportive guidance, and practical learning, girls
              are encouraged to build confidence, develop life skills, and
              understand themselves and their potential.
            </p>
            <div className="about-pillars" aria-label="ALMASI focus areas">
              <span>Faith</span>
              <span>Confidence</span>
              <span>Life skills</span>
              <span>Personal growth</span>
            </div>
          </div>
        </section>

        <section className="programme-section" id="programme">
          <div className="container programme-section__inner">
            <div className="programme-section__intro">
              <div className="section-kicker">
                <span className="section-kicker__line" />
                <span>The ALMASI journey</span>
              </div>
              <h2>
                Twelve weeks.
                <br />
                <span>So much room to grow.</span>
              </h2>
              <p>
                A guided mentorship journey designed to make space for
                reflection, new skills, meaningful conversations, and
                confidence that grows from within.
              </p>
              <p className="programme-section__note">
                The overview shares the programme at a high level. Facilitator
                resources and private learner information are not published
                here.
              </p>
            </div>
            <div className="journey-list">
              <article className="journey-step">
                <span className="journey-step__number">01</span>
                <div>
                  <span className="journey-step__weeks">WEEKS 1–4</span>
                  <h3>Discover your foundation</h3>
                  <p>
                    Begin with belonging, faith, self-understanding, and
                    noticing the strengths already within you.
                  </p>
                </div>
              </article>
              <article className="journey-step">
                <span className="journey-step__number">02</span>
                <div>
                  <span className="journey-step__weeks">WEEKS 5–8</span>
                  <h3>Build confidence and skills</h3>
                  <p>
                    Explore practical life skills, healthy choices, and ways
                    to express yourself with courage and care.
                  </p>
                </div>
              </article>
              <article className="journey-step">
                <span className="journey-step__number">03</span>
                <div>
                  <span className="journey-step__weeks">WEEKS 9–12</span>
                  <h3>Grow into what’s next</h3>
                  <p>
                    Reflect on how far you have come, celebrate progress, and
                    look ahead with hope and intention.
                  </p>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section className="benefits-section" id="benefits">
          <div className="container">
            <div className="benefits-section__heading">
              <div className="section-kicker">
                <span className="section-kicker__line" />
                <span>What you’ll find</span>
              </div>
              <h2>
                Growth that goes
                <br />
                <span>beyond the programme.</span>
              </h2>
            </div>
            <div className="benefit-grid">
              <article className="benefit-card">
                <span className="benefit-card__icon" aria-hidden="true">✧</span>
                <h3>Personal growth</h3>
                <p>Get to know your strengths, values, and the person you are becoming.</p>
              </article>
              <article className="benefit-card">
                <span className="benefit-card__icon" aria-hidden="true">♡</span>
                <h3>Guided reflection</h3>
                <p>Make room to think, ask questions, and connect faith with everyday life.</p>
              </article>
              <article className="benefit-card">
                <span className="benefit-card__icon" aria-hidden="true">✿</span>
                <h3>Practical activities</h3>
                <p>Explore useful skills and put new ideas into practice at your own pace.</p>
              </article>
              <article className="benefit-card">
                <span className="benefit-card__icon" aria-hidden="true">☼</span>
                <h3>Supportive mentorship</h3>
                <p>Be encouraged by caring guidance and a community that makes space for you.</p>
              </article>
              <article className="benefit-card">
                <span className="benefit-card__icon" aria-hidden="true">↗</span>
                <h3>Progress you can notice</h3>
                <p>Pause along the way to recognize your effort, learning, and growth.</p>
              </article>
            </div>
          </div>
        </section>

        <section className="closing-section" id="contact">
          <div className="container closing-section__inner">
            <div className="closing-section__copy">
              <span className="eyebrow">Your next chapter can start here</span>
              <h2>Ready to learn more about ALMASI?</h2>
              <p>Explore the programme or sign in to continue your journey.</p>
            </div>
            <div className="closing-section__actions">
              <a className="button button--primary" href="#programme">
                Learn about the programme
              </a>
              <Link className="button button--primary" to="/signup">
                Get Started
              </Link>
            </div>
          </div>
        </section>
        <section className="photo-cta-section">
          <img
            className="photo-cta-section__image"
            src="/almasi-mentorship.png"
            alt="Two women encouraging each other with a joyful high-five outdoors"
            loading="lazy"
          />
          <div className="photo-cta-section__overlay" />
          <div className="container photo-cta-section__content">
            <span className="eyebrow">You were made to grow</span>
            <h2>
              Your journey is yours.
              <br />
              <span>You don’t have to take it alone.</span>
            </h2>
            <p>
              Take a first step toward a more confident you, supported by faith,
              encouragement, and caring mentorship.
            </p>
            <Link className="button button--photo-cta" to="/signup">
              Begin your journey <span aria-hidden="true">→</span>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

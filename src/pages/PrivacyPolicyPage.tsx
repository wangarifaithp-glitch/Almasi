import { Link } from "react-router-dom";
import Brand from "../components/Brand";
import { getContactDestination } from "../lib/publicDestinations";

const contactUrl = getContactDestination(import.meta.env.VITE_CONTACT_URL);

export default function PrivacyPolicyPage() {
  return (
    <main className="legal-page">
      <div className="container legal-page__container">
        <Brand />
        <Link className="legal-page__back" to="/">
          ← Back to ALMASI
        </Link>
        <article className="legal-document">
          <span className="eyebrow">Your privacy matters</span>
          <h1>Privacy Policy</h1>
          <p className="legal-document__intro">
            This draft describes the information currently processed by the
            ALMASI website and learning platform. It is not legal advice or a
            statement that compliance with Kenyan data-protection law has been
            independently verified.
          </p>
          <div className="policy-confirmation" role="note">
            <strong>Before publication:</strong> ALMASI must confirm its legal
            organisation name and location, responsible privacy contact,
            service providers, storage region, retention periods, consent
            process, lawful basis, and the effective date of this policy.
          </div>

          <section>
            <h2>1. Information we may collect</h2>
            <p>
              The public website can be browsed without creating an account.
              When an account is created, the platform stores the learner’s
              name, email address, password hash, account role, active status,
              session version, and account timestamps. Public registration
              creates learner accounts only.
            </p>
            <p>
              The learning platform stores learner module answers, completion
              progress, private notes, private reflections, quiz answers and
              scores, and timestamps. If a learner belongs to a programme
              group, the platform may also store group membership, attendance,
              assignments, submissions, facilitator feedback, scores, and
              submission history.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> whether age, guardian, consent,
              safeguarding, contact, analytics, or device data is collected
              outside the fields currently implemented in this repository.
            </p>
          </section>

          <section>
            <h2>2. How information is used</h2>
            <p>
              Information is used to create and secure accounts, authenticate
              users, provide learner lessons, save learning activity and
              progress, support facilitator review, produce authorised
              programme reports, communicate password-reset links, protect
              learner privacy and safety, and maintain the security and
              operation of ALMASI services. It should not be used for unrelated
              purposes without an appropriate notice and, where required,
              permission.
            </p>
          </section>

          <section>
            <h2>3. Who may access information</h2>
            <p>
              Learners can access their own learning records. Facilitators can
              access records for groups assigned to them, including submissions
              requiring review. Supervisors can access authorised programme
              progress and reports. Administrators can use the administrative
              controls assigned to their role. Private learner notes and
              reflections are not included in staff reports. Information may
              also be disclosed when necessary to address a serious safety
              concern or comply with a valid legal requirement.
            </p>
            <p>
              Public programme pages do not display private learner records or
              facilitator-only materials.
            </p>
          </section>

          <section>
            <h2>4. Storage and security</h2>
            <p>
              The application uses role-based access controls, signed
              HTTP-only session cookies, secure production cookies, HTTPS
              deployment requirements, password hashing, database constraints,
              and audit records for selected programme actions. No online
              service can promise absolute security. Production credentials
              must be stored in managed secret configuration and never in the
              frontend or source repository.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> hosting and storage providers,
              storage locations, encryption and backup practices, and the
              organisation responsible for security.
            </p>
          </section>

          <section>
            <h2>5. Retention and deletion</h2>
            <p>
              The application currently has no automatic retention or deletion
              schedule. Records remain in the configured database until an
              authorised administrator or database operator removes them.
              Password-reset tokens have an application expiry period, but
              account, learning, programme, audit, and backup retention
              periods must be defined by ALMASI before production use.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> retention periods for account,
              learning, safeguarding, programme, audit, backup, and email
              records, plus the process for access, correction, export, and
              deletion requests.
            </p>
          </section>

          <section>
            <h2>6. Learners under 18 and guardian consent</h2>
            <p>
              ALMASI serves girls aged 12–16. Before collecting personal
              information from a learner or providing programme services,
              ALMASI must determine and follow the consent, guardian
              involvement, safeguarding, and age-appropriate notice
              requirements that apply where it operates. The current account
              form does not implement a guardian-consent workflow, so that
              workflow must be completed and reviewed before production
              registration of minors.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> operating locations, consent
              workflow, who verifies guardian authority, and how learner
              assent and safeguarding concerns are handled.
            </p>
          </section>

          <section>
            <h2>7. Your choices and privacy concerns</h2>
            <p>
              A learner or guardian may contact ALMASI to ask what information
              is held, request access, correction, export, deletion, or
              restriction where applicable, or raise a privacy concern.
              Requests may need to be verified to protect the learner’s
              information. ALMASI should respond through its confirmed
              privacy contact route and document the request-handling process.
            </p>
            <p>
              Contact:{" "}
              <a
                href={contactUrl}
                {...(contactUrl.startsWith("https://")
                  ? { target: "_blank", rel: "noreferrer" }
                  : {})}
              >
                Contact ALMASI about a privacy concern
              </a>
              .
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> publish a monitored privacy email or
              named contact person, escalation route, identity-verification
              process, and response timelines. Obtain Kenyan data-protection
              legal review before publication.
            </p>
          </section>

          <section>
            <h2>8. Changes to this policy</h2>
            <p>
              ALMASI should update this page when its practices change and
              identify when the updated policy takes effect. If a change
              materially affects learners or guardians, ALMASI should provide
              an appropriate notice.
            </p>
            <p className="policy-confirmation">
              <strong>Effective date:</strong> [ALMASI TO CONFIRM BEFORE
              PUBLICATION]
            </p>
          </section>
        </article>
      </div>
    </main>
  );
}

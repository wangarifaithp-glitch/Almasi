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
            This draft explains how ALMASI intends to handle information in
            connection with its website and mentorship programme. It is not a
            statement that legal compliance has been independently verified.
          </p>
          <div className="policy-confirmation" role="note">
            <strong>Before publication:</strong> ALMASI must confirm its legal
            organisation name and location, responsible privacy contact,
            service providers, storage region, retention periods, consent
            process, and the effective date of this policy.
          </div>

          <section>
            <h2>1. Information we may collect</h2>
            <p>
              The public website can be browsed without creating an account.
              If ALMASI later opens registration or programme services, it may
              need information such as a learner’s name, age range, contact
              details, guardian details and consent, and information needed to
              support safe participation. Only information needed for a stated
              purpose should be requested.
            </p>
            <p>
              Technical information such as browser type, device information,
              and basic server logs may be processed to operate and protect the
              website. ALMASI should confirm which analytics or logging tools
              are actually enabled before publication.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> exact data fields collected, whether
              analytics or cookies are used, and the responsible legal entity.
            </p>
          </section>

          <section>
            <h2>2. How information is used</h2>
            <p>
              Information may be used to respond to enquiries, administer
              participation, communicate programme updates, provide
              mentorship support, protect participant safety, and maintain the
              security and operation of ALMASI services. It should not be used
              for unrelated purposes without an appropriate notice and, where
              required, permission.
            </p>
          </section>

          <section>
            <h2>3. Who may access information</h2>
            <p>
              Access should be limited to authorised ALMASI personnel and
              service providers who need information for their assigned work.
              Information may also be disclosed when necessary to address a
              serious safety concern or comply with a valid legal requirement.
              ALMASI should document its access controls and any service
              providers before collecting learner information.
            </p>
            <p>
              Public programme pages do not display private learner records or
              facilitator-only materials.
            </p>
          </section>

          <section>
            <h2>4. Storage and security</h2>
            <p>
              ALMASI intends to use access controls and reasonable technical
              and organisational safeguards to protect information against
              loss, misuse, or unauthorised access. No online service can
              promise absolute security. Information should be stored only in
              approved systems with access limited to people who need it.
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
              Information should be kept only for as long as needed for the
              purpose it was collected, to support programme administration,
              address safety needs, or meet applicable recordkeeping
              requirements. When it is no longer needed, ALMASI should securely
              delete it or remove identifying details.
            </p>
            <p className="policy-confirmation">
              <strong>To confirm:</strong> retention periods for enquiries,
              learner and guardian records, programme notes, and technical
              logs, plus the process for deletion requests.
            </p>
          </section>

          <section>
            <h2>6. Learners under 18 and guardian consent</h2>
            <p>
              ALMASI serves girls aged 12–16. Before collecting personal
              information from a learner or providing programme services,
              ALMASI must determine and follow the consent, guardian
              involvement, safeguarding, and age-appropriate notice
              requirements that apply where it operates. A learner’s
              participation should be explained in clear, age-appropriate
              language, with a suitable way for the learner and guardian to ask
              questions or raise concerns.
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
              is held, request a correction or deletion, or raise a privacy
              concern. Requests may need to be verified to protect the
              learner’s information. ALMASI should respond through its
              confirmed privacy contact route.
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
              named contact person and the expected response process.
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

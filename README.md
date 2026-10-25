# ALMASI

ALMASI is a faith-centered mentorship platform for girls aged 12–16, with the
theme **“Refined in Faith, Growing in Confidence.”** This repository includes
a responsive public landing page, login and sign-up screens, password recovery
by email, and a small authenticated API foundation. The learner workspace
serves only published curriculum modules. The supplied ALMASI teaching manual
has been adapted into 12 learner-facing drafts. All modules remain unpublished
until an authorised supervisor reviews and publishes them.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/          # Versioned REST routes
│   │   ├── core/         # Environment-backed settings
│   │   ├── db/           # SQLAlchemy base, engine, session dependency
│   │   ├── models/       # Account, curriculum, and learner-data models
│   │   └── schemas/      # Validated API request/response schemas
│   ├── migrations/       # Alembic database migrations
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── .env.example
└── src/                  # React + TypeScript frontend
```

## Run locally

### Frontend

Requirements: Node.js 20.19+ or 22.12+ and npm.

```sh
npm install
npm run dev
```

The development server is available at `http://localhost:5173`. The Vite
development proxy forwards `/api/v1` requests to `http://127.0.0.1:8000`, so
the browser uses a same-origin API path and the backend must be running.
`frontend/.env.example` is the template for `frontend/.env.local`; set
`VITE_API_BASE_URL` there only when using a different API origin. Vite embeds
this value at build time, so production builds must be rebuilt after changing
it.

### Backend

Requirements: Python 3.10 or newer and a reachable MySQL database.

```sh
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Create a local config only if one does not already exist.
# Windows PowerShell: if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# macOS/Linux: [ -f .env ] || cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"  # Use output for AUTH_SECRET_KEY
# Configure RESEND_API_KEY and a verified RESEND_FROM_EMAIL in .env.
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Before starting the API, set `DATABASE_URL` in `backend/.env` to a reachable
MySQL database, set `AUTH_SECRET_KEY` to a newly generated value of at least
32 bytes, and configure the email values if password reset email is needed.
The backend resolves its `.env` file relative to `backend/app/core/config.py`,
so launching Uvicorn or Alembic from another working directory does not select
a different `.env`. Process environment variables take precedence over values
in `.env`; remove or correct a stale `DATABASE_URL` environment variable if it
is set. Create the database if it does not exist yet. Run the migration command
before starting the API. The API health endpoint
(`http://localhost:8000/api/v1/health`) checks both database connectivity and
that all application tables exist; it returns HTTP 503 with a safe explanation
if MySQL is unreachable, rejects the account, or migrations are missing. A
MySQL 1045 error means MySQL denied the account; it does not distinguish a
wrong password from a mismatched account host or missing database privileges.
The app does not print the connection URL or credentials in its database
diagnostics. Interactive API documentation is at
`http://localhost:8000/docs`.

The checked-in `backend/.env.example` contains only placeholders. Copy it to
`backend/.env`, then supply a dedicated database name, a dedicated MySQL
account, and that account's URL-encoded password. Never commit `.env` or put
database credentials in frontend `VITE_*` variables. If you manage MySQL
yourself, connect as a MySQL administrator and substitute the actual backend
host and a newly chosen secret in these commands; do not run them for an
existing account whose password you do not intend to change:

```sql
CREATE DATABASE IF NOT EXISTS almasi
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'almasi_app'@'<BACKEND_HOST>'
  IDENTIFIED BY '<NEW_UNIQUE_PASSWORD>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON almasi.* TO 'almasi_app'@'<BACKEND_HOST>';
SHOW GRANTS FOR 'almasi_app'@'<BACKEND_HOST>';
```

If the account already exists, ask the database administrator to verify the
matching `user@host`, its current credentials, and grants instead of resetting
or overwriting its password. Database migrations need the DDL privileges
listed above; runtime-only deployments can separate the migration account
from the app account and give the runtime account only data access. Apply
migrations with `python -m alembic upgrade head` from `backend/`.

On Windows PowerShell, run the frontend and backend in separate terminals:

```powershell
# Terminal 1: project root
if (-not (Test-Path frontend\.env.local)) { Copy-Item frontend\.env.example frontend\.env.local }
npm.cmd install
npm.cmd run dev
```

```powershell
# Terminal 2: project root
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env with DATABASE_URL and AUTH_SECRET_KEY before continuing.
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Verify `http://localhost:8000/api/v1/health` reports
`{"status":"ok","database":"ok"}` before trying registration or sign-in. The
12 curriculum modules are seeded as unpublished drafts. A trusted supervisor
must review and publish each module before it appears in the learner module
list.
Registration (`POST /api/v1/auth/register`), login
(`POST /api/v1/auth/login`), and current-user (`GET /api/v1/auth/me`) all use
JSON and an HttpOnly session cookie. The frontend sends credentialed requests;
do not replace the cookie with a browser-stored password or token. For a
production frontend and backend on separate origins, set `VITE_API_BASE_URL`
to the full HTTPS API base URL ending in `/api/v1`, and set backend
`CORS_ORIGINS` to the exact HTTPS frontend origin(s), without a trailing slash.

## Environment variables

Backend settings are read from the process environment or `backend/.env`:

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | FastAPI title shown in API documentation. |
| `APP_ENV` | Environment label, such as `development` or `production`. |
| `API_V1_PREFIX` | Versioned REST API prefix; defaults to `/api/v1`. |
| `DATABASE_URL` | SQLAlchemy MySQL URL, including the private database credentials. |
| `CORS_ORIGINS` | Comma-separated list of exact frontend origins allowed to call the API. |
| `AUTH_SECRET_KEY` | A random private key used to sign the HttpOnly session cookie. |
| `APP_BASE_URL` | Frontend origin used to construct password-reset links. |
| `RESEND_API_KEY` | Private Resend API key used to send password-reset emails. |
| `RESEND_FROM_EMAIL` | Sender address on a domain verified with Resend. |

Frontend settings use Vite's `VITE_` prefix. `VITE_API_BASE_URL` is the
non-secret base URL for API calls. Optional public destinations are
`VITE_CONTACT_URL`, `VITE_DEVELOPER_URL`, `VITE_INSTAGRAM_URL`,
`VITE_FACEBOOK_URL`, `VITE_TIKTOK_URL`, and `VITE_YOUTUBE_URL`. Configure these
only with destinations ALMASI has confirmed; unconfigured social accounts are
shown as placeholders, not links. Without a contact URL, contact actions use
the public landing-page contact section. Without a developer portfolio URL,
the Developer page explains that no portfolio has been configured.

Only public configuration belongs in the frontend; never put database
credentials, API secrets, or private keys in `VITE_*` variables because they
are included in the browser bundle. The privacy policy page is an editable
draft: resolve each ALMASI confirmation marker before treating the policy as
final or publishing it as legal advice.

### Authentication

New accounts require a password of 8–128 characters containing uppercase and
lowercase letters, a number, and a special character. Passwords are stored as
Argon2 hashes. Password reset links are sent through Resend, expire after 30
minutes, can only be used once, and are limited to one email per account per
minute. Configure a verified Resend sender, a private `AUTH_SECRET_KEY`, and
the production frontend origin before enabling account access.

Sign-up always creates a learner account; role values submitted by the browser
are ignored. Facilitator and supervisor roles must be assigned through a
trusted database administration process. The API separately authorizes each
workspace endpoint. Authentication tests use an isolated SQLite database and
mock Resend delivery:

```powershell
cd backend
$env:DATABASE_URL = "sqlite://"
python -m unittest discover -s tests -v
```

### Learner curriculum and private data

The API stores curriculum modules, ordered questions, learner notes,
reflections, question answers, submissions, and completion timestamps in
MySQL. Run `python -m alembic upgrade head` after configuring `DATABASE_URL`
to apply the schema and seed 12 unpublished modules from the supplied manual.
The learner-facing lesson text is adapted from its explanations; session
schedules, facilitator directions, attendance, and facilitator-only reports
are excluded. Objectives, reflection prompts, fictional case-study questions,
and take-home assignments are also included. A module remains unavailable to
learners until a supervisor reviews and publishes it.

Learner endpoints require a learner session and return only published modules:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/learner/modules` | Published modules and the signed-in learner's completion status. |
| `GET` | `/api/v1/learner/modules/{id}` | Objectives, lesson, questions, and that learner's own notes, reflection, and submitted answers. |
| `PUT` | `/api/v1/learner/modules/{id}/notes` | Create or update the learner's private module note. |
| `PUT` | `/api/v1/learner/modules/{id}/reflections` | Create or update the learner's private module reflection. |
| `PUT` | `/api/v1/learner/modules/{id}/answers` | Save or update private answer drafts without marking the module complete. |
| `POST` | `/api/v1/learner/modules/{id}/submit` | Submit one answer for every question and mark the module complete. |

Every learner-data query is scoped to the authenticated learner. Notes and
reflections are never returned by supervisor or facilitator APIs; there is no
staff read endpoint for this private content. Case-study answers and
assignments are saved as drafts and can be resumed; submission is rejected
unless the learner answers every required prompt. A draft answer is not counted
as progress, and a completed module cannot be submitted a second time.
Supervisor-only curriculum endpoints are `GET /api/v1/supervisor/modules` to
review drafts and published records, `POST /api/v1/supervisor/modules` to
create a draft, `PUT /api/v1/supervisor/modules/{id}` to update an unpublished
draft, `POST /api/v1/supervisor/modules/{id}/review` to record review, and
`POST /api/v1/supervisor/modules/{id}/publish` to publish it. Editing a draft
clears its review status. Review requires lesson content, nonblank objectives
and reflection prompts, at least one case-study question, one assignment, and
explicit supervisor confirmation. Publishing requires a recorded review.
Learner notes and reflections use MySQL `MEDIUMTEXT` storage, with length
constraints sized for the UTF-8 representation of the application limits.
Supervisor accounts must be assigned through a trusted database administration
process; public sign-up cannot grant this role.

The learner interface loads modules from these APIs and clearly reports
loading, service errors, empty/unpublished curriculum, save status, and
submission confirmation. A successful save or completion is shown only after
the API confirms the database write. Private reflections are currently
accessible only to their owner; no safeguarding-role access endpoint exists.
Avoid collecting names, contact details, locations, or personal safety-plan
details in learner answers. These endpoints and migrations are covered by
isolated SQLite automated tests, which verify API behaviour and learner data
ownership; those tests do not prove connectivity to a deployed MySQL service.
Before using this feature with learners, configure the real MySQL connection,
run migrations, and have a trusted supervisor review and publish the drafts.

### Programme workspaces

Facilitators use `GET /api/v1/facilitator/dashboard` for their assigned groups,
session plans, assignments, submissions, and reports. They can create
assignments, record attendance, update session status, provide feedback, lock
submissions, and submit session reports through the facilitator routes. Each
operation is restricted to an actively assigned group and recorded where
appropriate in the audit log.

Supervisors use `GET /api/v1/supervisor/reports` for programme progress,
attendance, and completion summaries, and
`GET /api/v1/supervisor/reports/export` to download an audited CSV report.
Neither facilitator nor supervisor responses include learner notes or private
reflections. Supervisors may separately review/publish curriculum through the
curriculum endpoints described above.

Administrators use `/api/v1/administrator` to manage accounts and active
roles, create groups and sessions, and assign facilitators and learners.
Administrator access must be bootstrapped through a trusted database
administration process; public sign-up cannot grant staff roles. Changing a
role or removing a group member preserves the assignment history while
revoking future access/submission rights.

The dashboards call the live API and show loading, success, and API error
states; they do not show a successful save when a request fails. The included
automated tests use an isolated SQLite database (and mock only outbound email
delivery); they do not claim production MySQL or Resend connectivity. The
actual MySQL connection must be verified independently using the health
endpoint before deploying or accepting registrations.

For local development, copy `backend/.env.example` to `backend/.env` and
`frontend/.env.example` to `frontend/.env.local`. The frontend defaults to
`/api/v1` and the Vite development proxy; set `VITE_API_BASE_URL` to an
absolute URL only for a separately hosted API. Environment files containing
real values are ignored by Git.

## Deployment

- **Frontend (Vercel):** deploy the repository root as a Vite application.
  Configure the build command as `npm run build` and output directory as
  `dist`. The included SPA rewrite keeps client-side routes working on direct
  visits and refreshes. Set the Vercel build environment variable
  `VITE_API_BASE_URL` to the deployed API's public HTTPS base URL ending in
  `/api/v1` (or use `/api/v1` if the same-origin reverse proxy forwards that
  path to the backend). The Vite development proxy is not used in production.
- **Backend:** deploy `backend/` to a Python ASGI-compatible host, install
  `backend/requirements.txt`, and run `uvicorn app.main:app --host 0.0.0.0
  --port $PORT` (adapt the port syntax to the host). Configure `DATABASE_URL`,
  `CORS_ORIGINS`, `AUTH_SECRET_KEY`, `APP_ENV=production`, `APP_BASE_URL`,
  `RESEND_API_KEY`, and `RESEND_FROM_EMAIL` as host-managed environment
  variables. Set the platform's working directory to `backend` so settings
  and Alembic load the correct files. Apply `python -m alembic upgrade head`
  as a release/deploy step before routing account traffic, then verify the
  public `/api/v1/health` endpoint returns HTTP 200.
- **MySQL:** use a managed MySQL service with TLS/network restrictions and
  least-privilege database credentials. Store its connection string only in
  the backend host's secret environment configuration. Allow the backend host
  to connect, not arbitrary public clients.

Before production, configure exact production origins, enable TLS on both
services, provision and rotate secrets through the hosting providers, and run
`python -m alembic upgrade head` for schema changes. Account passwords are
Argon2-hashed; reset links expire after 30 minutes and can only be used once.
Production session cookies are marked Secure and HttpOnly.

The public website includes a draft privacy policy at `/privacy-policy`.
Confirm its organisation-specific markers before publication. The footer and
floating actions use optional `VITE_*_URL` values documented above; unconfigured
social destinations are displayed as placeholders rather than working links.

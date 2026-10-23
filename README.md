# DoppleJa V1

**Two sides. Two Yes. One Match.**
*Zwei Seiten. Zwei Ja. Ein Match.*

DoppleJa is a mobile-first, swipe-based job-matching platform connecting local workers with private individuals and businesses in Germany.

**No CVs. No traditional applications.** Workers and employers discover suitable opportunities or candidates, indicate interest with a Like or Pass, and can chat directly after a **mutual Like creates a Match**.

> **Project status:** Active development (V1). The app is functional for local development and testing, but is **not yet production-ready**. The current demo data and generated portraits are illustrative, not actual job offers or users.

## What works today

- **Accounts and access:** Worker and employer roles; registration, email verification on the backend, login, logout, and cookie-based sessions.
- **Profiles:** Editable worker and employer profiles. Employers can represent a private individual or a business.
- **Jobs:** Job creation, discovery, editing, pausing/reactivating, archiving, and employer job management.
- **Matching:** Both sides can Like or Pass; mutual Likes create Matches.
- **Saved Likes:** Workers can view pending, matched, and unavailable liked jobs.
- **Chat:** Match-only conversations, persisted messages, and real-time WebSocket messaging.
- **Frontend:** Responsive, mobile-first interface with violet/yellow DoppleJa branding, champagne/glass styling, and illustrative job and profile imagery.
- **Testing:** Automated backend/frontend checks and a GitHub Actions workflow.
- **Demo environment:** Repeatable seed data for 50 employers, 100 workers, 100 job listings, 25 matches, and 54 messages.

**Visual conventions:** ♥ means interest/Like; 🤝 means a confirmed Match; 💬 means conversation. AI-generated portraits and sample profiles must be clearly identified as **demo/illustrative**.

## Technology stack

| Layer | Technology |
| --- | --- |
| API | Python 3.12, FastAPI |
| Database | PostgreSQL 16, PostGIS |
| ORM / migrations | SQLAlchemy, Alembic |
| Cache / supporting services | Redis |
| Frontend | HTML, CSS, vanilla JavaScript |
| Real-time messaging | WebSockets |
| Local infrastructure | Docker Compose |
| CI | GitHub Actions |
| Planned deployment | Nginx / VPS (not yet a completed production deployment) |

## Repository layout

```text
DoppleJa_V1/
├── backend/                 # FastAPI application, models, routers
├── frontend/                # Mobile-first web app, styles, assets
├── infrastructure/          # Infrastructure configuration
├── scripts/                 # Development utilities and demo seed
│   └── seed_demo.py
├── tests/                   # Automated tests
├── docs/
│   └── development-history/ # Archived phase documentation
├── alembic.ini              # Alembic configuration
├── compose.yaml             # Docker Compose services
└── README.md
```

## Requirements

- Git
- Docker Desktop with Docker Compose
- A code editor (e.g., VS Code)
- Python 3.12 is useful for direct local tooling; the API itself can run in Docker.

Do not commit `.env` secrets, credentials, private keys, or local database files.

## Quick start: local development

1. Clone the repository and switch to the shared development branch:

   ```bash
   git clone git@github.com:javahedi/DoppleJa_V1.git
   cd DoppleJa_V1
   git switch develop
   ```

   SSH access requires configuring your own GitHub SSH key. Alternatively, use GitHub's HTTPS clone URL.

2. Review `compose.yaml` and any required local environment configuration. If a sample environment file is provided, copy it and set **local-only** values. Never reuse another developer's credentials.

3. Start the containers:

   ```bash
   docker compose up -d --build
   ```

4. Apply database migrations:

   ```bash
   docker compose exec api alembic upgrade head
   ```

5. Open the frontend and API documentation (assuming the project's usual port mapping):

   - App: <http://127.0.0.1:8001/>
   - API docs: <http://127.0.0.1:8001/docs>
   - Health: <http://127.0.0.1:8001/api/health>

If startup fails, inspect `docker compose ps` and `docker compose logs api --tail=100`. Database configuration and exposed ports must match your local Compose setup.

## Automated tests

The project uses a separate test database. In the established local setup:

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test api \
  python -m pytest tests/ -v --tb=short
```

To check frontend JavaScript syntax:

```bash
node --check frontend/js/app.js
```

Always use the **test** database for automated tests, not the main development or demo database. Passing automated tests does not replace browser testing on mobile widths (e.g., 375px and 425px).

## Demo data — local testing only

A **separate** `doppleja_v1_demo` database is used to demonstrate full Discovery and Match experiences without altering normal development data.

| Sample records | Count |
| --- | ---: |
| Employers | 50 |
| Workers | 100 |
| Jobs | 100 |
| Matches | 25 |
| Messages | 54 |

The corrected and repeatable seeding script is `scripts/seed_demo.py`. The demo database must be migrated before seeding. **Check the script's database-name guard and Docker paths before executing it.** Never point the seeder at a production or shared live database.

Example demo account (only after seeding the demo database):

- Worker: `worker001@example.com`
- Employer: `employer01@example.com`
- Local demo password: `Demo2026!`

These credentials are intentionally public test credentials: **never use them outside an isolated local demo environment**. Do not expose the demo server on a public network. Existing local demo data does not automatically sync through GitHub.

**Note:** The demo seed script may not be included in the currently built API container. Verify that it is accessible in the container, or use a deliberate local developer workflow, before running it. Avoid assuming `/code/scripts/seed_demo.py` is mounted by default.

## Product workflow

1. A worker or employer registers and verifies their email.
2. Each completes a relevant profile.
3. Employers publish jobs; workers discover available listings.
4. Workers and employers Like or Pass relevant opportunities/candidates.
5. A **mutual Like** creates a Match.
6. Matched users can communicate through chat.

Only legitimate, active, eligible listings and accounts should appear in production discovery. Demo listings and generated worker portraits must not masquerade as real people or real vacancies.

## Team collaboration and governance

**Project owner:** `javahedi` — **sole final decision-maker for acceptance into the shared branches**.

- `main`: stable release branch.
- `develop`: shared integration branch.
- `feature/*`: isolated feature work.
- `fix/*`: isolated bug-fix work.

**All contributors must work on their own feature branches and submit pull requests targeting `develop`. No colleague may merge or push directly to `develop` or `main` without the project owner's explicit approval.** This is a team policy; the repository owner must also configure appropriate GitHub branch/ruleset permissions and verify that technical controls enforce it. Repository plan and visibility can affect the available enforcement options.

Typical developer workflow:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/short-description

# Make the change and run relevant tests.
git add <specific-files>
git commit -m "feat: short description"
git push -u origin feature/short-description
```

Then open a **pull request** from the feature branch into `develop`. The project owner reviews the diff, test results, screenshots (for UI changes), security implications, and GitHub Actions checks before deciding whether to merge.

**Do not:** force-push shared branches, run destructive database commands without approval, commit credentials, or use `git add .` without inspecting what will be staged.

The full onboarding and team rules are documented separately in the **DoppleJa Team Collaboration Handbook**; share that document with every contributor before granting write access.

## Current development priorities

- Continue aligning the UI with the original **13-screen DoppleJa design showcase**.
- Complete the user-facing email verification and onboarding experience.
- Refine photo-based Discovery, job filters, and employer candidate cards.
- Polish Match celebration, match summaries, and real-time chat screens.
- Improve demo-data development workflow and container packaging.
- Design a verified completed-job workflow before introducing mutual star reviews.
- Prepare production security, privacy, monitoring, backups, and deployment checks.

## Project principles

- **Simple:** No mandatory CV or traditional application flow.
- **Mutual:** Both sides choose before private conversation begins.
- **Mobile-first:** Fast, accessible flows designed primarily for phones.
- **Trustworthy:** Keep real identities and jobs distinct from demo content.
- **Controlled releases:** Contributors propose changes; the project owner makes the final merge decision.

---

**DoppleJa — Zwei Seiten. Zwei Ja. Ein Match.**

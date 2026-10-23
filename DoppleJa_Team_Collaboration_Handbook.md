# DoppleJa V1 — Team Collaboration & GitHub Handbook

**Version:** 1.0 · **Date:** 23 October 2026
**Repository:** https://github.com/javahedi/DoppleJa_V1
**Project owner and final release/merge decision-maker:** Repository owner (`javahedi`)
**Applies to:** Every developer, contributor, designer, tester, and contractor granted access.

> **Non-negotiable:** Contributors may develop code and push to their own feature branches. They must **never** push directly to `develop` or `main`, merge pull requests, force-push shared branches, or deploy changes without the owner's explicit approval. The owner alone decides whether work is accepted. GitHub permissions and branch rules must be configured to enforce this where supported. Written rules alone do not prevent accidental merges.

## 1. Understand the project before touching it

DoppleJa V1 is a two-sided job-matching app with a mobile-first frontend (HTML/CSS/vanilla JavaScript), FastAPI backend, PostgreSQL/PostGIS database, Docker Compose development environment, Alembic migrations, authentication/email verification, worker and employer profiles, jobs, Like/Pass swipe matching, mutual matches, and REST/WebSocket chat. GitHub Actions runs project CI. The design uses violet/yellow branding and champagne-glass screens; **♥ = Like, 🤝 = confirmed Match**.

Current branches: `main` = stable baseline; `develop` = tested integration; `feature/...` = individual work; `fix/...` = targeted bugs. Current seeded demo data: 50 employers, 100 workers, 100 job postings, 25 matches, 54 messages in a separate `doppleja_v1_demo` database. **Demo profiles, photos and jobs are fictional** and must not be shown as genuine public listings.

Every developer uses a **separate local clone and separate local PostgreSQL database**. Cloning code does *not* clone data, local `.env` files, Docker volumes, or running containers.

## 2. Owner ONLY — invite a colleague

1. Ask for the colleague's GitHub username. Never ask for their password or SSH private key.
2. Sign into GitHub as the repository owner. Visit https://github.com/javahedi/DoppleJa_V1.
3. Open **Settings → Collaborators** (usually under Access) → **Add people**.
4. Enter the exact GitHub username, choose the correct account, and send the invitation.
5. The colleague accepts the GitHub invitation using their own account.
6. **Before they start:** complete section 3 (protect branches). Do not assume collaborator access automatically limits merges.
7. Tell the colleague their assigned feature, expected changes, and that only the owner may accept or merge their pull request.

If the repository is transferred to a GitHub organization, set colleagues to an appropriately restricted role and retain admin/merge authority for the owner. Review repository-level access and the branch rules whenever team membership changes.

## 3. Owner ONLY — enforce the final decision on GitHub

**Critical GitHub limitation:** On a personal-account repository, collaborators can have write access; without effective protection they may be able to push or merge. A rule that requires **one approval** does not necessarily require approval from *this specific owner*. Also, private-repository branch protections/rulesets depend on GitHub plan and repository ownership. Check the controls actually available before relying on them.

Preferred owner setup (where available):

1. Open repository **Settings → Rules → Rulesets** (or **Settings → Branches → Add branch protection rule**, depending on GitHub UI).
2. Create/enforce rules applying separately to **`develop`** and **`main`**; ensure their status is **Active**, not merely Evaluate.
3. Require a pull request before merging; require at least one approving review; dismiss stale approvals after new commits; require all conversations resolved.
4. Require the relevant GitHub Actions status checks to pass. Choose the **actual workflow/job check names** from successful runs; do not guess names.
5. Block force pushes and branch deletion. Prevent direct pushes to the protected branches.
6. **Owner-only control:** Configure restrictions/bypass/allowed push or merge actors where available so that ONLY the owner can update the protected branches, and verify a non-owner cannot merge. Carefully distinguish “can approve” from “can merge.” Do not give colleagues bypass or admin rights.
7. If supported, define `.github/CODEOWNERS` with `* @javahedi` and require code-owner review. **Important:** CODEOWNERS is a review gate, not by itself an absolute restriction on who clicks Merge; use permissions/restrictions as well.
8. Check protections for `main` too; main should receive changes only by an owner-approved release PR from `develop`.
9. Perform a safe permission test with a small PR: colleague opens PR; confirm they cannot directly push to or merge into either protected branch, and you can complete the approved merge. Only then treat the restriction as enforced.

**If these safeguards are unavailable for your plan/private personal repository:** do not claim technical enforcement. Keep the “no merges without owner” policy as an interim team agreement and consider GitHub Pro or an organization with appropriate Team/Enterprise access controls, permissions and rulesets. Never make a private repository public only to get branch protection unless the owner explicitly intends public source code.

Official GitHub reference links:
- Invite collaborators: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository
- Protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

## 4. Colleague — install development tools

1. Create or sign into your **own** GitHub account and accept the repository invitation.
2. Install Git and Docker Desktop. On a Mac, install a terminal and a code editor (e.g. VS Code). On Windows use a compatible Docker/WSL environment; confirm path and command differences before starting.
3. Verify tools:

```bash
git --version
docker --version
docker compose version
```

4. Configure your own Git identity (substitute your real identity and your GitHub-associated address):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@yourdomain.example"
```

5. Set up your own GitHub SSH key **or** use an HTTPS clone with Git Credential Manager. SSH keys are per developer and must never be copied from the owner's computer. Follow https://docs.github.com/en/authentication/connecting-to-github-with-ssh . For SSH, test: `ssh -T git@github.com`.

## 5. Colleague — clone the correct branch

Choose ONE clone method:

```bash
# SSH (requires your own GitHub SSH key):
git clone git@github.com:javahedi/DoppleJa_V1.git
# OR HTTPS:
# git clone https://github.com/javahedi/DoppleJa_V1.git

cd DoppleJa_V1
git fetch origin
git switch develop
git pull --ff-only origin develop
git status
```

Expected: on branch `develop`, up to date, clean working tree. If access is denied, check invitation acceptance and your own GitHub authentication. Never use the owner's credentials.

## 6. Colleague — start local Docker (no production credentials)

1. Read `README.md`, `compose.yaml` and `alembic.ini` before editing them. Environment variables and port bindings may differ by machine.
2. Create local environment/config values only using a documented example (if one exists). Never commit `.env`, access tokens, private keys, database dumps or personal data.
3. Start the local stack:

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=80 api
```

4. Initialize/apply database migrations **in your own local database**:

```bash
docker compose exec api alembic upgrade head
```

5. Open the application and API using the ports set in `compose.yaml`. The owner's configuration used `http://127.0.0.1:8001/` and `/docs`; these addresses are local to **your** computer.
6. Never run `docker compose down -v`, `DROP DATABASE`, `alembic downgrade`, or destructive reset commands without an owner-approved reason and a confirmed backup.

### Optional: isolated demo database

The repository tracks `scripts/seed_demo.py`, but **its path inside the container depends on `compose.yaml` mounts or the image build**. First verify it is available:

```bash
docker compose exec api ls -l /code/scripts/seed_demo.py
```

If unavailable, **copy your checked-in script to the container** (temporary development method):

```bash
docker compose cp scripts/seed_demo.py api:/code/seed_demo.py
```

Only on your own local development DB, create the isolated demo DB:

```bash
docker compose exec db sh -lc 'createdb -U "$POSTGRES_USER" doppleja_v1_demo'
```

If it says the database already exists, don't re-create or erase it. Then run:

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_demo api alembic upgrade head
# If script was copied as /code/seed_demo.py:
docker compose exec -e POSTGRES_DB=doppleja_v1_demo api python /code/seed_demo.py
```

Demo credentials for local testing only: `worker001@example.com` or `employer01@example.com`, password `Demo2026!`. These are shared **fictional test credentials**, never production logins. Do **not** launch this database on a public server or expose the same demo password publicly. The demo database is local and separate; other developers' Likes and chats do not sync.

## 7. One issue = one feature branch

**Never edit or push directly to `develop` or `main`.** Start from fresh `develop`:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/discovery-photo-cards
```

Use meaningful branch names, e.g. `feature/email-verification-screen`, `feature/worker-profile`, `fix/discovery-filter`, `docs/setup-guide`. Keep changes scoped to the assigned issue; do not reformat or rewrite unrelated files.

Before coding, record what you plan to change, which files, how to test it, and any expected schema/API changes. Consult the owner before database migrations, breaking endpoint changes, auth/security modifications, deployment changes or dependency upgrades.

## 8. Daily workflow and tests

Start each workday:

```bash
git status
git branch --show-current
git fetch origin
```

Work only on your feature branch. Keep changes small. Before submitting:

```bash
node --check frontend/js/app.js

docker compose exec -e POSTGRES_DB=doppleja_v1_test api \
  python -m pytest tests/ -v --tb=short

git diff --check
git status --short
```

**Test-database note:** the `doppleja_v1_test` test database and schema must already be provisioned according to project setup. If it is missing, do not substitute the normal or demo database. Ask the owner for the test DB initialization procedure.

Manual browser checks are required for visual changes: mobile widths 375px and 425px; worker and employer accounts; Like/Pass, Matches, Chats, jobs and verification as applicable. Check browser console, broken images, dropdown legibility and layout obscured by fixed navigation. All user-uploaded/generated profile illustrations must be labeled as demo/symbolic where appropriate.

Before committing, carefully inspect changed files and secrets:

```bash
git diff --stat
git diff
git diff --check
```

Stage **only intended files** (avoid unreviewed `git add .`):

```bash
git add frontend/js/app.js frontend/css/styles.css
# Replace with the specific files you actually changed.
git diff --cached --check
git diff --cached --stat
git commit -m "feat: improve discovery card layout"
git push -u origin feature/discovery-photo-cards
```

Commit/push your branch **is allowed**; pushing does not mean the changes are accepted or released.

## 9. Open a Pull Request (PR) — do not merge it

1. Open https://github.com/javahedi/DoppleJa_V1/pulls.
2. Click **New pull request** or **Compare & pull request** after pushing.
3. Set **base = `develop`**; compare = **your feature branch**. Never target `main` for routine features.
4. Use a clear PR title and complete the template below.
5. Request review from **`@javahedi`**. Send the PR link to the owner.
6. Wait for GitHub Actions. Fix failures on the same feature branch and push again; checks will run again.
7. If the owner requests changes, make them on the same branch, explain the fix and request review again.
8. **Do NOT click Merge, Squash and merge, Rebase and merge, bypass checks, or close another person's PR.** Only the owner decides acceptance and merging.

### Copy-and-paste PR template

```text
Title: feat: <specific change>

Goal / issue:
What changed:
What files and endpoints are affected:
Screenshots / short demo video (before and after):
Automated test command + result:
Manual test scenarios + result:
Database migration? YES / NO
New dependency or environment variable? YES / NO
Security/privacy impact:
Known limitations / follow-up work:

Owner review required: @javahedi
This PR is NOT approved for merging until the owner explicitly approves.
```

## 10. Owner ONLY — PR review and acceptance checklist

Use this checklist on **every** PR:

- [ ] Task was approved and matches the agreed scope.
- [ ] PR targets `develop`, not `main`.
- [ ] Code diff is understandable; no unrelated rewrites.
- [ ] No private keys, credentials, customer information or unnecessary generated files.
- [ ] GitHub Actions/checks are green; tests run against an isolated test DB.
- [ ] UI changes tested at 375px and 425px; no regression in existing flows.
- [ ] API, database migrations and data-handling changes were explicitly reviewed.
- [ ] Demo vs. real identities/jobs are clearly separated.
- [ ] Any conflict is resolved and reviewed again after the last push.
- [ ] Owner explicitly chooses **Approve** or **Request changes**.
- [ ] Only after owner's acceptance, owner selects the approved merge method (prefer **Squash and merge** for small features) and merges.
- [ ] Owner verifies the `develop` CI run after merge; `main` stays untouched until a separate release decision.

**Warning:** Merely requesting the owner's review does not technically stop someone else from merging. Verify section 3 enforcement.

## 11. After the owner merges — update both local clones

The owner announces that the PR is merged. Each developer runs:

```bash
git switch develop
git pull --ff-only origin develop
```

Do this before opening a new feature branch. Do not delete branches until any unfinished work is safely retained. To delete a completed local feature branch after confirming it merged:

```bash
git branch -d feature/discovery-photo-cards
```

The owner may remove the remote branch after merge. A merge to `develop` is **not a production release**.

## 12. Handling conflicts and mistakes safely

**Merge conflict:** stop, save your uncommitted work safely, inspect status, fetch the latest `develop`, rebase or merge only with understanding, resolve conflicts, rerun tests and push your feature branch. If unsure, send the owner `git status`, affected filenames, and the error. Never force-push shared branches.

**Accidentally edited `develop` but have NOT committed:** stop, do not push. Ask the owner before moving work to a new branch. If changes are valuable, creating a branch from the current state may preserve them; do not blindly discard with `git reset --hard`.

**Accidentally committed to `develop` locally:** do not push. Preserve the commit in a new feature branch and ask the owner for the safest correction. Never rewrite a remote shared branch yourself.

**Failed tests or Docker error:** paste the exact command and full relevant error. Do not disable tests, weaken FK constraints, drop databases, or fabricate results to get a green check.

**Secret committed or leaked:** notify the owner immediately, rotate/revoke the credential and follow an approved cleanup procedure; deleting it from the latest commit is not sufficient.

## 13. Team ownership, communications and release policy

**Owner (`javahedi`)**: selects priorities; assigns tasks; approves breaking changes; has final decision over PR acceptance/merge, GitHub access, deployments and releases. **Contributor**: implements assigned scoped tasks, writes tests, runs checks, opens PR, responds to feedback. **No contributor approval is a substitute for owner approval.**

For each task keep a short written record: issue/goal, owner of task, branch name, estimate of affected components, screenshots, test evidence, PR link, and decision. Prefer one PR per coherent feature rather than mixing unrelated work.

`main` is updated only with a **separate owner-approved release PR** when `develop` has been tested as a complete release. Production secrets, deployment configuration and live customer data are owner-managed and are never copied to contributors' laptops without explicit authorization and security review.

## 14. Mandatory checklist for a new collaborator

- [ ] I accepted the GitHub invitation under my own account.
- [ ] I have my own Git and GitHub authentication; I do not use shared credentials.
- [ ] I cloned the repository and checked out `develop`.
- [ ] My local Docker app and migrations work.
- [ ] I understand that the demo data is fictional and isolated.
- [ ] I create a `feature/...` or `fix/...` branch for every assignment.
- [ ] I run automated and manual tests before requesting review.
- [ ] I push only my feature branch and open a PR targeting `develop`.
- [ ] I request review from `@javahedi` and wait for a decision.
- [ ] I will **never** directly push/merge to `develop` or `main`, force-push shared branches, reset databases, or deploy without approval.

**Acknowledgment**
Contributor name: ________________________
GitHub username: ________________________
Date: ________________________
Signature (optional): ________________________

---

**Owner's first setup action:** Invite the colleague, then confirm GitHub access and **test that only the owner can merge**. Only afterward assign the first feature branch.

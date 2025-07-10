# Clank Tank Backend Security Review (OWASP Top 10)

This checklist is based on the OWASP Top 10 security risks. Each item includes system-specific context and pointers to help a new reviewer perform a thorough, honest review. Please read the context and check off each item as you complete it. Add findings or notes under each section.

## Key File Roles

- **app.py**: Main FastAPI server. Handles all API endpoints, Discord OAuth, CORS, rate limiting, and most business logic. All authentication, access control, and user/session management is here. Also responsible for serving uploaded files and static data generation.
- **create_db.py**: Creates and initializes the SQLite database, including all tables, indexes, and constraints. Defines the schema for submissions, users, scores, feedback, and research. Ensures audit logging is set up.
- **github_analyzer.py**: Fetches and analyzes external GitHub repositories for research and scoring. Makes outbound HTTP requests, parses repo data, and may process user-supplied URLs. SSRF and input validation are key concerns here.
- **migrate_schema.py**: Handles database schema migrations and field additions. Can add columns to tables and update schema manifests. Ensures DB structure matches the evolving schema.
- **simple_audit.py**: Implements audit logging for all sensitive actions (who did what when). Provides decorators and helpers for logging user/system/security events to the audit table in the DB.
- **sync_schema_to_frontend.py**: Syncs the backend submission schema to the frontend and generates TypeScript types. Ensures frontend and backend are in sync, but does not handle user data or authentication directly.

## TODO

- [ ] **1. Broken Access Control**
  - **Context:**
    - All user authentication is via Discord OAuth (see `app.py`, `users` table).
    - Users should only be able to create, edit, or view their own submissions and data.
    - Admin or judge-only endpoints may exist for scoring, research, or moderation.
    - **Files to check:**
      - `app.py`: All API endpoints, especially those for submissions, editing, uploads, and admin/judge actions. Look for `validate_discord_token`, permission checks, and any endpoints that return or modify user data.
      - `create_db.py`: Defines the users table and submission ownership fields (e.g., `owner_discord_id`).
      - `simple_audit.py`: Check that audit logs record user IDs for sensitive actions.
    - **What to look for:**
      - Are all endpoints protected by authentication?
      - Is user identity checked before allowing access to or modification of data?
      - Are there endpoints that could leak or allow modification of other users' data?

- [ ] **2. Cryptographic Failures**
  - **Context:**
    - Discord OAuth tokens and any API secrets should be stored in environment variables, not in code or repo.
    - All API traffic should be over HTTPS in production.
    - No custom cryptography is used; relies on Discord and standard libraries.
    - **Files to check:**
      - `app.py`: OAuth logic, token handling, and any logging of sensitive data.
      - `.env` and deployment configs: Ensure secrets are not hardcoded.
    - **What to look for:**
      - Are secrets/tokens hardcoded anywhere?
      - Is HTTPS enforced in production?
      - Are any sensitive values logged or exposed in error messages?

- [ ] **3. Injection (SQL, Command, etc.)**
  - **Context:**
    - Uses SQLAlchemy ORM for most DB access (see `app.py`, `hackathon_manager.py`, etc.).
    - Some scripts or endpoints may use raw SQL for migrations or analytics.
    - User input is accepted for submissions, research, and feedback.
    - **Files to check:**
      - `app.py`: All DB access, especially any use of `text()` or raw SQL. Check for parameterized queries and input validation.
      - `create_db.py` and `migrate_schema.py`: Table/column creation and schema changes. Ensure no unsafe SQL execution.
      - `github_analyzer.py`: Any shell commands or subprocesses (e.g., Repomix, GitIngest), and any parsing of user-supplied URLs.
    - **What to look for:**
      - Any use of raw SQL with user input? (Should use parameterized queries.)
      - Is all user input validated and sanitized?
      - Are shell commands or subprocesses used with user input?

- [ ] **4. Insecure Design**
  - **Context:**
    - The system is schema-driven and versioned (see `schema.py`, `submission_schema.json`).
    - Audit logging is implemented (`simple_audit.py`).
    - No IP addresses are stored for privacy.
    - **Files to check:**
      - `app.py`: New features, endpoints, and any logic that could expose sensitive data.
      - `schema.py`, `submission_schema.json`: Ensure only necessary fields are exposed.
      - `simple_audit.py`: Audit logging coverage.
      - `migrate_schema.py`: Schema evolution and field additions.
    - **What to look for:**
      - Are new features threat-modeled before launch?
      - Is least privilege enforced (users/judges/admins)?
      - Are there endpoints or features that expose more data than necessary?

- [ ] **5. Security Misconfiguration**
  - **Context:**
    - FastAPI server config is in `app.py` and deployment scripts.
    - CORS settings, debug mode, and allowed hosts should be reviewed.
    - Rate limiting is implemented via `slowapi` in `app.py`.
    - **Files to check:**
      - `app.py`: CORS middleware, rate limiting, debug settings.
      - Deployment configs, Dockerfiles (if any): Production settings.
    - **What to look for:**
      - Is debug mode disabled in production?
      - Are CORS settings restrictive?
      - Are unnecessary ports/services disabled?
      - Are dependencies up to date?

- [ ] **6. Vulnerable and Outdated Components**
  - **Context:**
    - Python dependencies are in `requirements.txt`.
    - Uses FastAPI, SQLAlchemy, Discord.py, OpenAI, Anthropic, Requests, etc.
    - **Files to check:**
      - `requirements.txt`, `README.md`: Dependency list.
      - `github_analyzer.py`: Any use of external tools or libraries (e.g., Repomix, GitIngest).
    - **What to look for:**
      - Are dependencies regularly updated?
      - Are there any known vulnerabilities (use `pip-audit`, `safety`, or similar)?

- [ ] **7. Identification and Authentication Failures**
  - **Context:**
    - All authentication is via Discord OAuth (see `app.py`).
    - No passwords are stored; only OAuth tokens.
    - Session management is handled in the backend and frontend.
    - **Files to check:**
      - `app.py`: OAuth logic, session/token handling, and endpoints requiring authentication.
      - `create_db.py`: Users table structure.
    - **What to look for:**
      - Are OAuth tokens validated server-side?
      - Are sessions/tokens invalidated on logout?
      - Is there any way to bypass authentication?

- [ ] **8. Software and Data Integrity Failures**
  - **Context:**
    - Audit logging is in `simple_audit.py`.
    - Schema versioning is in `schema.py` and `submission_schema.json`.
    - Database migrations are handled by `migrate_schema.py`.
    - **Files to check:**
      - `simple_audit.py`: Audit log implementation and coverage.
      - `migrate_schema.py`: Schema changes and migration safety.
      - `create_db.py`: Initial schema creation and constraints.
    - **What to look for:**
      - Are all sensitive actions logged?
      - Are there integrity checks for critical files or schema?
      - Is the audit log protected from tampering?

- [ ] **9. Security Logging and Monitoring Failures**
  - **Context:**
    - All actions are logged via `simple_audit.py`.
    - Logs should be monitored for suspicious activity.
    - **Files to check:**
      - `simple_audit.py`: Log storage, log review/monitoring setup.
      - `app.py`: Calls to audit logging functions.
    - **What to look for:**
      - Are all sensitive actions (login, data changes, etc.) logged?
      - Are logs reviewed or monitored?
      - Are alerts set up for critical events?

- [ ] **10. Server-Side Request Forgery (SSRF)**
  - **Context:**
    - The system fetches external URLs for GitHub analysis and research (see `github_analyzer.py`, `research.py`).
    - User-supplied URLs may be used for repo analysis.
    - **Files to check:**
      - `github_analyzer.py`: All HTTP requests, especially those using user-supplied URLs. Look for validation and restrictions.
      - `app.py`: Any endpoints that accept URLs or fetch external data.
    - **What to look for:**
      - Are URLs validated and restricted before fetching?
      - Is SSRF risk mitigated (e.g., block internal IPs, localhost, etc.)?

---

**Instructions:**
- Work through each item, checking the box when complete.
- Add notes, findings, or follow-ups under each item as needed.
- Refer to the file paths and context above for where to look and what to check. 
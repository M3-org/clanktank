# Hackathon TODO — Discord Guild Roles Capture

## Feature: Capture Discord roles for users in the hackathon guild

- **Goal**: When a user authenticates via Discord, record their roles (for `DISCORD_GUILD_ID`) and store them in the DB for feature-gating.
- **Approach**: Prefer bot-based lookup if `DISCORD_BOT_TOKEN` is available; otherwise use OAuth scope `guilds.members.read`.

## Relevant Files
- `hackathon/backend/app.py`: OAuth scopes, token exchange, user validation, DB schema init/migration, API responses
- `hackathon/backend/data/hackathon.db`: add `users.roles` column (TEXT JSON array of role IDs)
- `hackathon/dashboard/frontend/src/contexts/AuthContext.tsx`: extend `DiscordUser` type with optional `roles: string[]`
- `hackathon/dashboard/frontend/src/lib/api.ts`: ensure `/auth/me` and callback return `roles`
- `hackathon/dashboard/frontend/src/lib/storage.ts`: optionally persist roles alongside auth
- `.env.example`: add `DISCORD_GUILD_ID`, optional `DISCORD_BOT_TOKEN`; note OAuth scope `guilds.members.read`

### Security Fixes (Applied)
- Path Traversal mitigation in `hackathon/backend/app.py` for `/api/uploads/{filename}`:
  - Resolve and validate path stays within `data/uploads` via `resolve()` and `relative_to()`; return 400 on invalid paths, 404 when not found.
- XSS mitigation in `hackathon/dashboard/frontend/src/components/Markdown.tsx`:
  - Replaced ad-hoc script stripping with `DOMPurify.sanitize` allowing no raw HTML.
  - Added safe URL check for `a.href` and `img.src` (http/https only); block others.
  - Added dependency `dompurify` to `hackathon/dashboard/frontend/package.json`.

## Implementation Notes (Security)
- The uploads endpoint now rejects traversal attempts like `../../etc/passwd` with HTTP 400.
- Markdown input is sanitized before rendering; raw HTML is stripped to rely on Markdown only.

## Tasks

### Backend
- [ ] Add env config: `DISCORD_GUILD_ID` (required), `DISCORD_BOT_TOKEN` (optional)
- [ ] Update auth URL scopes to include `identify guilds guilds.members.read` when bot token not present
- [ ] On login and on `/auth/me`, fetch roles for the user for `DISCORD_GUILD_ID`:
  - [ ] Preferred: GET `https://discord.com/api/guilds/{guild_id}/members/{user_id}` with `Bot` token
  - [ ] Fallback: GET `https://discord.com/api/users/@me/guilds/{guild_id}/member` with user `Bearer` token (requires `guilds.members.read`)
- [ ] DB migration at startup: ensure `users.roles` (TEXT) exists; create if missing
- [ ] Store roles as JSON array of role IDs in `users.roles`
- [ ] Extend `DiscordUser` response model to include `roles: List[str] | None`

### Frontend
- [ ] Update `DiscordUser` in `AuthContext.tsx` to include optional `roles: string[]`
- [ ] `hackathonApi.getCurrentUser` should pass through roles; no breaking changes
- [ ] Optional: `storage.ts` allow persisting roles (backward compatible)
- [ ] Add tiny helper (later): `hasRole(roleId: string)` for gating UI (not in this PR)

### Documentation
- [ ] Update README(s):
  - [ ] Document `DISCORD_GUILD_ID` and optional `DISCORD_BOT_TOKEN`
  - [ ] If no bot token, add OAuth scope `guilds.members.read` and note app must be in the guild
- [ ] Update `.env.example` with these keys and comments

## Acceptance Criteria
- [ ] After Discord login, DB `users` row has `roles` JSON array (e.g., `["12345","67890"]`)
- [ ] `/api/auth/me` returns `roles` and frontend stores it in state
- [ ] Fallback path works when only OAuth scopes are configured (no bot token)
- [ ] No regression to existing auth flows

## Notes / Risks
- Bot approach requires the bot in the guild with permissions to view members.
- OAuth approach requires `guilds.members.read` and app added to the guild; users must be members.
- Store role IDs (not names) to keep stable references; resolve names on-demand if needed.

## Follow-up: Role Names Mapping (Nice-to-have)
- [ ] Fetch guild roles list via bot (`GET https://discord.com/api/guilds/{guild_id}/roles`) and cache in-memory (e.g., 5–15 min TTL)
- [ ] On `/auth/me`, map stored `roles` (IDs) to names and include `roles_names: string[]` (non-breaking)
- [ ] Optional: expose `role_flags` based on `.env` configured important roles (e.g., `JUDGE_ROLE_ID`, `ADMIN_ROLE_ID`)
- [ ] Keep DB storing IDs only (truth); resolve names at response time using the cache

---

## Prompt Consolidation — Research
- Consolidated research prompt assembly to `hackathon/prompts/research_prompts.py`.
- Backend now delegates prompt construction: `hackathon/backend/research.py -> create_research_prompt(...)`.
- Removed legacy inline prompt text in `research.py`.

### Relevant Files
- `hackathon/backend/research.py`: uses `create_research_prompt` and handles IO/cache/DB only
- `hackathon/prompts/research_prompts.py`: source of truth for research prompt templates and helpers

### Implementation Notes
- `create_research_prompt(project_data, github_analysis, gitingest_content)` trims large inputs and adds timing context.
- Kept fallback import to support package-relative execution.

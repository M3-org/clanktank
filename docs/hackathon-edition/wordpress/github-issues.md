# Potential GitHub Issues for WordPress Hackathon Integration

---

## 0. [Meta] Review and Approve WordPress Hackathon Issues Plan
**Labels:** hackathon, wordpress

**Description:**
Review this `github-issues.md` file, which lists all proposed GitHub issues for the WordPress-based hackathon judging system. Confirm that the scope, context, and operational details for each task are correct and sufficient before creating individual issues. Suggest edits, additions, or removals as needed.

**Operational Context:**
- This file is intended as a planning checkpoint for the WordPress integration team.
- Once approved, each issue can be created in GitHub for tracking and assignment.
- See canonical references in each issue for further detail.
- **Security Note:** Do not collect sensitive personal information (such as email addresses) if endpoints are public or unauthenticated. Use Discord username (required), X (Twitter) username (optional), and Solana wallet (optional) for contact. See [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md) for details.

---

## 1. [WordPress] Implement `/wp-json/hackathon/v1/submissions` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Implement a REST API endpoint that returns a list of all hackathon project submissions, supporting optional query params (`status`, `category`). Response must match the canonical dashboard API shape. Use WP_Query/meta queries and expose all required fields via ACF or `register_post_meta` with `show_in_rest: true`.

**Operational Context:**
- Canonical API shape and field list: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Data model: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Must be compatible with the React dashboard frontend, which expects fields like `submission_id`, `project_name`, `team_name`, `category`, `status`, `created_at`, `avg_score`, `judge_count`, `discord_username`, `x_username`, and `solana_wallet`.
- **Security Note:** Do not include email or other sensitive info.

---

## 2. [WordPress] Implement `/wp-json/hackathon/v1/submission/{id}` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Create a REST API endpoint to return detailed information for a single submission by ID. Response must include all fields as per the canonical data model (project info, team, scores, research, etc.).

**Operational Context:**
- Canonical API and field list: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Data model: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Example fields: `project_name`, `team_name`, `category`, `description`, `status`, `created_at`, `github_url`, `scores`, `research`, `discord_username`, `x_username`, `solana_wallet`.
- **Security Note:** Do not include email or other sensitive info.

---

## 3. [WordPress] Implement `/wp-json/hackathon/v1/submission/{id}/feedback` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Add an endpoint to return community feedback for a submission. Should aggregate reactions, vote counts, and voter lists. Store feedback in post meta or a custom table for performance.

**Operational Context:**
- Canonical feedback structure: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Example: feedback is an array of objects with `reaction_type`, `emoji`, `name`, `vote_count`, and `voters`.
- See [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py) for aggregation logic and emoji mapping.

---

## 4. [WordPress] Implement `/wp-json/hackathon/v1/leaderboard` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Create a leaderboard endpoint that returns ranked projects by final score. Use WP_Query/meta queries for aggregation and sorting.

**Operational Context:**
- Canonical leaderboard shape: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Data model: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Example fields: `rank`, `project_name`, `team_name`, `category`, `final_score`, `youtube_url`.

---

## 5. [WordPress] Implement `/wp-json/hackathon/v1/stats` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Add an endpoint to return overall statistics for the dashboard. Should return total submissions, counts by status and category, and last update timestamp.

**Operational Context:**
- Canonical stats shape: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Example: `{ "total_submissions": 100, "by_status": {"submitted": 20}, "by_category": {"DeFi": 30}, "updated_at": "..." }`

---

## 6. [WordPress] Build/Update Hackathon Submission Form (Elementor/ACF)
**Labels:** hackathon, wordpress

**Description:**
Design and implement the hackathon project submission form using Elementor and/or ACF. Ensure all canonical fields are present ([Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)). Only collect Discord username (required), X (Twitter) username (optional), and Solana wallet (optional) for contact. Validation, user feedback, and confirmation email are optional enhancements, not strictly required, but recommended for better UX.

**Operational Context:**
- Canonical field list: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Implementation notes: [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md)
- Test end-to-end submission and data storage.
- **Security Note:** Do not include email or other sensitive info.

---

## 7. [WordPress] Configure ACF Field Group for Hackathon Projects
**Labels:** hackathon, wordpress

**Description:**
Set up an ACF field group for all hackathon project fields (team info, project URLs, category, status, research, scores, feedback, etc.). Ensure all fields are exposed in the REST API (`show_in_rest: true`). Only collect Discord username (required), X (Twitter) username (optional), and Solana wallet (optional) for contact.

**Operational Context:**
- Canonical field list: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Test with REST API and dashboard frontend.
- **Security Note:** Do not include email or other sensitive info.

---

## 8. [WordPress] Build Admin Dashboard for Project Review & Scoring
**Labels:** hackathon, wordpress

**Description:**
Create an admin UI for reviewing submissions, entering judge scores, and updating project status. Should display all project data, scores, and feedback. Optionally, add bulk actions and filters.

**Operational Context:**
- Canonical judging workflow: [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py)
- Implementation notes: [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md)

---

## 9. [WordPress] Implement Static Data Export for Static Site Deployment
**Labels:** hackathon, wordpress

**Description:**
Add a static data export option (e.g., via WP-CLI or a custom endpoint) to generate JSON files for submissions, leaderboard, and stats. Output must match the dashboard API shape for static hosting.

**Operational Context:**
- Canonical static export: [dashboard README](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/README.md)
- Useful for GitHub Pages or other static hosting.

---

## 10. [WordPress] Document and Test API Compatibility with Dashboard Frontend
**Labels:** hackathon, wordpress

**Description:**
Test the WordPress API endpoints with the React dashboard frontend. Document any issues, required tweaks, or WP-specific logic. Update documentation and code as needed for full compatibility.

**Operational Context:**
- Canonical API and frontend: [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py), [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)

---

## 11. [WordPress] Ensure All Submission, Score, Research, and Feedback Fields Are Exposed in REST API
**Labels:** hackathon, wordpress

**Description:**
Audit and update the WordPress data model to ensure all required fields are present and exposed in the REST API. Use ACF or `register_post_meta` with `show_in_rest: true`. Fields must match the canonical data model. Only collect Discord username (required), X (Twitter) username (optional), and Solana wallet (optional) for contact.

**Operational Context:**
- Canonical field list: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Test with the dashboard frontend for compatibility.
- **Security Note:** Do not include email or other sensitive info.

---

## 12. [WordPress] Update Documentation and Cross-Link All Implementation Notes
**Labels:** hackathon, wordpress

**Description:**
Update all documentation to reflect the latest implementation, cross-linking between API reference, data model, and implementation notes. Ensure new contributors can easily find canonical sources and operational context.

**Operational Context:**
- Implementation notes: [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md)
- API reference: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Data model: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)

--- 
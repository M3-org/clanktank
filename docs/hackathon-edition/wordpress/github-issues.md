# Potential GitHub Issues for WordPress Hackathon Integration

This file lists actionable GitHub issues to guide the implementation and improvement of the WordPress-based hackathon judging system. Each issue includes a title, description, operational context, and suggested labels (`hackathon`, `wordpress`).

---

## 1. [WordPress] Implement `/wp-json/hackathon/v1/submissions` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Implement a REST API endpoint that returns a list of all hackathon project submissions, supporting optional query params (`status`, `category`). Response must match the canonical dashboard API shape. Use WP_Query/meta queries and expose all required fields via ACF or `register_post_meta` with `show_in_rest: true`.

**Operational Context:**
- Reference: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md), [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Must be compatible with the React dashboard frontend.

---

## 2. [WordPress] Implement `/wp-json/hackathon/v1/submission/{id}` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Create a REST API endpoint to return detailed information for a single submission by ID. Response must include all fields as per the canonical data model (project info, team, scores, research, etc.).

**Operational Context:**
- Reference: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Test with a real project and ensure all fields are present.

---

## 3. [WordPress] Implement `/wp-json/hackathon/v1/submission/{id}/feedback` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Add an endpoint to return community feedback for a submission. Should aggregate reactions, vote counts, and voter lists. Store feedback in post meta or a custom table for performance.

**Operational Context:**
- Reference: [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py)
- Ensure emoji/reaction mapping matches frontend expectations.

---

## 4. [WordPress] Implement `/wp-json/hackathon/v1/leaderboard` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Create a leaderboard endpoint that returns ranked projects by final score. Use WP_Query/meta queries for aggregation and sorting.

**Operational Context:**
- Reference: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Test with published projects and ensure correct ranking.

---

## 5. [WordPress] Implement `/wp-json/hackathon/v1/stats` Endpoint
**Labels:** hackathon, wordpress

**Description:**
Add an endpoint to return overall statistics for the dashboard. Should return total submissions, counts by status and category, and last update timestamp.

**Operational Context:**
- Reference: [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Ensure data matches what the dashboard expects.

---

## 6. [WordPress] Build/Update Hackathon Submission Form (Elementor/ACF)
**Labels:** hackathon, wordpress

**Description:**
Design and implement the hackathon project submission form using Elementor and/or ACF. Ensure all canonical fields are present (see [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)). Add validation, user feedback, and confirmation email as needed.

**Operational Context:**
- Reference: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md), [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md)
- Test end-to-end submission and data storage.

---

## 7. [WordPress] Configure ACF Field Group for Hackathon Projects
**Labels:** hackathon, wordpress

**Description:**
Set up an ACF field group for all hackathon project fields (team info, project URLs, category, status, research, scores, feedback, etc.). Ensure all fields are exposed in the REST API (`show_in_rest: true`).

**Operational Context:**
- Reference: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Test with REST API and dashboard frontend.

---

## 8. [WordPress] Build Admin Dashboard for Project Review & Scoring
**Labels:** hackathon, wordpress

**Description:**
Create an admin UI for reviewing submissions, entering judge scores, and updating project status. Should display all project data, scores, and feedback. Optionally, add bulk actions and filters.

**Operational Context:**
- Reference: [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py), [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md)
- Ensure workflow matches canonical judging process.

---

## 9. [WordPress] Implement Static Data Export for Static Site Deployment
**Labels:** hackathon, wordpress

**Description:**
Add a static data export option (e.g., via WP-CLI or a custom endpoint) to generate JSON files for submissions, leaderboard, and stats. Output must match the dashboard API shape for static hosting.

**Operational Context:**
- Reference: [dashboard README](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/README.md)
- Useful for GitHub Pages or other static hosting.

---

## 10. [WordPress] Document and Test API Compatibility with Dashboard Frontend
**Labels:** hackathon, wordpress

**Description:**
Test the WordPress API endpoints with the React dashboard frontend. Document any issues, required tweaks, or WP-specific logic. Update documentation and code as needed for full compatibility.

**Operational Context:**
- Reference: [dashboard/app.py](https://github.com/m3-org/clanktank/blob/main/scripts/hackathon/dashboard/app.py), [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md)
- Ensure all endpoints and fields are present and correctly shaped.

---

## 11. [WordPress] Ensure All Submission, Score, Research, and Feedback Fields Are Exposed in REST API
**Labels:** hackathon, wordpress

**Description:**
Audit and update the WordPress data model to ensure all required fields are present and exposed in the REST API. Use ACF or `register_post_meta` with `show_in_rest: true`. Fields must match the canonical data model.

**Operational Context:**
- Reference: [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Test with the dashboard frontend for compatibility.

---

## 12. [WordPress] Update Documentation and Cross-Link All Implementation Notes
**Labels:** hackathon, wordpress

**Description:**
Update all documentation to reflect the latest implementation, cross-linking between API reference, data model, and implementation notes. Ensure new contributors can easily find canonical sources and operational context.

**Operational Context:**
- Reference: [Implementation Notes](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/implementation-notes.md), [API Reference](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/api-reference.md), [Data Model](https://github.com/m3-org/clanktank/blob/main/docs/hackathon-edition/wordpress/data-model.md)
- Review for clarity and completeness.

--- 
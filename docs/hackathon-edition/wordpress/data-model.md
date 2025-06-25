# WordPress Hackathon Data Model

This page documents the recommended data model for the WordPress-based hackathon judging system, aligned with the canonical Python/React implementation and dashboard frontend.

> **Security Note:**
> If submission data is exposed via non-authenticated endpoints, do not collect sensitive personal information (such as email addresses). Use Discord and X (Twitter) usernames for contact, and optionally allow a Solana wallet address for prize distribution or verification.

## Submission Fields

| Field                | Type     | Description                                 | Canonical Mapping           |
|----------------------|----------|---------------------------------------------|-----------------------------|
| submission_id        | string   | Unique ID for the submission                | submission_id               |
| project_name         | string   | Name of the project                         | project_name                |
| team_name            | string   | Name of the team or builder                 | team_name                   |
| category             | string   | Project category (DeFi, AI/Agents, etc.)    | category                    |
| description          | string   | Project description                         | description                 |
| status               | string   | Submission status (submitted, published, etc.) | status                  |
| created_at           | string   | ISO timestamp of submission creation        | created_at                  |
| updated_at           | string   | ISO timestamp of last update                | updated_at                  |
| github_url           | string   | GitHub repository URL                       | github_url                  |
| demo_video_url       | string   | Demo video URL                              | demo_video_url              |
| live_demo_url        | string   | Live demo URL (optional)                    | live_demo_url               |
| tech_stack           | string   | Main languages/frameworks (optional)        | tech_stack                  |
| how_it_works         | string   | Short explanation of how it works           | how_it_works                |
| problem_solved       | string   | Problem the project solves                  | problem_solved              |
| coolest_tech         | string   | Coolest technical part                      | coolest_tech                |
| next_steps           | string   | What the team is building next              | next_steps                  |
| discord_username     | string   | Discord username for contact                | discord_username            |
| x_username           | string   | X (Twitter) username for contact (optional) | x_username                  |
| solana_wallet        | string   | Solana wallet address (optional)            | solana_wallet               |

## Judge Scores

- Stored as a structured array/object in post meta or a custom table.
- Each judge scores:
  - innovation
  - technical_execution
  - market_potential
  - user_experience
  - weighted_total
  - notes (optional, JSON)

## Research Data

- Store as a JSON object in post meta:
  - github_analysis
  - market_research
  - technical_assessment

## Community Feedback

- Store as a structured array/object in post meta or a custom table:
  - reaction_type (e.g., hype, innovation_creativity, technical_execution, market_potential, user_experience)
  - vote_count
  - voters (array of usernames or IDs)

## Leaderboard Entry

| Field        | Type   | Description                |
|--------------|--------|----------------------------|
| rank         | int    | Project rank               |
| project_name | string | Name of the project        |
| team_name    | string | Name of the team           |
| category     | string | Project category           |
| final_score  | float  | Final weighted score       |
| youtube_url  | string | YouTube/demo video URL     |

## Status & Category Values

- **Status:** submitted, researched, round1_complete, published, etc.
- **Category:** DeFi, AI/Agents, Gaming, Infrastructure, Social, Other

## Mapping to Canonical System

- All fields and structures should match those in [hackathon-show-config.md](../hackathon-show-config.md) and [dashboard/app.py](../../scripts/hackathon/dashboard/app.py).
- Use ACF or `register_post_meta` with `show_in_rest: true` to expose all fields in the WP REST API.
- For aggregation (leaderboard, stats), use WP_Query or custom SQL as needed.

## See Also
- [API Reference](./api-reference.md)
- [Canonical Config](../hackathon-show-config.md)
- [Dashboard Backend](../../scripts/hackathon/dashboard/app.py) 
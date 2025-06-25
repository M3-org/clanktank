# WordPress Hackathon REST API Reference

This page documents the recommended REST API endpoints for the WordPress-based hackathon judging system, inspired by the canonical dashboard implementation and designed for compatibility with a React or static frontend.

## Overview

- All endpoints should be registered under `/wp-json/hackathon/v1/`.
- Data models and field names should match the canonical system (see [hackathon-show-config.md](../hackathon-show-config.md) and [dashboard README](../../scripts/hackathon/dashboard/README.md)).
- Use `register_rest_route` and `register_post_meta`/ACF to expose all necessary fields.

## Endpoints

### 1. List Submissions
- **GET** `/wp-json/hackathon/v1/submissions`
- **Query Params:** `status`, `category` (optional)
- **Response:**
```json
[
  {
    "submission_id": "...",
    "project_name": "...",
    "team_name": "...",
    "category": "...",
    "status": "...",
    "created_at": "...",
    "avg_score": 37.5,
    "judge_count": 4
  },
  ...
]
```

### 2. Submission Detail
- **GET** `/wp-json/hackathon/v1/submission/{id}`
- **Response:**
```json
{
  "submission_id": "...",
  "project_name": "...",
  "team_name": "...",
  "category": "...",
  "description": "...",
  "status": "...",
  "created_at": "...",
  "updated_at": "...",
  "github_url": "...",
  "demo_video_url": "...",
  "live_demo_url": "...",
  "tech_stack": "...",
  "how_it_works": "...",
  "problem_solved": "...",
  "coolest_tech": "...",
  "next_steps": "...",
  "scores": [
    {
      "judge_name": "Marc",
      "innovation": 8,
      "technical_execution": 7,
      "market_potential": 9,
      "user_experience": 7,
      "weighted_total": 33.5,
      "notes": {}
    }
  ],
  "research": {
    "github_analysis": {},
    "market_research": {},
    "technical_assessment": {}
  },
  "avg_score": 37.5
}
```

### 3. Submission Feedback
- **GET** `/wp-json/hackathon/v1/submission/{id}/feedback`
- **Response:**
```json
{
  "submission_id": "...",
  "total_votes": 42,
  "feedback": [
    {
      "reaction_type": "hype",
      "emoji": "🔥",
      "name": "General Hype",
      "vote_count": 20,
      "voters": ["user1", "user2"]
    },
    ...
  ]
}
```

### 4. Leaderboard
- **GET** `/wp-json/hackathon/v1/leaderboard`
- **Response:**
```json
[
  {
    "rank": 1,
    "project_name": "...",
    "team_name": "...",
    "category": "...",
    "final_score": 38.5,
    "youtube_url": "..."
  },
  ...
]
```

### 5. Stats
- **GET** `/wp-json/hackathon/v1/stats`
- **Response:**
```json
{
  "total_submissions": 100,
  "by_status": {"submitted": 20, "published": 80},
  "by_category": {"DeFi": 30, "AI/Agents": 40, ...},
  "updated_at": "2025-06-03T12:00:00Z"
}
```

## Notes
- All endpoints should return data in the shape expected by the dashboard frontend for drop-in compatibility.
- Use WP_Query and meta queries for aggregation endpoints (leaderboard, stats).
- For custom fields, use `register_post_meta` or ACF with `show_in_rest: true`.
- For feedback, store reactions and voters in a structured meta field or custom table.
- See [dashboard/app.py](../../scripts/hackathon/dashboard/app.py) for reference implementation. 
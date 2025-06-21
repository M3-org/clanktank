# {{ project_title }}

**Team:** {{ team_name }}  
**Category:** {{ category }}  
**Submission ID:** {{ submission_id }}

## Description
{{ description }}

## Links
- **GitHub:** [{{ github_url }}]({{ github_url }})
- **Demo Video:** [{{ demo_video_url }}]({{ demo_video_url }})
{% if live_demo_url %}
- **Live Demo:** [{{ live_demo_url }}]({{ live_demo_url }})
{% endif %}

## How It Works
{{ how_it_works }}

## Problem Solved
{{ problem_solved }}

## Technical Highlights
{{ technical_highlights }}

## What's Next
{{ whats_next }}

{% if tech_stack %}
## Tech Stack
{{ tech_stack }}
{% endif %}

{% if team_members %}
## Team Members
{{ team_members }}
{% endif %}

## Contact
{% if discord_handle %}
- Discord: {{ discord_handle }}
{% endif %}
{% if twitter_handle %}
- Twitter: {{ twitter_handle }}
{% endif %}

---
*Processed for Clank Tank Hackathon Edition*
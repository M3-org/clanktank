# Create Hackathon Episode Generation

## Overview
Create a new script, `hackathon_episode_generator.py`, that uses the final, synthesized data from `hackathon.db` to generate structured JSON files. These files will serve as a complete blueprint for rendering compelling hackathon episodes, telling the story of each project's journey through the judging process.

## Background
With all scoring and synthesis complete, this script will transform the raw data into a narrative. It will generate a "show script" that contrasts the judges' initial expert analysis with the community's sentiment, culminating in a final verdict. This structured JSON output can then be used by a rendering engine (like PlayCanvas, After Effects, or Remotion) to create the final video.

## Requirements

### Episode Generation Logic
1. **Fetch Completed Projects**: The script will query `hackathon.db` for projects with `status = 'completed'`. It can be run for a single project or a batch to create a multi-project episode.
2. **Structure Episode Data**: For each project, it will pull all relevant data:
   - Submission details from `hackathon_submissions`.
   - The initial Round 1 scores and final text verdicts for each judge from `hackathon_scores`.
   - The community vote tally and the final calculated community bonus.
3. **Generate a Narrative Script**: The core of this script is to generate a show script that follows a clear narrative arc for each project:
   - **Host Intro**: Generate dialogue for Eliza to introduce the project.
   - **Present R1 Scores**: Show the initial scores from the judges.
   - **Present Community Feedback**: Show the community's reaction, creating a "twist".
   - **Synthesize Final Verdicts**: Convert the judges' final verdict notes into spoken dialogue that reconciles their initial thoughts with the community's input.
   - **Reveal Final Score**: Generate an outro for Eliza to summarize and announce the final combined score.
4. **Format Output JSON**: The script will output a structured JSON file containing the entire episode flow, including scene changes, character dialogue, and specific on-screen graphic cues.

### Tasks
- [ ] Create `scripts/hackathon/hackathon_episode_generator.py`.
- [ ] Implement logic to fetch all necessary data (R1/R2 scores, community votes, etc.) from `hackathon.db`.
- [ ] Create powerful AI prompts to generate host and judge dialogue that follows a narrative arc.
- [ ] Structure the output into a well-defined JSON format with specific events for dialogue, graphics, and scene changes.
- [ ] Add support for generating single-project or multi-project episodes.
- [ ] Implement a templating system for different episode segments (intro, project review, outro).
- [ ] Add command-line interface to trigger episode generation.

## Technical Details

### Episode Narrative Flow
For each project, the generated episode events should follow this structure to create a compelling narrative:
1.  **Eliza:** Introduces the project.
2.  **Graphic:** `show_project_card` (name, description).
3.  **Eliza:** Presents the initial, "expert-only" scores from Round 1.
4.  **Graphic:** `show_r1_scores` (judges' weighted scores).
5.  **Eliza:** "But what did the community think? Let's look at the votes."
6.  **Graphic:** `show_community_tally` (counts for all 5 reaction types).
7.  **Eliza:** Asks a judge for their final thoughts, considering the community's reaction.
8.  **Judge:** Delivers their AI-generated final verdict dialogue.
9.  **Repeat 7-8** for all judges.
10. **Eliza:** Reveals the final score.
11. **Graphic:** `show_final_score` (R1 score + community bonus).

### Example Dialogue Generation Prompt
```python
# In prompts/episode_dialogue.py
def create_dialogue_prompt(judge_name, r1_notes, community_summary, final_verdict):
    return f\"\"\"
    You are the AI persona for {judge_name}, a judge on an AI game show.
    Your task is to convert your analytical notes into a single, concise, spoken line for the final show.
    
    Here's the data for your review:
    
    **Your Private Round 1 Notes:**
    "{r1_notes}"

    **Community Feedback Summary:**
    - Innovation: {community_summary.get('innovation_creativity', 0)} votes
    - Technical: {community_summary.get('technical_execution', 0)} votes
    - Market: {community_summary.get('market_potential', 0)} votes
    - UX: {community_summary.get('user_experience', 0)} votes
    - Hype: {community_summary.get('hype', 0)} votes

    **Your Final Written Verdict (after seeing community feedback):**
    "{final_verdict}"

    **Instructions:**
    Based on all the above, generate a single, punchy, spoken line of dialogue (40 words max) that summarizes your final stance. Start by addressing the host, Eliza. Make it sound natural, as if you're speaking on a show.
    \"\"\"
```

### Output JSON Structure (Example)
```json
{
  "episode_title": "Hackathon Finals: AI vs. DeFi",
  "segments": [
    {
      "segment_type": "intro",
      "events": [
        { "type": "dialogue", "character": "Eliza", "line": "Welcome back! First up, we have a project aiming to revolutionize decentralized finance..." }
      ]
    },
    {
      "segment_type": "project_review",
      "submission_id": "proj_123",
      "project_name": "DeFiLlama AI",
      "events": [
        { "type": "show_graphic", "graphic_type": "project_card", "data": { "name": "DeFiLlama AI", "description": "AI-powered portfolio management." } },
        { "type": "dialogue", "character": "Eliza", "line": "Here's how our judges scored it in Round 1, based on their expert analysis." },
        { "type": "show_graphic", "graphic_type": "r1_scores", "data": { "aimarc": 8.5, "aishaw": 7.0, "spartan": 9.0, "peepo": 6.5 } },
        { "type": "dialogue", "character": "Eliza", "line": "But the community had their own say! Let's see the votes." },
        { "type": "show_graphic", "graphic_type": "community_tally", "data": { "innovation_creativity": 50, "technical_execution": 35, "market_potential": 80, "user_experience": 20, "hype": 120 } },
        { "type": "dialogue", "character": "Eliza", "line": "Marc, the community clearly loved the market potential here. What's your final word?" },
        { "type": "dialogue", "character": "AI Marc", "line": "Eliza, the community is spot on. This isn't just a project, it's a future unicorn. My score stands, and my conviction is even higher." },
        { "type": "dialogue", "character": "AI Shaw", "line": "Eliza, while I see the hype, the codebase needs a refactor. A solid effort, but the tech needs work to match the vision." },
        { "type": "dialogue", "character": "Eliza", "line": "Alright, with the community bonus added, let's see the final score!" },
        { "type": "show_graphic", "graphic_type": "final_score", "data": { "total_score": 44.5 } }
      ]
    },
    {
      "segment_type": "outro",
      "events": [
        { "type": "dialogue", "character": "Eliza", "line": "What an incredible project! Join us after the break for our next finalist." }
      ]
    }
  ]
}
```

## Files to Create
- `scripts/hackathon/hackathon_episode_generator.py`
- `scripts/hackathon/prompts/episode_dialogue.py`

## Acceptance Criteria
- [ ] Successfully generates a structured JSON file for a hackathon episode.
- [ ] The JSON output follows the specified narrative flow (Intro -> R1 -> Community -> R2 -> Final Score).
- [ ] AI-generated dialogue is coherent, concise, and matches judge personas.
- [ ] The JSON output contains all necessary data and specific graphic cues for rendering.
- [ ] Can generate episodes for single or multiple projects.
- [ ] The process is entirely self-contained and does not affect other systems.

## Dependencies
- Projects must be in `completed` status in `hackathon.db` (output of Issue #006)
- OpenRouter API key for dialogue generation

## References
- Episode format ideas in `hackathon-show-config.md`
- Hackathon database schema in `001-setup-hackathon-database.md`
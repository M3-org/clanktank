# Implement Round 2 Synthesis for Final Scoring

## Overview
Implement the Round 2 synthesis logic within `hackathon_manager.py`. This will aggregate community feedback from `hackathon.db` and combine it with the initial AI judge scores to produce a final, comprehensive evaluation and a definitive final score.

## Background
Round 2 is where the AI judges' technical analysis meets community sentiment. This synthesis step is crucial for producing a balanced final score that reflects both expert opinion and user appeal. The logic will be self-contained within the hackathon scripts.

## Requirements

### Synthesis Logic
1. **Fetch Community Feedback**: For each project with a `status = 'community-voting'`, query the `community_feedback` table in `hackathon.db` to get all reaction data.
2. **Calculate Community Bonus**: Aggregate the total number of reactions for each project. The project with the most reactions receives a 2.0 point bonus. All other projects receive a bonus proportional to their total reaction count relative to the maximum.
3. **Generate Round 2 Prompts**: Create new, context-rich prompts for each of the four AI judges. These prompts will include:
   - The project's submission and research data.
   - The judge's own Round 1 scores and notes.
   - A quantitative summary of the community feedback (vote counts per category) and the calculated bonus.
4. **Get Final AI Verdicts**: Send the Round 2 prompts to the AI model. The goal is not to re-score the four criteria, but to get a final, synthesized paragraph of text from each judge explaining their final verdict, considering the community's input.
5. **Calculate Final Score**: The final score is the sum of the judge's weighted Round 1 score and the calculated community bonus.
6. **Store Final Data**:
   - Update the `hackathon_scores` table with the final verdict text and the community bonus applied.
   - Update the submission's status from `community-voting` to `completed` in the `hackathon_submissions` table.

### Tasks
- [ ] Add functions to `hackathon_manager.py` for Round 2 logic.
- [ ] Implement logic to fetch and aggregate community feedback by counting votes per category.
- [ ] Implement the community bonus calculation based on total reactions.
- [ ] Create a robust Round 2 prompt generation logic that presents a judge with their R1 score and the community's feedback.
- [ ] Integrate with OpenRouter to get final text verdicts from AI judges.
- [ ] Implement final score calculation (Round 1 weighted score + community bonus).
- [ ] Update database tables with final verdicts, scores, and status.
- [ ] Add command-line interface to trigger Round 2 synthesis.

## Technical Details

### Command Line Usage
```bash
# Run Round 2 synthesis for a specific project
python scripts/hackathon/hackathon_manager.py --synthesize --submission-id <id>

# Run for all projects ready for synthesis
python scripts/hackathon/hackathon_manager.py --synthesize --all
```

### Community Bonus Calculation Logic
```python
# In hackathon_manager.py
def calculate_community_bonus(all_projects_feedback):
    # Find the maximum total reaction count among all projects
    max_reactions = 0
    for project_id, feedback in all_projects_feedback.items():
        total_reactions = len(feedback)
        if total_reactions > max_reactions:
            max_reactions = total_reactions
    
    # Calculate bonus for each project, proportional to the max
    project_bonuses = {}
    for project_id, feedback in all_projects_feedback.items():
        total_reactions = len(feedback)
        if max_reactions > 0:
            bonus = (total_reactions / max_reactions) * 2.0
        else:
            bonus = 0.0
        project_bonuses[project_id] = bonus
        
    return project_bonuses
```

### Example Round 2 Prompt
```python
# In prompts/judge_personas.py
def create_round2_prompt(judge_name, r1_notes, community_summary):
    return f\"\"\"
    You are {judge_name}. In Round 1, you provided the following analysis:
    ---
    {r1_notes}
    ---

    Now, consider the community's feedback.
    
    **Community Vote Tally:**
    - Innovation & Creativity (💡): {community_summary.get('innovation_creativity', 0)} votes
    - Technical Execution (💻): {community_summary.get('technical_execution', 0)} votes
    - Market Potential (📈): {community_summary.get('market_potential', 0)} votes
    - User Experience (😍): {community_summary.get('user_experience', 0)} votes
    - General Hype (🔥): {community_summary.get('hype', 0)} votes
    - Calculated Community Bonus: {community_summary.get('bonus_score', 0.0):.2f} / 2.00

    **Your Task:**
    Based on the community's reaction, provide your final, synthesized verdict. Do you stand by your initial assessment, or does the community's feedback change your perspective? For instance, if they loved the user experience but you didn't, address that disconnect. Your final score from Round 1 will stand, but this is your chance to provide the final word.
    \"\"\"
```

## Files to Modify
- `scripts/hackathon/hackathon_manager.py`
- `scripts/hackathon/prompts/judge_personas.py` (for Round 2 prompts)

## Acceptance Criteria
- [ ] Successfully aggregates community feedback from the database
- [ ] Generates final verdicts from AI judges that acknowledge community input
- [ ] Correctly calculates the final score by adding the community bonus
- [ ] Updates all relevant tables in `hackathon.db` with the final results
- [ ] Updates the project status to `completed`
- [ ] Operates independently of any Clank Tank systems

## Dependencies
- Projects must be in `community-voting` status (output of Issue #005)
- OpenRouter API key must be configured

## References
- Round 2 process description in `hackathon-show-config.md`
- Hackathon database schema in `001-setup-hackathon-database.md`
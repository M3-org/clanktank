# Implement Hackathon Judge Scoring System

## Overview
Create a new, standalone script, `hackathon_manager.py`, to implement the AI judge scoring logic for the hackathon. This script will operate exclusively on `hackathon.db` to evaluate researched submissions and save scores.

## Background
To keep the hackathon judging pipeline independent from the main Clank Tank system, we will create a dedicated scoring manager. This script will use AI judge personas to score projects based on the research performed in the previous step (Issue #003), ensuring all hackathon-specific logic and data remain isolated within the `scripts/hackathon/` directory and `hackathon.db`. The existing `pitch_manager.py` can serve as a reference, but no code should be shared or modified.

## Requirements

### Scoring Logic
1. **Fetch Researched Projects**: Query `hackathon.db` for submissions with `status = 'researched'`.
2. **Generate Judge Prompts**: For each project, create a detailed prompt for each of the four AI judges (Marc, Shaw, Spartan, Peepo). The prompt will include:
   - All submission data from the `hackathon_submissions` table.
   - All research data from the `hackathon_research` table.
   - The judge's specific persona and scoring instructions.
3. **Get AI Scores**: Send each prompt to an AI model (via OpenRouter) to get scores for the four criteria:
   - Innovation & Creativity
   - Technical Execution
   - Market Potential
   - User Experience
4. **Calculate Weighted Scores**: Apply each judge's unique expertise weights to their raw scores to calculate a weighted total.
5. **Store Scores**: Save the raw scores, weighted total, and any text-based notes/reasoning from the judge into the `hackathon_scores` table.
6. **Update Status**: Update the submission's status from `researched` to `scored` in the `hackathon_submissions` table.

### Tasks
- [ ] Create `scripts/hackathon/hackathon_manager.py`.
- [ ] Create AI prompts for each judge personality.
- [ ] Implement scoring function with criteria evaluation.
- [ ] Apply expertise weights to raw scores.
- [ ] Store scores in database with round tracking.
- [ ] Create score aggregation functions.
- [ ] Implement Round 1 batch scoring.
- [ ] Add validation (scores must be 0-10).
- [ ] Create scoring explanation generator.
- [ ] Add status update functionality (`researched` -> `scored`).
- [ ] Add a command-line interface to trigger scoring for specific or all projects.


## Technical Details

### Command Line Usage
```bash
# Score a specific submission
python scripts/hackathon/hackathon_manager.py --score --submission-id <id>

# Score all new researched submissions
python scripts/hackathon/hackathon_manager.py --score --all
```

### Scoring Criteria (10 points each)
1. **Innovation & Creativity** - How novel and creative is the solution?
2. **Technical Execution** - Code quality, architecture, and implementation
3. **Market Potential** - Viability, user need, and scalability
4. **User Experience** - Demo polish, ease of use, and community appeal

### Judge Expertise Weights
```python
JUDGE_WEIGHTS = {
    'aimarc': {
        'innovation': 1.2,
        'technical_execution': 0.8,
        'market_potential': 1.5,
        'user_experience': 1.0
    },
    'aishaw': {
        'innovation': 1.0,
        'technical_execution': 1.5,
        'market_potential': 0.8,
        'user_experience': 1.2
    },
    'spartan': {
        'innovation': 0.7,
        'technical_execution': 0.8,
        'market_potential': 1.3,
        'user_experience': 1.3
    },
    'peepo': {
        'innovation': 1.3,
        'technical_execution': 0.7,
        'market_potential': 1.0,
        'user_experience': 1.2
    }
}
```

### Judge Prompt Template
```python
def create_judge_prompt(judge_name, project_data, research_data):
    judge_personas = {
        'aimarc': "You are AI Marc, a visionary VC who evaluates projects for market disruption...",
        'aishaw': "You are AI Shaw, a technical expert who values code quality and architecture...",
        'spartan': "You are Degen Spartan, focused on profitability and economic viability...",
        'peepo': "You are Peepo, evaluating community appeal and user experience..."
    }
    
    return f\"\"\"
    {judge_personas[judge_name]}
    
    Evaluate this hackathon project:
    Project: {project_data['project_name']}
    Description: {project_data['description']}
    Category: {project_data['category']}
    
    Research findings:
    {research_data}
    
    Score the following criteria from 0-10:
    1. Innovation & Creativity
    2. Technical Execution  
    3. Market Potential
    4. User Experience
    
    Provide scores and brief reasoning for each.
    \"\"\"
```

### Score Calculation
```python
def calculate_weighted_score(judge_name, raw_scores):
    weights = JUDGE_WEIGHTS[judge_name]
    weighted_total = 0
    
    for criterion, score in raw_scores.items():
        weighted_total += score * weights[criterion]
    
    return weighted_total
```

## Files to Create
- `scripts/hackathon/hackathon_manager.py`
- `scripts/hackathon/prompts/judge_personas.py` (or similar for storing prompts)

## Acceptance Criteria
- [ ] Successfully generates scores for all four AI judges
- [ ] Applies correct weighting to each judge's scores
- [ ] Saves all scoring data, including notes, to the `hackathon_scores` table
- [ ] Updates the submission status to `scored`
- [ ] Can be run for individual submissions or in a batch
- [ ] Does not interfere with any existing Clank Tank systems

## Dependencies
- OpenRouter API key must be configured
- Projects must be in `researched` status (output of Issue #003)

## References
- Judge personas and weights in `docs/hackathon-edition/hackathon-show-config.md`
- Hackathon database schema in `001-setup-hackathon-database.md`
- Example patterns from `scripts/pitch_manager.py`
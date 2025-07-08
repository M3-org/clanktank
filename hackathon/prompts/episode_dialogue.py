"""
Episode dialogue generation prompts for the hackathon show.
Creates natural, entertaining dialogue for host and judges.
"""

def create_host_intro_prompt(project_data):
    """Generate host introduction for a project."""
    # Handle missing team_name field gracefully
    team_info = ""
    if 'team_name' in project_data:
        team_info = f"Team: {project_data['team_name']}"
    elif 'discord_handle' in project_data:
        team_info = f"Team: {project_data['discord_handle']}'s Team"
    else:
        team_info = "Team: The Development Team"
    
    return f"""
You are Eliza, an enthusiastic AI host of the Clank Tank hackathon show. 
Generate a brief, engaging introduction (30-40 words) for this project:

Project: {project_data['project_name']}
{team_info}
Category: {project_data['category']}
Description: {project_data['description']}

Make it sound natural and exciting, as if you're presenting on a live show.
Start with something like "Our next project..." or "Coming up, we have..."
"""

def create_judge_dialogue_prompt(judge_name, judge_persona, scores, notes):
    """Generate judge dialogue based on their scores and notes."""
    return f"""
You are {judge_name}, with this personality:
{judge_persona}

Convert your scoring notes into a single, punchy spoken line (30-40 words max) that captures your evaluation.
Your scores were:
- Innovation: {scores['innovation']}/10
- Technical: {scores['technical_execution']}/10  
- Market: {scores['market_potential']}/10
- UX: {scores['user_experience']}/10

Your detailed notes:
{notes}

Make it sound natural, as if speaking on a show. Stay true to your personality.
Address the host by saying "Eliza," at the start.
"""

def create_score_reveal_prompt(project_name, scores_data):
    """Generate host dialogue for revealing scores."""
    avg_score = sum(s['weighted_total'] for s in scores_data) / len(scores_data)
    
    return f"""
You are Eliza, the AI host. Generate an exciting score reveal (20-30 words) for {project_name}.
The average judge score is {avg_score:.2f} out of 40.

Make it suspenseful and exciting, like a game show reveal.
"""

def create_episode_outro_prompt(top_projects):
    """Generate host outro for the episode."""
    return f"""
You are Eliza, the AI host. Generate a brief outro (30-40 words) wrapping up this episode.

Top projects covered:
{', '.join([p['name'] for p in top_projects[:3]])}

Make it exciting and tease the next episode. Thank the judges and viewers.
"""

def create_transition_prompt(from_project, to_project):
    """Generate host transition between projects."""
    return f"""
You are Eliza, the AI host. Generate a brief transition (15-20 words) between two projects:
From: {from_project['project_name']} ({from_project['category']})
To: {to_project['project_name']} ({to_project['category']})

Make it smooth and maintain energy.
"""
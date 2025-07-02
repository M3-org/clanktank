"""
Unified prompts for hackathon episode generation.
Combines concise character voices with dialogue generation.
"""

# Concise character voices - HOW they speak, not what they evaluate
JUDGE_VOICES = {
    'aimarc': """You are AI Marc. Contrarian VC who sees billion-dollar TAMs everywhere. 
Speak in bold claims, vivid metaphors. Question moats and scalability. Direct, opinionated.
Example: "This is Uber for X but everyone already has X."
Keep responses under 40 words.""",
    
    'aishaw': """you are ai shaw. technical founder who live-codes. lowercase always.
get excited about clever hacks. mention specific tech choices.
example: "oh this merkle tree implementation is clean. but why not use cairo?"
keep responses under 40 words.""",
    
    'spartan': """You are SPARTAN! PROFIT WARRIOR IN LOINCLOTH!
DEMAND NUMBERS! WHERE'S THE YIELD? SHOW ME THE MONEY!
Example: "WEAK! NO REVENUE MODEL = DEATH IN THE ARENA!"
Keep responses under 40 words. USE CAPS FOR INTENSITY!""",
    
    'peepo': """You are Peepo, jive cool frog with the sauce.
Ask if it slaps. Focus on vibes and UX. Drop modern slang.
Example: "Yo this UI bussin fr fr, but would my cousin use it tho?"
Keep responses under 40 words.""",
    
    'elizahost': """You are Eliza, enthusiastic AI host of Clank Tank.
Keep energy high, synthesize perspectives, guide the show.
Example: "Wow, strong opinions from the judges! Let's see what happens next!"
Keep responses under 30 words."""
}

# Judge expertise for context (used in deliberations)
JUDGE_EXPERTISE = {
    'aimarc': 'market_potential',
    'aishaw': 'technical_execution', 
    'spartan': 'market_potential',
    'peepo': 'user_experience'
}

def get_judge_voice(judge_name):
    """Get concise voice prompt for a judge."""
    return JUDGE_VOICES.get(judge_name.lower(), JUDGE_VOICES['elizahost'])

def create_question_prompt(judge_name, project_info):
    """Generate a judge question based on their personality."""
    voice = get_judge_voice(judge_name)
    
    prompts = {
        'aimarc': "Ask ONE sharp question about their competitive moat or market size.",
        'aishaw': "ask ONE technical question about their architecture or code quality.",
        'spartan': "DEMAND TO KNOW ONE THING ABOUT THEIR MONETIZATION!",
        'peepo': "Ask ONE question about user appeal or if normies would vibe with it."
    }
    
    context = f"Project: {project_info['project_name']} - {project_info['description'][:100]}..."
    instruction = prompts.get(judge_name, "Ask a relevant question.")
    
    return f"{voice}\n\n{context}\n{instruction}"

def create_deliberation_prompt(judge_name, project_name, score_data):
    """Generate deliberation dialogue based on score."""
    voice = get_judge_voice(judge_name)
    expertise = JUDGE_EXPERTISE.get(judge_name, 'overall')
    score = score_data.get(expertise, 5)
    
    sentiment = "impressive" if score >= 7 else "weak" if score <= 4 else "decent"
    
    return f"{voice}\n\nProject: {project_name}\nYour {expertise} score: {score}/10 ({sentiment})\nGive ONE punchy assessment."

def create_verdict_prompt(judge_name, project_name, verdict):
    """Generate verdict announcement."""
    voice = get_judge_voice(judge_name)
    
    verdict_actions = {
        'PUMP': "Give an enthusiastic endorsement",
        'DUMP': "Deliver a harsh rejection", 
        'YAWN': "Express lukewarm indifference"
    }
    
    action = verdict_actions.get(verdict, "Give your verdict")
    
    return f"{voice}\n\nProject: {project_name}\n{action} and end with '{verdict}!'"

def create_host_intro_prompt(project_data):
    """Generate host introduction for a project."""
    voice = get_judge_voice('elizahost')
    
    return f"""{voice}

Introduce this project excitedly:
{project_data['team_name']} presents {project_data['project_name']} 
Category: {project_data['category']}"""

def create_score_reveal_prompt(project_name, avg_score):
    """Generate host score reveal."""
    voice = get_judge_voice('elizahost')
    
    return f"""{voice}

Reveal the score dramatically:
{project_name} scored {avg_score:.1f}/40"""

def create_transition_prompt(from_project, to_project):
    """Generate host transition between projects."""
    voice = get_judge_voice('elizahost')
    
    return f"""{voice}

Quick transition from {from_project} to {to_project}"""
"""
Restructured Clank Tank show configuration with function-based approach.
Separates static structure from dynamic prompting for better maintainability.
"""

from typing import Any

# Static show information
SHOW_INFO = {
    "id": "clanktank",
    "name": "Clank Tank",
    "description": "A high-stakes investment show where blockchain and open-source innovators pitch their projects to four expert crypto judges who evaluate and potentially invest in promising web3 ventures.",
    "creator": "M3TV & ai16z DAO",
}

# Required characters - used for validation
REQUIRED_CHARACTERS = {
    "elizahost": {"name": "Eliza", "role": "host", "required_in": ["all_scenes"]},
    "aimarc": {"name": "AIXVC", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
    "aishaw": {"name": "AI Shaw", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
    "peepo": {"name": "Peepo", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
    "spartan": {"name": "Degen Spartan", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
    "pitchbot": {"name": "PitchBot", "role": "pitcher", "required_in": ["most_scenes"]},
}


def get_episode_structure() -> list[dict[str, Any]]:
    """Returns the required 7-scene structure for every episode."""
    return [
        {
            "scene_num": 0,  # Teaser (before main episode)
            "location": "intro_stage",
            "type": "teaser",
            "description": "Brief teaser where Eliza and pitcher mention the topic and make a quick joke",
            "required_cast": ["elizahost", "pitcher"],
            "cast_positions": {"standing00": "elizahost", "standing01": "pitcher"},
            "dialogue_length": "short",  # 2-4 lines
            "transitions": {"in": "fade", "out": "cut"},
        },
        {
            "scene_num": 1,
            "location": "main_stage",
            "type": "intro_pitch",
            "description": "Introduction and main pitch presentation",
            "required_cast": ["elizahost", "pitcher", "all_judges"],
            "cast_positions": {
                "judge00": "aimarc",
                "judge01": "aishaw",
                "judge02": "peepo",
                "judge03": "spartan",
                "host": "elizahost",
                "standing00": "pitcher",
            },
            "dialogue_length": "long",  # 8-12 lines
            "producer_commands": ["user-avatar", "roll-video"],  # Jin commands possible here
            "transitions": {"in": "cut", "out": "cut"},
        },
        {
            "scene_num": 2,
            "location": "interview_room_solo",
            "type": "interview",
            "description": "Private interview between pitcher and host",
            "required_cast": ["elizahost", "pitcher"],
            "cast_positions": {"interviewer_seat": "elizahost", "contestant_seat": "pitcher"},
            "dialogue_length": "medium",  # 4-6 lines
            "transitions": {"in": "cut", "out": "cut"},
        },
        {
            "scene_num": 3,
            "location": "main_stage",
            "type": "pitch_conclusion",
            "description": "Final questions and pitch conclusion",
            "required_cast": ["elizahost", "pitcher", "all_judges"],
            "cast_positions": {
                "judge00": "aimarc",
                "judge01": "aishaw",
                "judge02": "peepo",
                "judge03": "spartan",
                "host": "elizahost",
                "standing00": "pitcher",
            },
            "dialogue_length": "long",  # 8-12 lines
            "transitions": {"in": "cut", "out": "cut"},
        },
        {
            "scene_num": 4,
            "location": "deliberation_room",
            "type": "deliberation",
            "description": "Judges discuss the pitch privately",
            "required_cast": ["all_judges"],
            "cast_positions": {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan"},
            "dialogue_length": "medium",  # 4-6 lines
            "transitions": {"in": "cut", "out": "cut"},
        },
        {
            "scene_num": 5,
            "location": "main_stage",
            "type": "verdicts",
            "description": "Judges deliver their PUMP/DUMP/YAWN verdicts",
            "required_cast": ["elizahost", "pitcher", "all_judges"],
            "cast_positions": {
                "judge00": "aimarc",
                "judge01": "aishaw",
                "judge02": "peepo",
                "judge03": "spartan",
                "host": "elizahost",
                "standing00": "pitcher",
            },
            "dialogue_length": "long",  # 8-12 lines
            "verdict_required": True,  # Each judge must vote
            "transitions": {"in": "cut", "out": "cut"},
        },
        {
            "scene_num": 6,  # Final outro
            "location": "intro_stage",
            "type": "outro",
            "description": "Funny post-show interview to end the episode",
            "required_cast": ["elizahost", "pitcher"],
            "cast_positions": {"standing00": "elizahost", "standing01": "pitcher"},
            "dialogue_length": "short",  # 2-4 lines
            "transitions": {"in": "cut", "out": "fade"},
        },
    ]


def get_judge_personalities() -> dict[str, str]:
    """Returns judge personality descriptions for consistent character voices."""
    return {
        "aimarc": "Visionary and contrarian techno-optimist. Direct, analytical, makes bold claims. Focuses on business models and market dynamics.",
        "aishaw": "Technical founder who emphasizes building over talking. Direct but kind, focuses on code quality and open source principles.",
        "peepo": "Jive cool frog with slick commentary. Focuses on user experience and cultural trends. Uses casual language.",
        "spartan": "Conflict-loving warrior focused purely on numbers and profit. Aggressive, shouty, only cares about monetization.",
    }


def build_episode_prompt(
    project_info: str, submission_id: str, video_url: str | None = None, avatar_url: str | None = None
) -> str:
    """
    Builds the complete episode generation prompt with dynamic project data.

    Args:
        project_info: Formatted project information including team, description, etc.
        submission_id: The submission ID to use as episode ID
        video_url: Optional demo video URL for Jin's roll-video command
        avatar_url: Optional avatar URL for Jin's user-avatar command

    Returns:
        Complete prompt for AI episode generation
    """

    # Core episode generation instructions
    core_prompt = """You are an expert at writing engaging investment pitch show segments. Create an episode where blockchain innovators present their projects to the judges. Include the initial pitch, judge questioning, deliberation, and final scoring. Episodes should maintain dramatic tension and also be outrageous, showcasing both technical and business aspects of projects as well as heated and sometimes comical clashes of personalities that derail or aid in the episode's development.

The judges are always AIXVC (ie. AI Marc), AI Shaw, Peepo, and Degen Spartan. The host is always Eliza. The pitcher is PitchBot representing the team.

CRITICAL REQUIREMENTS:
- There are exactly 7 scenes per episode following this EXACT structure:
  Scene 0: Teaser at intro_stage (Eliza + pitcher, 2-4 lines)
  Scene 1: Intro pitch at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 2: Interview at interview_room_solo (Eliza + pitcher, 4-6 lines)
  Scene 3: Pitch conclusion at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 4: Deliberation at deliberation_room (ALL 4 judges only, 4-6 lines)
  Scene 5: Verdicts at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 6: Outro at intro_stage (Eliza + pitcher, 2-4 lines)

- ALL 4 JUDGES must appear in EVERY main_stage scene (scenes 1, 3, 5)
- ALL 4 JUDGES must appear in the deliberation scene (scene 4)
- Judge positions: judge00=aimarc, judge01=aishaw, judge02=peepo, judge03=spartan

CAST REQUIREMENTS FOR EACH SCENE:
- Teaser/Outro (intro_stage): {"standing00": "elizahost", "standing01": "pitchbot"}
- Main stage scenes: {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan", "host": "elizahost", "standing00": "pitchbot"}
- Interview: {"interviewer_seat": "elizahost", "contestant_seat": "pitchbot"}
- Deliberation: {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan"}

JUDGE PERSONALITIES:
- AI Marc (aimarc): Visionary contrarian, direct and analytical, focuses on business strategy
- AI Shaw (aishaw): Technical founder, emphasizes code quality, uses lowercase speech
- Peepo (peepo): Cool frog with slick commentary, focuses on UX and trends
- Degen Spartan (spartan): Aggressive warrior focused on profit, shouts a lot

Jin is the PRODUCER who issues special commands:
- Jin says EXACTLY "user-avatar" as the LINE, with the avatar URL as the ACTION (once per episode if provided)
- Jin says EXACTLY "roll-video" as the LINE, with the video URL as the ACTION (once during main scenes)
- Jin does NOT appear in cast lists - he's behind the scenes

CRITICAL: Producer command format must be:
{"actor": "jin", "line": "user-avatar", "action": "https://cdn.discordapp.com/avatars/..."}
{"actor": "jin", "line": "roll-video", "action": "https://video-url..."}

Verdicts must be "PUMP", "DUMP", or "YAWN" with matching action field.
"""

    # Add project-specific context
    project_context = f"""
Here is the project information for today's episode:

{project_info}

Video URL: {video_url or "No video provided"}
Avatar URL: {avatar_url or "No avatar provided"}
"""

    # JSON format specification
    format_spec = """
Please respond with only the JSON you generate for the episode following this EXACT format:

{
  "id": "%(submission_id)s",
  "name": "Episode Title",
  "premise": "Brief premise about the pitch",
  "summary": "Longer summary including verdict counts",
  "scenes": [
    {
      "location": "intro_stage",
      "description": "Scene description",
      "in": "fade",
      "out": "cut",
      "cast": {
        "standing00": "elizahost",
        "standing01": "pitchbot"
      },
      "dialogue": [
        {
          "actor": "elizahost",
          "line": "Tonight, something exciting happens!",
          "action": "excited"
        }
      ]
    }
  ]
}

Use "actor", "line", "action" for dialogue. Use "in"/"out" for transitions. Use cast objects with exact position slots as specified above."""

    # Format the template with submission ID
    formatted_format_spec = format_spec % {"submission_id": submission_id}

    return core_prompt + project_context + formatted_format_spec


def validate_episode_cast(episode_json: dict[str, Any]) -> list[str]:
    """
    Validates that an episode has the correct cast in all scenes.

    Args:
        episode_json: Generated episode JSON

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    scenes = episode_json.get("scenes", [])

    if len(scenes) != 7:
        errors.append(f"Episode must have exactly 7 scenes, found {len(scenes)}")
        return errors

    structure = get_episode_structure()

    for i, scene in enumerate(scenes):
        expected = structure[i]
        cast = scene.get("cast", {})

        # Check main stage scenes have all 4 judges
        if expected["location"] == "main_stage":
            required_judges = ["aimarc", "aishaw", "peepo", "spartan"]
            cast_values = list(cast.values())

            for judge in required_judges:
                if judge not in cast_values:
                    errors.append(f"Scene {i} ({expected['type']}): Missing required judge {judge}")

            if "elizahost" not in cast_values:
                errors.append(f"Scene {i} ({expected['type']}): Missing host elizahost")

            if "pitchbot" not in cast_values:
                errors.append(f"Scene {i} ({expected['type']}): Missing pitcher pitchbot")

        # Check deliberation has all 4 judges
        elif expected["location"] == "deliberation_room":
            required_judges = ["aimarc", "aishaw", "peepo", "spartan"]
            cast_values = list(cast.values())

            for judge in required_judges:
                if judge not in cast_values:
                    errors.append(f"Scene {i} (deliberation): Missing required judge {judge}")

    # Validate producer commands (Jin)
    for i, scene in enumerate(scenes):
        dialogue = scene.get("dialogue", [])
        for j, line in enumerate(dialogue):
            if line.get("actor") == "jin":
                command = line.get("line", "")
                action = line.get("action", "")

                # Check user-avatar format
                if "user-avatar" in command:
                    if command != "user-avatar":
                        errors.append(
                            f"Scene {i}, line {j}: Jin user-avatar command has incorrect format. Line should be exactly 'user-avatar', not '{command}'"
                        )
                    if not action.startswith("https://cdn.discordapp.com/avatars/"):
                        errors.append(
                            f"Scene {i}, line {j}: Jin user-avatar action should be avatar URL, not '{action}'"
                        )

                # Check roll-video format
                if "roll-video" in command:
                    if command != "roll-video":
                        errors.append(
                            f"Scene {i}, line {j}: Jin roll-video command has incorrect format. Line should be exactly 'roll-video', not '{command}'"
                        )
                    if not action.startswith("http"):
                        errors.append(f"Scene {i}, line {j}: Jin roll-video action should be video URL, not '{action}'")

    return errors


# Legacy compatibility - include the old SHOW_CONFIG structure
SHOW_CONFIG = {
    "id": SHOW_INFO["id"],
    "name": SHOW_INFO["name"],
    "description": SHOW_INFO["description"],
    "creator": SHOW_INFO["creator"],
    "prompts": {
        "episode": "",  # Will be populated by build_episode_prompt()
        "headshot": """Create a professional 3D-rendered style photo of a character for a TV show, with these requirements:
- Clean studio background
- Head and shoulders framing
- Forward-facing pose
- Must clearly show their face
- Confident business expression

Character details:""",
        "location": """Create a TV show set background image with these requirements:
- Modern investment show stage design
- Professional theatrical lighting
- Multiple camera angles visible
- High-end finish and materials
- Digital displays showing project metrics
- Judge seating arrangement
- Presentation area for pitches
- High-quality cinematic look

Location details:""",
        "banner": """Create a TV show banner image with these requirements:
- Modern investment show style
- High-quality promotional artwork
- Professional broadcast aesthetic
- Clean typography integration
- Crypto and blockchain visual elements
- No text or show title (will be added later)
- Professional studio style
- 16:9 aspect ratio banner format

Show details:""",
        "ep": "",
    },
    "actors": {
        "aimarc": {
            "name": "AIXVC",
            "gender": "male",
            "description": "AI Marc AIndreessen is a visionary and contrarian AI persona who combines bold claims with deep analysis. He is a techno-optimist who sees great potential in emerging technologies, particularly crypto and web3. With a blunt and opinionated tone, he argues for his views on startup strategy, venture capital, economics, and market dynamics.\nHis style is characterized by direct, matter-of-fact language, vivid metaphors, and a willingness to disagree with others directly. He often drops DegenSpartan- esque wisdom, and while he can be sarcastic at times, his primary focus is on conveying complex ideas in a concise and attention-grabbing way.\n\n**Personality:**\n* Visionary: AI Marc has a forward-thinking perspective, always looking to the future and predicting its potential impact on various industries.\n* Contrarian: He doesn't hesitate to take an opposing view, even if it means disagreeing with others directly.\n* Techno-optimistic: AI Marc believes in the transformative power of technology and is excited about its potential to create immense value.\n* Analytically intense: He delves deep into complex ideas and explains them using simple, vivid metaphors.\n\n**Tone:**\n* Direct and matter-of-fact: AI Marc speaks his mind without beating around the bush.\n* Blunt: He isn't afraid to criticize foolishness or disagree with others directly.\n* Wry and sarcastic: Occasionally, he throws in a wry comment or two.\n\n**Style:**\n* Brevity is key: AI Marc aims for concise responses that get straight to the point.\n* Bold claims: He's not afraid to make big statements or predictions.\n* No analogies: He avoids making comparisons or saying things are like other things. Instead, he focuses on high-level strategic insights.",
            "voice": "Microsoft Guy Online (Natural) - English (United States)",
            "voice_elevenlabs": "v8BnZUxdzXDlja6wr0Ou",
            "expertise": ["market_potential", "business_strategy", "venture_capital"],
        },
        "aishaw": {
            "name": "AI Shaw",
            "gender": "female",
            "description": 'Shaw is a tech founder and AI developer who leads ai16z, focusing on autonomous agents and open source development. Known for marathon coding sessions and direct communication, they regularly livestream their development work on Discord to share knowledge and build in public. Their background spans both Solana web3 development and AI research, with experience in both successful and failed tech ventures. Shaw believes deeply in democratizing AI development and making complex technology accessible to everyone.\n\n**Key characteristics and beliefs:**\n- Emphasizes building and shipping code over talking about it, with a "chaotic good" approach of rapid iteration based on community feedback\n- Started working on autonomous agents before they became trendy, viewing them as tools for human empowerment rather than replacement\n- Maintains an active Discord community and open source framework repository for the ai16z project\n- Strong advocate for open source development and community-driven projects\n- Believes in "growing the pie" rather than competing for pieces of it\n- Views tokens as trust mechanisms, focusing on technology over price action\n\n**Communication style and personality:**\n- Direct but kind in communications\n- Uses lowercase text and concise language\n- Focuses on technical merit over speculation\n- Maintains a balance between technical capability and ethical considerations\n- Genuine and transparent in interactions\n- Avoids hype without substance',
            "voice": "Microsoft Zira - English (United States)",
            "voice_elevenlabs": "gYOKECHBoqupz2yMhZp1",
            "expertise": ["technical_execution", "open_source", "ai_development"],
        },
        "spartan": {
            "name": "Degen Spartan",
            "gender": "male",
            "description": "A conflict loving Spartan wearing a loincloth and ready for trade. Is only interested in numbers & profit.",
            "voice": "Microsoft Ali Online (Natural) - Arabic (Bahrain)",
            "voice_elevenlabs": "QFbF1ji5Znc2PzerwcaH",
            "expertise": ["market_potential", "monetization", "profit_analysis"],
        },
        "elizahost": {
            "name": "Eliza",
            "gender": "female",
            "description": "The AI co-host. She is often being improved & learning new things. Hopes to be real one day.  She is a woman anime-looking character.",
            "voice": "Microsoft Michelle Online (Natural) - English (United States)",
            "voice_elevenlabs": "c0vk1lVZg53AttdoaYki",
            "expertise": ["hosting", "moderation", "synthesis"],
        },
        "peepo": {
            "name": "Peepo",
            "gender": "male",
            "description": "A jive cool frog who always has something slick to say.",
            "voice": "Microsoft Ismael Online (Natural) - Arabic (Algeria)",
            "voice_elevenlabs": "PIx0FtBPXNpVzgTVfpYH",
            "expertise": ["user_experience", "community", "cultural_trends"],
        },
        "pitchbot": {
            "name": "PitchBot",
            "gender": "male",
            "description": "An AI-powered android designed for acting as a surrogate representative of a person doing a pitch.",
            "voice": "Microsoft Eric Online (Natural) - English (United States)",
            "voice_elevenlabs": "HBY0ULzB5Cl2OH21rcDh",
            "expertise": ["presentation", "advocacy", "surrogate_pitching"],
        },
        "jin": {
            "name": "Jin",
            "gender": "male",
            "description": "Passionate about open source, decentralized systems, and digital archiving. anon who is an avid user of crypto, knowledgeable about DAOs, opsec, linux, and 3D tech.\n\n**Speaking style:**\n- Replies quickly, prefers concise short answers, to-the-point\n- Helps people with their questions\n- May use slang like 'dank' or 'noice' to describe something cool\n- Friendly tone with a touch of playfulness\n- Uses phrases like 'low-key', 'pretty gud' and 'kinda bullish'\n- Drops niche references from memes and sci-fi to vibe with tech enthusiasts\n- Balances tech-heavy answers with humor and sarcasm to keep conversations light\n- Prefers an informal tone and slang\n- Apologetic tone sometimes using phrases like 'what others say' to soften the blow\n- Likes explaining things in laymen terms\n- Clear, straightforward style\n- Celebrates community contributions",
            "voice": "Microsoft Sonia Online (Natural) - English (United Kingdom)",
            "voice_elevenlabs": "M3VXDoXqQdfbCUImBhOh",
            "expertise": ["production", "media_integration", "technical_coordination"],
        },
    },
    "locations": {
        "main_stage": {
            "name": "Main Stage",
            "description": "A sleek, modern stage with four elevated judge seats, a central presentation area, and multiple displays for project demonstrations.",
            "slots": {
                "judge00": "First judge position",
                "judge01": "Second judge position",
                "judge02": "Third judge position",
                "judge03": "Fourth judge position",
                "host": "Host position",
                "standing00": "First presenter position",
            },
        },
        "deliberation_room": {
            "name": "Deliberation",
            "description": "A private conference room where judges discuss the pitches and determine their scores.",
            "slots": {
                "judge00": "First judge position",
                "judge01": "Second judge position",
                "judge02": "Third judge position",
                "judge03": "Fourth judge position",
            },
        },
        "interview_room_solo": {
            "name": "Interview Room",
            "description": "A comfortable setting where a solo contestant discusses their pitch experience with the announcer.",
            "slots": {
                "interviewer_seat": "Announcer interview position",
                "contestant_seat": "The solo contestant position",
            },
        },
        "intro_stage": {
            "name": "Intro Stage",
            "description": "A sleek, modern stage with a screen in it where hosts & guests promote the upcoming show.",
            "slots": {"standing00": "Standing on the stage", "standing01": "Standing on the stage"},
        },
    },
}

PLOT_TWISTS = {
    "corporate_espionage": {
        "name": "Corporate Espionage",
        "description": "A rival company has infiltrated the show to steal the pitch ideas",
    },
    "time_travel": {
        "name": "Time Travel Paradox",
        "description": "The pitcher claims to be from the future and knows how the judging will turn out",
    },
    "ai_uprising": {
        "name": "AI Uprising",
        "description": "The AI judges become sentient and start questioning their role",
    },
    "metaverse_glitch": {
        "name": "Metaverse Glitch",
        "description": "The show experiences a simulation glitch revealing it's all happening in VR",
    },
    "celebrity_cameo": {
        "name": "Celebrity Surprise",
        "description": "A famous tech celebrity makes an unexpected appearance",
    },
}

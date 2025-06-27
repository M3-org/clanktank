# Central manifest for all hackathon submission fields and schemas (versioned)

# List of supported versions
SUBMISSION_VERSIONS = ["v1", "v2"]
LATEST_SUBMISSION_VERSION = "v2"

# Versioned field lists
SUBMISSION_FIELDS = {
    "v1": [
        "project_name",
        "team_name",
        "description",
        "category",
        "discord_handle",
        "twitter_handle",
        "github_url",
        "demo_video_url",
        "live_demo_url",
        "logo_url",
        "tech_stack",
        "how_it_works",
        "problem_solved",
        "coolest_tech",
        "next_steps",
        # Note: Do not include contact_email here as it is not on the form
    ],
    "v2": [
        "project_name",
        "team_name",
        "description",
        "category",
        "discord_handle",
        "twitter_handle",
        "github_url",
        "demo_video_url",
        "live_demo_url",
        "image_url",
        "tech_stack",
        "how_it_works",
        "problem_solved",
        "favorite_part",
        "test_field",
    ],
}

# Versioned detailed schemas (for API and dynamic frontend)
SUBMISSION_SCHEMA = {
    "v1": [
        # (You can add a detailed schema for v1 if needed)
    ],
    "v2": [
        {
            "name": "project_name",
            "label": "Project Name",
            "type": "text",
            "required": True,
            "placeholder": "My Awesome Project",
            "maxLength": 100,
        },
        {
            "name": "team_name",
            "label": "Team Name",
            "type": "text",
            "required": True,
            "placeholder": "The A-Team",
            "maxLength": 100,
        },
        {
            "name": "category",
            "label": "Category",
            "type": "select",
            "required": True,
            "options": [
                "DeFi",
                "AI/Agents",
                "Gaming",
                "Infrastructure",
                "Social",
                "Other",
            ],
            "placeholder": "Select a category",
        },
        {
            "name": "description",
            "label": "Project Description",
            "type": "textarea",
            "required": True,
            "placeholder": "A short, clear description of what your project does.",
            "maxLength": 2000,
        },
        {
            "name": "github_url",
            "label": "GitHub URL",
            "type": "url",
            "required": True,
            "placeholder": "https://github.com/...",
        },
        {
            "name": "demo_video_url",
            "label": "Demo Video URL",
            "type": "url",
            "required": True,
            "placeholder": "https://youtube.com/...",
        },
        {
            "name": "live_demo_url",
            "label": "Live Demo URL",
            "type": "url",
            "required": False,
            "placeholder": "https://my-project.com",
        },
        {
            "name": "logo_url",
            "label": "Project Logo URL",
            "type": "url",
            "required": False,
            "placeholder": "https://my-project.com/logo.png",
        },
        {
            "name": "tech_stack",
            "label": "Tech Stack",
            "type": "textarea",
            "required": False,
            "placeholder": "e.g., React, Python, Solidity,...",
        },
        {
            "name": "how_it_works",
            "label": "How It Works",
            "type": "textarea",
            "required": False,
            "placeholder": "Explain the technical architecture and how the components work together.",
        },
        {
            "name": "problem_solved",
            "label": "Problem Solved",
            "type": "textarea",
            "required": False,
            "placeholder": "What problem does your project solve?",
        },
        {
            "name": "coolest_tech",
            "label": "What's the most impressive part of your project?",
            "type": "textarea",
            "required": False,
            "placeholder": "Describe the most impressive technical aspect or feature.",
        },
        {
            "name": "next_steps",
            "label": "Next Steps",
            "type": "textarea",
            "required": False,
            "placeholder": "What are your future plans for this project?",
        },
        {
            "name": "discord_handle",
            "label": "Discord Handle",
            "type": "text",
            "required": True,
            "placeholder": "username#1234",
            "pattern": r"^.+#\\d{4}$|^.+$",  # username#1234 or just username
            "helperText": "Format: username#1234 or just username",
        },
        {
            "name": "twitter_handle",
            "label": "X (Twitter) Handle",
            "type": "text",
            "required": False,
            "placeholder": "@username",
        },
    ]
}

# Helper functions

def get_latest_version():
    return LATEST_SUBMISSION_VERSION

def get_fields(version):
    if version == "latest":
        version = get_latest_version()
    return SUBMISSION_FIELDS[version]

def get_schema(version):
    if version == "latest":
        version = get_latest_version()
    return SUBMISSION_SCHEMA[version] 
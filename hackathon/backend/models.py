"""Pydantic models for the Hackathon API."""

from typing import Any

from pydantic import BaseModel, create_model

from hackathon.backend.schema import get_fields


class SubmissionSummary(BaseModel):
    submission_id: int
    project_name: str
    category: str
    status: str
    created_at: str
    avg_score: float | None = None
    judge_count: int | None = None
    project_image: str | None = None
    description: str | None = None
    discord_handle: str | None = None
    # Add Discord user info
    discord_id: str | None = None
    discord_username: str | None = None
    discord_discriminator: str | None = None
    discord_avatar: str | None = None
    twitter_handle: str | None = None


class SubmissionDetail(BaseModel):
    submission_id: int
    project_name: str
    category: str
    description: str
    status: str
    created_at: str
    updated_at: str
    github_url: str | None = None
    demo_video_url: str | None = None
    project_image: str | None = None
    problem_solved: str | None = None
    favorite_part: str | None = None
    scores: list[dict[str, Any]] | None = None
    research: dict[str, Any] | None = None
    avg_score: float | None = None
    solana_address: str | None = None
    discord_handle: str | None = None
    # Add Discord user info for detail view
    discord_id: str | None = None
    discord_username: str | None = None
    discord_avatar: str | None = None
    community_score: float | None = None  # Add community score field
    can_edit: bool | None = None
    is_creator: bool | None = None
    twitter_handle: str | None = None


# Dynamically create the SubmissionCreate models from versioned manifests
submission_fields_v1 = {field: (str | None, None) for field in get_fields("v1")}
SubmissionCreateV1 = create_model("SubmissionCreateV1", **submission_fields_v1)

# Update SubmissionCreateV2 model to match new schema
submission_fields_v2 = {
    "project_name": (str | None, None),
    "discord_handle": (str | None, None),  # owner/creator
    "category": (str | None, None),
    "description": (str | None, None),
    "twitter_handle": (str | None, None),
    "github_url": (str | None, None),
    "demo_video_url": (str | None, None),
    "project_image": (str | None, None),
    "problem_solved": (str | None, None),
    "favorite_part": (str | None, None),
    "solana_address": (str | None, None),  # optional
}
SubmissionCreateV2 = create_model("SubmissionCreateV2", **submission_fields_v2)


class LeaderboardEntry(BaseModel):
    rank: int
    submission_id: int
    project_name: str
    category: str
    final_score: float
    community_score: float | None = None  # Add community score field
    youtube_url: str | None = None
    status: str
    discord_handle: str | None = None
    # Add these fields for avatar and linking
    discord_id: str | None = None
    discord_username: str | None = None
    discord_avatar: str | None = None


# Define a model for the submission schema field
class SubmissionFieldSchema(BaseModel):
    name: str
    label: str
    type: str
    required: bool
    placeholder: str = None
    maxLength: int = None
    options: list[str] = None
    pattern: str = None
    helperText: str = None


# Enhanced submission schema response with window information
class SubmissionSchemaResponse(BaseModel):
    fields: list[SubmissionFieldSchema]
    submission_window_open: bool
    submission_deadline: str | None = None
    current_time: str


# Define a model for stats
class StatsModel(BaseModel):
    total_submissions: int
    by_status: dict
    by_category: dict
    updated_at: str


# Feedback response models
class FeedbackItem(BaseModel):
    reaction_type: str
    emoji: str
    name: str
    vote_count: int
    voters: list[str]


class FeedbackSummary(BaseModel):
    submission_id: int
    total_votes: int
    feedback: list[FeedbackItem]


# Discord OAuth models
class DiscordUser(BaseModel):
    discord_id: str
    username: str
    discriminator: str | None = None
    avatar: str | None = None
    roles: list[str] | None = None


class DiscordAuthResponse(BaseModel):
    user: DiscordUser
    access_token: str


class DiscordCallbackRequest(BaseModel):
    code: str


class LikeDislikeRequest(BaseModel):
    submission_id: int
    action: str  # "like" or "dislike" or "remove"


class LikeDislikeResponse(BaseModel):
    likes: int
    dislikes: int
    user_action: str | None = None  # "like", "dislike", or None

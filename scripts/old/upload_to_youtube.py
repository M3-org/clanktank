#!/usr/bin/env python3

import argparse
import httplib2
import os
import random
import sys
import time
import json # For loading .env.json if used

# The google-api-python-client and oauth2client libraries are typically installed via pip
# For example: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


# --- Configuration ---
# These can be overridden by command-line arguments or environment variables

# Default path for client secrets. Can be overridden by --client-secrets or YOUTUBE_CLIENT_SECRETS_PATH env var
DEFAULT_CLIENT_SECRETS_FILE = "client_secrets.json"
# Default path for storing OAuth2 credentials. Can be overridden by --credentials-storage or YOUTUBE_CREDENTIALS_PATH env var
DEFAULT_CREDENTIALS_FILE = "youtube_credentials.json"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Retry logic (can be kept as is from the original sample)
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError) # Simplified for modern httplib2
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


def load_env_vars(env_path='.env.json'):
    """Loads environment variables from a .env.json file if it exists."""
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                env_config = json.load(f)
            for key, value in env_config.items():
                os.environ[key] = str(value) # Ensure env values are strings
            print(f"Loaded environment variables from {env_path}")
        except Exception as e:
            print(f"Warning: Could not load or parse {env_path}: {e}")

def get_authenticated_service(args):
    """
    Authenticates with the YouTube API using OAuth 2.0.
    Prioritizes environment variables for non-interactive flows (e.g., GitHub Actions).
    Falls back to local file-based flow for interactive sessions.
    """
    creds = None

    # CI/CD Flow (GitHub Actions) - using environment variables for credentials
    env_client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    env_client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    env_refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if env_client_id and env_client_secret and env_refresh_token:
        print("Attempting authentication using environment variables (CI/CD mode).")
        creds = Credentials(
            None, # No access token initially, will be fetched using refresh_token
            refresh_token=env_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env_client_id,
            client_secret=env_client_secret,
            scopes=[YOUTUBE_UPLOAD_SCOPE]
        )
        # If the credentials have a refresh token, they are likely valid or can be refreshed.
        # A refresh is attempted automatically by the google-auth library when a request is made if the token is expired.
        # We can explicitly try to refresh here if needed for an early check, but often not necessary.
        if creds.expired and creds.refresh_token:
            try:
                print("Refreshing access token via environment credentials...")
                creds.refresh(Request())
                print("Access token refreshed successfully via environment credentials.")
            except Exception as e:
                print(f"Error refreshing token via environment credentials: {e}. Upload may fail.")
                # Depending on strictness, could exit here or let the API call fail
    else:
        print("Environment variables for CI/CD mode not fully set. Attempting local file-based OAuth flow.")
        # Local Interactive Flow (using files)
        credentials_file = args.credentials_storage
        client_secrets_file = args.client_secrets
        if os.path.exists(credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(credentials_file, [YOUTUBE_UPLOAD_SCOPE])
            except Exception as e:
                print(f"Warning: Could not load credentials from {credentials_file}: {e}. Will attempt to re-authorize.")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("Refreshing access token from local file...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh token from local file: {e}. Need to re-authorize.")
                    creds = None 
            if not creds:
                if not os.path.exists(client_secrets_file):
                    print(f"ERROR: OAuth 2.0 client secrets file not found at {client_secrets_file}")
                    sys.exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, [YOUTUBE_UPLOAD_SCOPE])
                print(f"Attempting local authorization. A browser window should open.")
                creds = flow.run_local_server(port=0)
            
            try:
                with open(credentials_file, 'w') as token_file:
                    token_file.write(creds.to_json())
                print(f"Credentials saved to {credentials_file}")
            except Exception as e:
                print(f"Error saving credentials to {credentials_file}: {e}")

    if not creds:
        print("ERROR: Failed to obtain authentication credentials.")
        sys.exit(1)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)


def initialize_upload(youtube, args):
    """
    Initializes and performs the video upload process.
    """
    tags_list = None
    if args.tags:
        tags_list = [tag.strip() for tag in args.tags.split(',') if tag.strip()] # Ensure clean tags

    video_metadata_body = {
        'snippet': {
            'title': args.title,
            'description': args.description,
            'tags': tags_list,
            'categoryId': args.category_id
        },
        'status': {
            'privacyStatus': args.privacy_status,
            'selfDeclaredMadeForKids': False # Defaulting to False, adjust if needed
        }
    }
    
    print(f"\n--- Uploading Video ---")
    print(f"File: {args.video_file}")
    print(f"Title: {args.title}")
    # print(f"Description: {args.description}") # Can be very long
    print(f"Tags: {tags_list}")
    print(f"Category ID: {args.category_id}")
    print(f"Privacy Status: {args.privacy_status}")

    try:
        media_body = MediaFileUpload(args.video_file, chunksize=-1, resumable=True)
    except Exception as e:
        print(f"Error creating MediaFileUpload for {args.video_file}: {e}")
        return None

    insert_request = youtube.videos().insert(
        part=",".join(video_metadata_body.keys()),
        body=video_metadata_body,
        media_body=media_body
    )

    video_id = resumable_upload(insert_request)

    if video_id and args.thumbnail_file:
        if os.path.exists(args.thumbnail_file):
            try:
                print(f"\n--- Uploading Thumbnail ---")
                print(f"Thumbnail: {args.thumbnail_file} for video ID: {video_id}")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(args.thumbnail_file)
                ).execute()
                print("Thumbnail successfully uploaded.")
            except HttpError as e:
                print(f"An HTTP error {e.resp.status} occurred while uploading thumbnail:\n{e.content}")
            except Exception as e:
                 print(f"An error occurred while uploading thumbnail: {e}")
        else:
            print(f"\nWARNING: Thumbnail file specified but not found at {args.thumbnail_file}. Skipping thumbnail upload.")
    elif video_id and not args.thumbnail_file:
        print("\nNo thumbnail file specified. Skipping thumbnail upload.")
    
    return video_id


def resumable_upload(request):
    """
    Performs a resumable upload, with retries for transient errors.
    """
    response = None
    error_details = None
    retry_count = 0
    video_id = None

    while response is None:
        try:
            print(f"Uploading chunk (attempt {retry_count + 1}/{MAX_RETRIES + 1})...")
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    video_id = response['id']
                    print(f"Video id '{video_id}' was successfully uploaded.")
                else:
                    print(f"The upload failed with an unexpected response: {response}")
                    return None 
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error_details = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
            else:
                print(f"A non-retriable HTTP error {e.resp.status} occurred:\n{e.content}")
                raise 
        except tuple(RETRIABLE_EXCEPTIONS) as e: 
            error_details = f"A retriable error occurred: {e}"
        except Exception as e: 
            print(f"An unexpected error occurred during upload: {e}")
            raise 

        if error_details:
            print(error_details)
            retry_count += 1
            if retry_count > MAX_RETRIES:
                print("Exceeded maximum number of retries. Upload failed.")
                return None 

            max_sleep = 2**retry_count
            sleep_seconds = random.uniform(0, max_sleep) # Use random.uniform for float sleep
            print(f"Sleeping for {sleep_seconds:.2f} seconds before retrying...")
            time.sleep(sleep_seconds)
            error_details = None 
    return video_id


def main():
    load_env_vars() # Load .env.json first

    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    
    parser.add_argument("--video-file", 
                        default=os.environ.get('YOUTUBE_VIDEO_FILE'),
                        required=not bool(os.environ.get('YOUTUBE_VIDEO_FILE')),
                        help="Path to the video file to upload. Required if YOUTUBE_VIDEO_FILE env var is not set.")
    parser.add_argument("--title", 
                        default=os.environ.get('YOUTUBE_TITLE', "Default YouTube Title"), 
                        help="Title of the YouTube video. Defaults to 'Default YouTube Title' or YOUTUBE_TITLE env var.")
    parser.add_argument("--description", 
                        default=os.environ.get('YOUTUBE_DESCRIPTION', "Default description."), 
                        help="Description of the YouTube video. Defaults to 'Default description.' or YOUTUBE_DESCRIPTION env var.")
    parser.add_argument("--tags", 
                        default=os.environ.get('YOUTUBE_TAGS', ""), 
                        help="Comma-separated list of tags for the video. Can also be set via YOUTUBE_TAGS env var.")
    parser.add_argument("--category-id", 
                        default=os.environ.get('YOUTUBE_CATEGORY_ID', "22"), 
                        help="Numeric YouTube video category ID (e.g., 22 for People & Blogs). Can also be set via YOUTUBE_CATEGORY_ID env var.")
    parser.add_argument("--privacy-status", 
                        choices=["public", "private", "unlisted"], 
                        default=os.environ.get('YOUTUBE_PRIVACY_STATUS', "private"), 
                        help="Privacy status of the video. Defaults to 'private' or YOUTUBE_PRIVACY_STATUS env var.")
    parser.add_argument("--thumbnail-file", 
                        default=os.environ.get('YOUTUBE_THUMBNAIL_FILE'),
                        help="Path to the thumbnail image for the video (optional). Can also be set via YOUTUBE_THUMBNAIL_FILE env var.")
    parser.add_argument("--client-secrets",
                        default=os.environ.get('YOUTUBE_CLIENT_SECRETS_PATH', DEFAULT_CLIENT_SECRETS_FILE),
                        help=f"Path to client_secrets.json. Defaults to '{DEFAULT_CLIENT_SECRETS_FILE}' or YOUTUBE_CLIENT_SECRETS_PATH env var.")
    parser.add_argument("--credentials-storage",
                        default=os.environ.get('YOUTUBE_CREDENTIALS_LOCAL_PATH', DEFAULT_CREDENTIALS_FILE),
                        help=f"Path to store/load OAuth2 credentials for local interactive runs. Defaults to '{DEFAULT_CREDENTIALS_FILE}' or YOUTUBE_CREDENTIALS_LOCAL_PATH env var.")
    
    args = parser.parse_args()

    if not args.video_file:
        print("ERROR: --video-file argument or YOUTUBE_VIDEO_FILE environment variable is required and was not found.")
        sys.exit(1)
    if not os.path.exists(args.video_file):
        print(f"ERROR: Video file not found at {args.video_file}")
        sys.exit(1)
    if args.thumbnail_file and not os.path.exists(args.thumbnail_file):
        print(f"WARNING: Thumbnail file specified ('{args.thumbnail_file}') but not found. Proceeding without thumbnail upload.")
        args.thumbnail_file = None 

    print("--- YouTube Uploader Initializing ---")
    if not os.environ.get('YOUTUBE_CLIENT_ID'): # Heuristic: if no direct env vars, probably local mode
        print(f"Using Client Secrets Path: {os.path.abspath(args.client_secrets)}")
        print(f"Using Credentials Storage Path (for local flow): {os.path.abspath(args.credentials_storage)}")

    try:
        youtube = get_authenticated_service(args)
        if youtube:
            initialize_upload(youtube, args)
            print("\n--- YouTube Upload Process Finished ---")
        else:
            print("Could not get authenticated YouTube service. Upload aborted.")
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
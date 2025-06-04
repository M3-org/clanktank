#!/usr/bin/env python3

import argparse
import httplib2
import os
import random
import sys
import time
import json
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

DEFAULT_CLIENT_SECRETS_FILE = "client_secrets.json"
DEFAULT_CREDENTIALS_FILE = "youtube_credentials.json"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

def load_env_vars():
    dotenv_path = Path('.env')
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        print("Loaded environment variables from .env")
    json_env_path = Path('.env.json')
    if json_env_path.exists():
        try:
            with open(json_env_path, 'r') as f:
                env_config = json.load(f)
            for key, value in env_config.items():
                os.environ[key] = str(value)
            print(f"Loaded environment variables from {json_env_path}")
        except Exception as e:
            print(f"Warning: Could not load or parse {json_env_path}: {e}")

def get_authenticated_service(args):
    creds = None
    env_client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    env_client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    env_refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if env_client_id and env_client_secret and env_refresh_token:
        print("Using environment credentials (CI/CD mode).")
        creds = Credentials(
            None,
            refresh_token=env_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env_client_id,
            client_secret=env_client_secret,
            scopes=[YOUTUBE_UPLOAD_SCOPE]
        )
        try:
            creds.refresh(Request())
            print("Access token refreshed successfully.")
        except Exception as e:
            print(f"Error refreshing token via environment credentials: {e}")
            sys.exit(1)
    else:
        print("Falling back to local OAuth flow (interactive mode).")
        credentials_file = args.credentials_storage
        client_secrets_file = args.client_secrets
        if os.path.exists(credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(credentials_file, [YOUTUBE_UPLOAD_SCOPE])
            except Exception:
                creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                if not os.path.exists(client_secrets_file):
                    print(f"Missing client secrets file: {client_secrets_file}")
                    sys.exit(1)
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, [YOUTUBE_UPLOAD_SCOPE])
                creds = flow.run_local_server(port=0)
            with open(credentials_file, 'w') as token_file:
                token_file.write(creds.to_json())

    if not creds:
        print("ERROR: Failed to obtain credentials.")
        sys.exit(1)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

def update_thumbnail(youtube, video_id, thumbnail_path):
    if not os.path.exists(thumbnail_path):
        print(f"ERROR: Thumbnail file not found at {thumbnail_path}")
        return
    print(f"Updating thumbnail for video ID: {video_id}")
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print("Thumbnail updated successfully.")
    except HttpError as e:
        print(f"HTTP error {e.resp.status}:\n{e.content}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def initialize_upload(youtube, args):
    tags_list = [tag.strip() for tag in args.tags.split(',') if tag.strip()] if args.tags else None
    video_metadata_body = {
        'snippet': {
            'title': args.title,
            'description': args.description,
            'tags': tags_list,
            'categoryId': args.category_id
        },
        'status': {
            'privacyStatus': args.privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    print(f"Uploading: {args.video_file} | Title: {args.title}")
    try:
        media_body = MediaFileUpload(args.video_file, chunksize=-1, resumable=True)
    except Exception as e:
        print(f"Error reading video file: {e}")
        return None

    insert_request = youtube.videos().insert(
        part=','.join(video_metadata_body.keys()),
        body=video_metadata_body,
        media_body=media_body
    )
    video_id = resumable_upload(insert_request)
    if video_id and args.thumbnail_file and os.path.exists(args.thumbnail_file):
        update_thumbnail(youtube, video_id, args.thumbnail_file)
    return video_id

def resumable_upload(request):
    response, error_details = None, None
    retry_count, video_id = 0, None

    while response is None:
        try:
            print(f"Uploading chunk (attempt {retry_count + 1})...")
            status, response = request.next_chunk()
            if response and 'id' in response:
                video_id = response['id']
                print(f"Upload complete. Video ID: {video_id}")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error_details = f"Retriable HTTP error {e.resp.status}:\n{e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error_details = f"Retriable error: {e}"
        except Exception as e:
            raise

        if error_details:
            print(error_details)
            retry_count += 1
            if retry_count > MAX_RETRIES:
                print("Max retries exceeded.")
                return None
            time.sleep(random.uniform(0, 2 ** retry_count))
            error_details = None
    return video_id

def main():
    load_env_vars()

    parser = argparse.ArgumentParser(description="Upload or update a video/thumbnail on YouTube.")
    parser.add_argument("--video-file", default=os.environ.get('YOUTUBE_VIDEO_FILE'),
                        help="Path to the video file to upload.")
    parser.add_argument("--title", default=os.environ.get('YOUTUBE_TITLE', "Default Title"))
    parser.add_argument("--description", default=os.environ.get('YOUTUBE_DESCRIPTION', "Default description."))
    parser.add_argument("--tags", default=os.environ.get('YOUTUBE_TAGS', ""))
    parser.add_argument("--category-id", default=os.environ.get('YOUTUBE_CATEGORY_ID', "22"))
    parser.add_argument("--privacy-status", choices=["public", "private", "unlisted"],
                        default=os.environ.get('YOUTUBE_PRIVACY_STATUS', "private"))
    parser.add_argument("--thumbnail-file", default=os.environ.get('YOUTUBE_THUMBNAIL_FILE'))
    parser.add_argument("--update-thumbnail-for",
                        help="If set, updates the thumbnail for an existing video ID.")
    parser.add_argument("--client-secrets", default=os.environ.get('YOUTUBE_CLIENT_SECRETS_PATH', DEFAULT_CLIENT_SECRETS_FILE))
    parser.add_argument("--credentials-storage", default=os.environ.get('YOUTUBE_CREDENTIALS_LOCAL_PATH', DEFAULT_CREDENTIALS_FILE))

    args = parser.parse_args()

    if args.update_thumbnail_for:
        if not args.thumbnail_file:
            print("ERROR: --thumbnail-file is required with --update-thumbnail-for.")
            sys.exit(1)
        youtube = get_authenticated_service(args)
        update_thumbnail(youtube, args.update_thumbnail_for, args.thumbnail_file)
        return

    if not args.video_file:
        print("ERROR: --video-file is required unless updating thumbnail.")
        sys.exit(1)
    if not os.path.exists(args.video_file):
        print(f"ERROR: Video file not found at {args.video_file}")
        sys.exit(1)

    if args.thumbnail_file and not os.path.exists(args.thumbnail_file):
        print(f"WARNING: Thumbnail not found at {args.thumbnail_file}. Skipping.")
        args.thumbnail_file = None

    youtube = get_authenticated_service(args)
    initialize_upload(youtube, args)
    print("Done.")

if __name__ == "__main__":
    main()

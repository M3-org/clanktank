# Create Hackathon YouTube Upload Pipeline

## Overview
Create a new script, `hackathon_youtube_uploader.py`, to handle the upload of recorded hackathon episodes to YouTube with appropriate metadata pulled from `hackathon.db`.

## Background
We need an automated way to publish the final hackathon episode videos. To keep things separate, we'll create a dedicated uploader script that sources all its information from the hackathon database and recordings directory, without touching the existing Clank Tank YouTube pipeline.

## Requirements

### Upload Process
1. **Fetch Recorded Episodes**: The script will scan the `recordings/hackathon/` directory for new video files that have not yet been uploaded.
2. **Gather Metadata**: For each video, it will parse the filename to get the `submission_id` and query `hackathon.db` to retrieve all necessary metadata:
   - **Title**: e.g., "Clank Tank Hackathon: Judging 'Project Name'"
   - **Description**: A detailed description including the project's one-liner, a link to its GitHub, the final score, and judge verdicts.
   - **Tags**: Relevant tags like "hackathon", "AI judging", the project's category (e.g., "DeFi"), and tech stack.
3. **Generate Thumbnail**: The script should be able to select or generate a thumbnail for the video (e.g., using the project's logo from the submission).
4. **Upload to YouTube**: Use the YouTube Data API to upload the video file with the prepared metadata and thumbnail.
5. **Update Status**: After a successful upload, update the project's status in the `hackathon_submissions` table to `published` and store the YouTube video URL.

### Tasks
- [ ] Create `scripts/hackathon/hackathon_youtube_uploader.py`
- [ ] Implement logic to find new videos in `recordings/hackathon/`
- [ ] Add function to query `hackathon.db` for video metadata
- [ ] Create dynamic generation for YouTube titles, descriptions, and tags
- [ ] Integrate YouTube Data API for video upload
- [ ] Add thumbnail generation/selection logic
- [ ] Add logic to update the status to `published` and save the video URL
- [ ] Implement a tracking mechanism (e.g., a simple log file or DB table) to avoid re-uploading videos

## Technical Details

### YouTube Metadata Generation
```python
# In scripts/hackathon/hackathon_youtube_uploader.py
def generate_metadata(submission_id):
    # 1. Query hackathon_submissions, hackathon_scores tables
    # ...
    
    title = f"Clank Tank Hackathon: Judging '{project_data['project_name']}'"
    
    description = f"""
{project_data['description']}

    Check out the project on GitHub: {project_data['github_url']}

    Final Score: {final_score}

    Judge Verdicts:
    - AI Marc: "{marc_verdict}"
    - AI Shaw: "{shaw_verdict}"
    - ...
    """
    
    tags = ['hackathon', 'clank tank', 'ai judging', project_data['category']]
    
    return {'title': title, 'description': description, 'tags': tags}
```

## Files to Create
- `scripts/hackathon/hackathon_youtube_uploader.py`

## Acceptance Criteria
- [ ] Successfully uploads recorded hackathon videos to YouTube
- [ ] Populates the title, description, and tags with data from `hackathon.db`
- [ ] Sets a custom thumbnail for the video
- [ ] Updates the project status to `published` in the database
- [ ] Stores the final YouTube URL back in the database
- [ ] Does not re-upload videos that are already published
- [ ] The existing Clank Tank YouTube upload script is unaffected

## Dependencies
- YouTube Data API credentials (client_secrets.json, etc.) must be configured
- Recorded video files must be present in `recordings/hackathon/` (output of Issue #008)

## References
- Example patterns from `scripts/clanktank/upload_to_youtube.py`
- Google API Python Client and YouTube Data API documentation
- Hackathon database schema in `001-setup-hackathon-database.md`
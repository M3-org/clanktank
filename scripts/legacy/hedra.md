# Hedra CLI

A command-line interface for the Hedra API to create digital avatars and talking heads.

## Features

- **Character Generation**: Create digital avatars from images and audio
- **Voice Management**: List and preview voices (from API or local files)
- **Project Management**: List, view, share, and delete your Hedra projects
- **Interactive Mode**: Step-by-step guided workflow

## Installation

### Prerequisites

- Python 3.6+
- `requests` library (`pip install requests`)
- Audio player (optional): ffplay, mpg123, or mplayer (for voice preview)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/hedra-labs/hedra-cli.git
   cd hedra-cli
   ```

2. Make the script executable:
   ```bash
   chmod +x hedra
   ```

3. Configure your API key:
   ```bash
   ./hedra config --api-key YOUR_API_KEY
   ```

## Usage

### Character Generation

Generate a talking avatar with text-to-speech:
```bash
./hedra generate --text "Hello world!" --img portrait.jpg --voice-id <voice_id>
```

Generate with an uploaded audio file:
```bash
./hedra generate --audio-file audio.wav --img portrait.jpg
```

Generate a character with an AI-created image:
```bash
./hedra generate --text "Hello world" --voice-id <voice_id> --img-prompt "A professional woman with glasses"
```

### Voice Management

List available voices:
```bash
./hedra voice list
```

Preview a voice by ID or name:
```bash
./hedra voice preview <voice_id_or_name>
```

### Project Management

List your recent projects:
```bash
./hedra project list
```

Get project details:
```bash
./hedra project get <project_id>
```

Download a project's output:
```bash
./hedra project download <project_id> --output my_video.mp4
```

Share a project:
```bash
./hedra project share <project_id>
```

Delete a project:
```bash
./hedra project delete <project_id>
```

### Interactive Mode

For a guided experience:
```bash
./hedra interactive
```

## Using Local Voice Files

The client can use voice files in the `assets` folder for previews:

1. Put your voice samples in the `assets` directory (e.g., `assets/Laura.mp3`)
2. When listing voices, those with matching local files will be marked with ✓ in the LOCAL column
3. Use `hedra voice preview Laura` to play the local file directly

You can set a custom assets directory:
```bash
./hedra config --assets-dir /path/to/your/voices
```

## Examples with Sample Assets

The repository includes sample assets that can be used:

```bash
# Generate with 16:9 aspect ratio
./hedra generate --audio-file assets/audio.wav --img assets/16_9.jpg --aspect-ratio 16:9

# Generate with 9:16 aspect ratio
./hedra generate --audio-file assets/audio.wav --img assets/9_16.jpg --aspect-ratio 9:16

# Preview a voice from the assets folder
./hedra voice preview Alice
```

## Advanced Options

### Aspect Ratio

Specify the aspect ratio of the output video:
```bash
./hedra generate --text "Hello" --voice-id <voice_id> --img <path> --aspect-ratio 16:9
```

### Seed for Reproducibility

Set a seed for reproducible image generation:
```bash
./hedra generate --text "Hello" --voice-id <voice_id> --img-prompt "A teacher" --seed 42
```

### Animation Prompt

Add instructions for the animation style:
```bash
./hedra generate --text "Hello" --voice-id <voice_id> --img <path> --animation-prompt "nodding and smiling"
```

### Custom Output Path

Specify where to save the generated video:
```bash
./hedra generate --text "Hello" --voice-id <voice_id> --img <path> --output my_video.mp4
```

## Limitations

- The Hedra API supports generating videos up to 4 minutes in length
- Supported aspect ratios: 1:1, 16:9, 9:16
- Image files should be in JPG or PNG format
- Audio files should be in WAV or MP3 format

## Configuration

All settings are stored in `~/.hedra.conf`:

```
api_key=your_api_key
base_url=https://mercury.dev.dream-ai.com/api
default_output_dir=outputs
assets_dir=/path/to/assets
```

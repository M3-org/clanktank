# Crossfade Video Script
A bash script that uses melt (MLT Framework) to concatenate video files with 1-second crossfades between each pair. Supports input from command-line arguments or a text file, with customizable output file.

## Requirements

- MLT Framework: Install melt (e.g., sudo apt install melt on Debian/Ubuntu).
- FFmpeg: For MP4 output encoding (usually installed with melt).

## Usage

```bash
./crossfade.sh [-i input.txt] [-o output.mp4] video1 video2 [video3 ...]
```

- `-i input.txt`: Read video files from a text file (one per line).
- `-o output.mp4`: Specify output file (default: `output.mp4`).
- `video1 video2 ...`: List video files directly (e.g., `clip1.mp4 clip2.mp4`).

## Examples

1. Command-Line Input:

```bash
./crossfade.sh Interview1.mp4 node.mp4 SPARTA_02B.mp4 -o result.mp4
```
Creates result.mp4 with crossfades.

2. Text File Input:
`videos.txt`:

```
clip1.mp4
clip2.mp4
clip3.mp4
```

```bash
./crossfade.sh -i videos.txt -o final.mp4
```

## Features
- Applies 1-second crossfades (25 frames at 25 fps) using melt’s luma transition.
- Supports any melt-compatible video format (e.g., .mp4, .mov, .mkv).
- Requires at least 2 videos.

## Notes
- Adjust `-mix 25` in the script for different fade durations (e.g., `-mix 50` for 2 seconds).
For non-25 fps videos, add `fps=30` to the `-consumer` line (e.g., `-consumer avformat:$output_file fps=30`).

---

# Shmotime Player

An automated playback and recording solution for Shmotime episodes with high-quality audio and video capture.

## Overview

Shmotime Player is a Node.js tool that automates the playback of Shmotime interactive episodes while capturing high-quality video and audio using Puppeteer and Chrome's native media capabilities. It handles the entire playback flow from launching the browser to clicking through the episode and detecting when an episode is complete.

## Features

- **Full Audio/Video Recording** - Captures both video and audio in MP4 or WebM format
- **Automatic Episode Navigation** - Handles episode loading, start buttons, and completion detection
- **Smart Viewport Control** - Ensures proper screen dimensions for consistent, high-quality recordings
- **Cross-Platform** - Works on Windows, macOS, and Linux with automatic Chrome detection
- **Configurable Options** - Flexible settings for resolution, output format, frame rate, and more
- **Headless Support** - Run in visible or headless mode (for server environments)

## Requirements

- Node.js (using v23)
- Google Chrome or Chromium browser installed
- `puppeteer-stream` package and its dependencies

## Installation

```bash
# Install dependencies
npm install
```

## Usage

### Basic Usage

```bash
node shmotime-recorder.js https://shmotime.com/shmotime_episode/your-episode-url/
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--headless` | Run in headless mode (no visible browser) |
| `--no-record` | Disable recording (playback only) |
| `--quiet` | Reduce logging verbosity |
| `--wait=TIME` | Maximum time to wait for episode to finish (in ms, default 3600000) |
| `--output=DIR` | Output directory for recordings (default ./recordings) |
| `--chrome-path=PATH` | Custom Chrome executable path |
| `--format=FORMAT` | Output format: mp4 or webm (default mp4) |
| `--width=WIDTH` | Video width in pixels (default 1920) |
| `--height=HEIGHT` | Video height in pixels (default 1080) |
| `--fps=FPS` | Frame rate (default 30) |

### Examples

Record an episode in 1080p:
```bash
node shmotime-recorder.js https://shmotime.com/shmotime_episode/the-security-sentinel/
```

Record in headless mode with custom dimensions:
```bash
node shmotime-recorder.js --headless --width=1280 --height=720 --fps=60 https://shmotime.com/shmotime_episode/your-episode/
```

Record with a custom Chrome path and output directory:
```bash
node shmotime-recorder.js --chrome-path="/usr/bin/chromium" --output=./my-recordings https://shmotime.com/shmotime_episode/your-episode/
```

## Output

Recordings are saved to the specified output directory (default: `./recordings`) with filenames in the format:
```
{show-title}-{episode-title}-{timestamp}.{format}
```

## Advanced Usage

### Using as a Library

You can also use Shmotime Player as a library in your own Node.js projects:

```javascript
const ShmotimePlayer = require('./shmotime-player');

async function recordEpisode() {
  const player = new ShmotimePlayer({
    headless: false,
    videoWidth: 1920,
    videoHeight: 1080,
    outputDir: './my-recordings'
  });
  
  try {
    await player.initialize();
    await player.loadEpisodeUrl('https://shmotime.com/shmotime_episode/your-episode/');
    await player.startEpisode();
    await player.waitForEpisodeToFinish();
  } finally {
    await player.close();
  }
}

recordEpisode().catch(console.error);
```

## Troubleshooting

### Common Issues

1. **Black bars in recording**: If you see black bars at the top/bottom of your recording, try running with `--height` slightly larger than your desired height.

2. **Audio issues**: Make sure your system audio is working. The tool automatically unmutes all audio elements.

3. **Chrome not found**: Use the `--chrome-path` option to specify your Chrome executable location.

4. **MP4 recording fails**: Some environments have issues with MP4 recording. Try using WebM format with `--format=webm`.

### Debugging

Run with more verbosity enabled to see detailed logs:

```bash
node shmotime-recorder.js --verbose https://shmotime.com/shmotime_episode/your-episode/
```

## Technical Details

Shmotime Player uses:
- **Puppeteer** - For browser automation
- **Puppeteer-stream** - For capturing browser tab content with audio
- **Chrome DevTools Protocol** - For precise window control
- **Custom CSS injection** - To ensure proper element sizing and positioning

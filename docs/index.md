# Clank Tank 🤖💰

An AI-powered game show where entrepreneurs pitch to simulated judges, competing for virtual funding and real attention.

<div align="center">
  <a href="https://m3org.com/tv/" target="_blank">Visit Official Website</a> • 
  <a href="https://tally.so/r/3X8EKO" target="_blank">Submit Your Pitch</a> •
  <a href="https://www.youtube.com/watch?v=R-oObQtsksw" target="_blank">Watch Latest Episode</a>
</div>


## About Clank Tank

Clank Tank is an autonomous entertainment platform where users submit real business pitches that are transformed into complete, simulated episodes featuring AI-generated characters, dialogue, and interactions. Inspired by "Shark Tank," our system creates entertaining show episodes that provide exposure for projects while offering AI-driven feedback.

The show features a panel of AI judges who evaluate pitches, question the presenter, and ultimately decide whether to "pump" or "dump" the project.

<iframe src="https://m3org.com/tv" width="100%" height="800px" style="border:none;"></iframe>


### Latest Episode

[Watch Episode S1E1: The AI Battle Arena](https://www.youtube.com/watch?v=R-oObQtsksw&pp=0gcJCU8JAYcqIYzv)

## How It Works

1. **Pitch Submission**: Entrepreneurs submit their project details and personal information through our [submission form](https://tally.so/r/3X8EKO)
2. **AI Simulation**: Our system creates an AI character to represent the pitcher and generates a complete episode script
3. **Real-Time Rendering**: The episode is rendered in 3D using PlayCanvas (with variants for Unity/Unreal)
4. **Publishing**: Episodes are shared via web embeds and social media clips
5. **Feedback & Exposure**: Projects gain visibility, useful critique, and potential connections to capital

## Technical Architecture

The Clank Tank system uses a modular architecture with several key components:

```
┌─────────────────┐     ┌───────────────┐     ┌─────────────────┐
│  Pitch System   │────▶│  Writers Room │────▶│ Episode Builder │
└─────────────────┘     └───────────────┘     └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                         ┌─────────────────┐
│  Human Review   │◀────────────────────────│  JSON Episode   │
└─────────────────┘                         └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                         ┌─────────────────┐
│ Video Production│◀────────────────────────│ 3D Playback     │
└─────────────────┘                         └─────────────────┘
```

## Project Structure

```
.
├── docs/               # Documentation and concept files
├── media/              # Assets for the show
│   ├── cast/           # Character images and headshots
│   ├── clips/          # Video segments (intro, outro, transitions)
│   └── thumbnails/     # Episode thumbnails and promotional images
├── scripts/            # Automation tools
│   └── shmotime-recorder.js  # Recording utility for episodes
└── README.md           # This file
```

### Core Components

1. **AI Writers' Room**: Uses Anthropic Claude to generate natural dialogue and interactions between judges and pitchers
2. **Rendering Framework**: PlayCanvas (web-based) with planned support for Unity/Unreal for higher fidelity
3. **Show Runner**: JSON-based event system that controls the flow of scenes, dialogue, and camera work
4. **Audio Pipeline**: ElevenLabs for voice synthesis plus sound effects and transitions
5. **Recording System**: Automated tools to create high-quality recordings from rendered episodes

### Running the Recorder

The repository includes a powerful recording tool for capturing high-quality videos of episodes:

```bash
# Record an episode
node scripts/shmotime-recorder.js https://shmotime.com/shmotime_episode/your-episode-url/

# For more options
node scripts/shmotime-recorder.js --help
```

---

## Season 1 Development Roadmap

### Phase 1: Production Enhancement (Current)
- [ ] Complete audio pipeline with compression/DSP for voices
- [x] Create consistent sound effect package (stingers, transitions)
- [x] Implement professional intro/outro videos
- [ ] Add buffer space between dialogue lines for better pacing
- [ ] Develop structured segment format for episodes

### Phase 2: Content Improvement
- [ ] Enhanced judge interactions with deeper questioning
- [ ] Project demo integrations (15-30 seconds each)
- [ ] Balanced episode structure with varied pitches
- [ ] Multi-agent AI writers' room

### Phase 3: Community Integration
- [ ] Audience feedback mechanisms
- [ ] Post-episode resources (PDF/webpage with project details)
- [ ] Token-based voting system
- [ ] Community submission review system
- [ ] Special guest judges from community

### Phase 4: Format Expansion
- [ ] Grant proposal reviews
- [ ] Hackathon judging
- [ ] Governance discussions
- [ ] Extended episode formats


---

*Clank Tank is an entertainment platform and does not provide financial advice. All judge decisions are simulated and do not constitute real investment offers.*

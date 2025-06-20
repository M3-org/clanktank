# Clank Tank Hackathon Edition

Welcome to the documentation for adapting Clank Tank to judge hackathons using AI-powered judges.

## Overview

Clank Tank Hackathon Edition transforms our AI-powered game show platform into an automated hackathon judging system. Projects are evaluated by our AI judges (Marc, Shaw, Spartan, and Peepo) through a two-round process that combines technical analysis with community feedback.

## Documentation Structure

### 📋 [Show Configuration](hackathon-show-config.md)
Complete guide to the hackathon adaptation including:
- Judge personalities and adaptations
- Two-round judging system
- Scoring criteria and weights
- Submission form requirements

### 🔧 Technical Implementation Options

#### [Option 1: Using Existing Infrastructure](hackathon-technical-notes-existing.md)
Leverage Clank Tank's current technology stack:
- Reuse sheet_processor.py and pitch_manager.py
- Integrate with existing AI research pipeline
- Minimal new code required

#### [Option 2: WordPress Self-Contained](hackathon-technical-notes-wordpress.md)
Build everything within WordPress + Elementor:
- Custom plugin with full integration
- ACF field management
- REST API endpoints
- Discord webhook support

### 🎨 [Creative Enhancements](hackathon-creative-notes.md)
Optional visual improvements:
- 2D composition strategies
- AI-generated backgrounds
- Props and overlay suggestions
- Interactive creative partner guide

## Quick Links

- [Project Milestones](milestones.md) - Development roadmap and GitHub issues
- [Main Clank Tank Docs](../) - Return to main documentation

## Getting Started

1. Review the [Show Configuration](hackathon-show-config.md) to understand the concept
2. Choose a technical implementation path based on your resources
3. Check the [Milestones](milestones.md) for development priorities
4. Optionally explore [Creative Enhancements](hackathon-creative-notes.md)

## Key Features

- **AI-Powered Judging**: Four distinct AI personalities evaluate projects
- **Two-Round System**: Initial technical review + community-informed final scoring  
- **Automated Research**: AI analyzes GitHub repos and project viability
- **Community Integration**: Discord reactions influence final scores
- **Flexible Implementation**: Choose between existing infrastructure or WordPress

## Contact

For questions or contributions, please check the [GitHub repository](https://github.com/m3-org/clanktank).
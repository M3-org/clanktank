# Clank Tank Hackathon Edition

*This folder contains both current (canonical) docs and legacy/reference material. See below for navigation tips.*

## How to Use These Docs
- **Start with the files listed under 'Documentation Structure' below.**
- **For deep technical specs or historical decisions, see the `archive/` subfolder.**
- **Reference docs are clearly marked as such.**
- **If in doubt, follow cross-links from the main docs to the canonical source.**

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

### 🔧 **Technical Fixes & Architecture**

#### [Schema Architecture Consolidation](schema-consolidation.md)
Complete schema management overhaul:
- Single source of truth architecture
- Eliminated schema conflicts and duplicates
- Dynamic validation generation
- Bulletproof field synchronization

#### [Image Upload Final Fix](image-upload-final-fix.md)
Root cause analysis and fix for image upload issues:
- Frontend File object handling bug
- TypeScript type corrections
- Complete validation chain fixes

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

---

## 🛠️ Documentation Cleanup & Improvement Instructions (For LLMs or Junior Devs)

### Goal
Systematically review, update, and clean up the `docs/hackathon-edition/` folder to ensure all documentation is:
- Accurate and up-to-date with the latest code and process
- Free of redundancy and outdated notes
- Easy to navigate for new contributors

### Context
- The hackathon judging system is now fully implemented and tested (see `PROGRESS.md` for a phase-by-phase summary).
- Many design decisions, format specs, and process notes are archived in `docs/hackathon-edition/archive/`.
- The scripts in `scripts/hackathon/` are the source of truth for actual implementation.
- The web dashboard and leaderboard are in `scripts/hackathon/dashboard/`.

### Step-by-Step Instructions

1. **Inventory the Docs Folder**
   - List all files in `docs/hackathon-edition/` and its subfolders.
   - Note which are current, which are legacy/archived, and which are drafts or stubs.

2. **Review Metadata and Modification Dates**
   - Use `ls -lt` or file explorer to check last modified dates.
   - Prioritize updating older files that are still referenced in the main docs or code.

3. **Cross-Reference with Archives**
   - For any spec, format, or process doc, check if a more recent or canonical version exists in `archive/`.
   - If so, merge, summarize, or link to the canonical version. Avoid duplication.

4. **Check Against Scripts**
   - For each phase (submission, research, scoring, voting, synthesis, episode generation, dashboard), open the relevant script(s) in `scripts/hackathon/`.
   - Ensure the documentation matches the actual CLI, arguments, and outputs.
   - Update examples, usage notes, and diagrams as needed.

5. **Update Index and Navigation**
   - Make sure `README.md` (this file) and `mkdocs.yml` accurately reflect the current structure and entry points.
   - Remove or archive any files that are no longer referenced or needed.

6. **Consolidate and Clarify**
   - Merge similar or redundant docs (e.g., multiple update notes) into a single, well-organized file (see `pipeline-updates.md`).
   - Use clear section headers, tables, and code blocks for readability.
   - Add cross-links between related docs (e.g., from `episode-format.md` to archived specs).

7. **Document All Major Decisions**
   - For any non-obvious design or compatibility decision, ensure there is a clear note in the relevant doc (e.g., why unified format, why Jin as surrogate, etc.).

8. **Check for Sensitive or Generated Files**
   - Ensure no sensitive credentials or large generated files are in the docs folder.
   - Reference, but do not include, files like `client_secrets.json`, `youtube_credentials.json`, or large DBs.

9. **Final Review**
   - Read through the docs as if you are a new contributor. Is everything clear? Are there any dead links or confusing sections?
   - Propose or make edits to improve clarity, accuracy, and navigation.

### Reference Points
- `PROGRESS.md` — Phase-by-phase implementation summary
- `pipeline-updates.md` — Changelog and major process notes
- `episode-format.md` — Unified episode format and compatibility
- `archive/` — Canonical specs, format references, and migration notes
- `scripts/hackathon/` — Source of truth for all hackathon logic
- `scripts/hackathon/dashboard/` — Web interface and leaderboard

### Deliverable
A clean, up-to-date, and well-organized `docs/hackathon-edition/` folder that:
- Accurately documents the current system
- Is easy for new contributors to navigate
- Clearly distinguishes between current, legacy, and reference material

---
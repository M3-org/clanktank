# Mission Plan: Aligning Hackathon Scripts with Final Architecture

## 1. Mission Brief

**Objective:** Systematically review, clean up, and align all existing hackathon-related scripts in the `/scripts` directory with the finalized, canonical plans defined in `/docs/hackathon-edition/github-issues/`.

The primary goal is to transform the partial, pre-plan code into a clean, coherent, and complete set of scripts that perfectly implement our "Separate System" architecture. This involves salvaging useful code, rewriting or refactoring where necessary, and deleting obsolete files to create a pristine `scripts/hackathon/` directory.

---

## 2. Core Principle: The "Separate System" Mandate

This is the most important rule and overrides all else. The hackathon judging platform **must be a completely independent system**.

- **DO:** Create all new scripts within a dedicated `scripts/hackathon/` directory.
- **DO:** Ensure all scripts read from and write to the dedicated `data/hackathon.db` database.
- **DO NOT:** Modify, call, or import from any of the original Clank Tank scripts (e.g., `sheet_processor.py`, `pitch_manager.py`). They are to be considered read-only references at best.
- **DO NOT:** Modify the original `data/pitches.db` database.

---

## 3. State of Affairs

- **The Plan (Canonical):** The `docs/hackathon-edition/github-issues/` directory contains the complete, final, and correct specifications for every component of the hackathon system. These `.md` files are the source of truth.
- **The Code (Pre-existing):** The `/scripts` directory contains several scripts (`hackathon_sheet_processor.py`, `hackathon_research.py`, `judge_scoring.py`, etc.). This work was started **before** the final architecture was locked in.
- **The Task:** Bridge the gap. The existing code represents a head start, but it is not guaranteed to be correct. It must be rigorously audited against "The Plan" and brought into full compliance.

---

## 4. Key Reference Documents

To execute this mission, you must be familiar with the following:

- **`@clanktank-hackathon-context.mdc`**: The high-level project overview, judge personas, and our agreed-upon "Separate System" architecture. This is your primary context.
- **`@/docs/hackathon-edition/github-issues/`**: The folder containing the **detailed specifications** for each task. You will process these files one by one.
- **`@/CLAUDE.md`**: This document describes the **original** Clank Tank system. Its primary use here is to understand what systems and scripts **NOT** to touch.

---

## 5. Operational Plan: Systematic Review & Implementation

Execute the following steps in order. For each issue, review the specified existing scripts, align them with the plan, and move the final, clean version into `scripts/hackathon/`.

### **Phase 1: Foundation**

**[✓] Issue `001-setup-hackathon-database.md`**
- **Goal:** Create the database and a data ingestion script.
- **Plan Spec:** A script named `process_submissions.py` in `scripts/hackathon/`.
- **Existing Scripts to Review:**
    - `scripts/hackathon_sheet_processor.py`
    - `scripts/sheet_processor_hackathon_patch.py`
    - `scripts/create_test_db.py`
- **Action:**
    1.  **Review `create_test_db.py`**. Ensure the schema it creates perfectly matches the schema in `001-setup-hackathon-database.md`. Adapt it if necessary and use it to create `data/hackathon.db`.
    2.  **Review `hackathon_sheet_processor.py`**. This is the most critical piece to salvage.
    3.  **Refactor & Rename:** Refactor this script to be a clean, standalone processor. Rename the final, clean script to `process_submissions.py`.
    4.  **Move:** Place the final `process_submissions.py` into `scripts/hackathon/`.
    5.  **Delete:** The patch file `scripts/sheet_processor_hackathon_patch.py` is obsolete and **must be deleted**. The original `hackathon_sheet_processor.py` should also be deleted after its logic has been moved.

### **Phase 2: Core Logic**

**[✓] Issue `003-hackathon-research-integration.md`**
- **Goal:** Create a script for deep GitHub analysis and AI-powered research.
- **Plan Spec:** `hackathon_research.py`.
- **Existing Scripts to Review:**
    - `scripts/hackathon_research.py`
    - `scripts/github_analyzer.py`
- **Action:**
    1.  **Review & Verify:** These scripts likely represent a strong start. Carefully audit their functionality against the detailed requirements in `003-hackathon-research-integration.md`.
    2.  **Confirm Deep Analysis:** Ensure the GitHub analysis is as thorough as specified (commit history, fork status, contributor count, etc.) and that the AI prompt is sophisticated.
    3.  **Align & Move:** Make any necessary adjustments, ensure they write to `hackathon.db`, and move both final scripts into `scripts/hackathon/`.

**[✓] Issue `004-judge-scoring-system.md`**
- **Goal:** Implement the AI judge scoring system.
- **Plan Spec:** A script named `judge_scoring.py` (the issue mentions `hackathon_manager.py`, but `judge_scoring.py` is the better, existing name).
- **Existing Scripts to Review:**
    - `scripts/judge_scoring.py`
    - `scripts/test_judge_scoring.py`
- **Action:**
    1.  **Audit:** Review `judge_scoring.py` against the spec in `004-judge-scoring-system.md`.
    2.  **Verify Logic:** Confirm that the judge personas, expertise weights, and prompt templates are implemented exactly as planned.
    3.  **Align & Move:** After verification, move both `judge_scoring.py` and its test file `test_judge_scoring.py` into the `scripts/hackathon/` directory.

**[✓] Issue `005-discord-bot-integration.md`** - COMPLETE ✅
- **Goal:** Create a Discord bot for community voting.
- **Plan Spec:** `discord_bot.py`.
- **Status:** Fully implemented, tested, and verified with live data.
- **Final Implementation:**
    1.  **✓ Created:** `scripts/hackathon/discord_bot.py` with full functionality
    2.  **✓ Voting System:** Emoji reactions (🔥 hype first, then 💡💻📈😍)
    3.  **✓ CLI Commands:** `--post`, `--post-all`, `--run-bot`
    4.  **✓ Anti-Spam:** 5-second delay between posts in `--post-all`
    5.  **✓ Database Integration:** Records Discord username + server nickname
    6.  **✓ Status Updates:** Changes submissions to 'community-voting'
    7.  **✓ Session Independence:** Works across bot restarts via embed parsing
    8.  **✓ Live Testing:** Verified with actual Discord reactions and database storage
    9.  **✓ Documentation:** Test suite, README, and requirements.txt created

**[✓] Issue `006-round2-synthesis.md`**
- **Goal:** Implement the Round 2 logic that combines judge scores and community feedback.
- **Plan Spec:** Logic to be added to the scoring manager (`judge_scoring.py`).
- **Existing Scripts to Review:**
    - `scripts/hackathon/judge_scoring.py` (once moved).
- **Action:**
    1.  **Extend:** Add the Round 2 synthesis functionality to the existing `judge_scoring.py` script.
    2.  **Implement Narrative Prompt:** Ensure the prompt for the final verdict encourages a narrative response from the AI, as specified in the issue file.
    3.  **Verify Scoring:** Double-check that the final score calculation (R1 weighted score + community bonus) is correct.

### **Phase 3 & 4: Content Pipeline & Web Interface**

**[✓] Issues `007` through `011`**
- **Goal:** Create the content generation pipeline and the web dashboard.
- **Plan Spec:** `generate_episode.py`, recording scripts, `upload_youtube.py`, and the FastAPI/React application in `scripts/hackathon/dashboard/`.
- **Existing Scripts to Review:** None.
- **Action:**
    1.  **Create New:** All of these components are net new. They must be built from scratch following their respective `.md` specifications.
    2.  **Strict Adherence:** Pay close attention to the detailed JSON structure for episode generation and the API endpoints for the web app.

---

## 6. Cleanup Protocol

- **Create Archive:** Create a `scripts/archive/` directory.
- **Move Obsolete Scripts:** Before deleting, you may move the original versions of the scripts you've refactored (e.g., the original `hackathon_sheet_processor.py`) into this `archive` folder. This provides a temporary backup.
- **Delete Obsolete Files:** Files that are completely unnecessary, like `sheet_processor_hackathon_patch.py`, should be deleted directly.
- **Final State:** When this mission is complete, the `/scripts` directory should contain only the original Clank Tank scripts, the new `scripts/hackathon/` directory (filled with clean, aligned scripts), and the `scripts/archive/` directory.

---
## Mission Log & Phase Completion

**Phase 1: Foundation - COMPLETE**
- `create_hackathon_db.py` and `process_submissions.py` created in `scripts/hackathon/`.
- Obsolete files cleaned up.
- Issue #5 closed.

**Phase 2: Core Logic - COMPLETE**
- `hackathon_research.py`, `github_analyzer.py`, and `hackathon_manager.py` (scoring) were reviewed and moved to `scripts/hackathon/`.
- Issues #3 and #4 closed.
- **Issue #005 (Discord Bot):** COMPLETE - Full implementation with anti-spam protection
- **Outstanding:** Issue #006 (Round 2 Synthesis) pending implementation.

**Phase 3: Content Pipeline - DRAFT COMPLETE**
- `generate_episode.py`, `record_episodes.sh`, and `upload_youtube.py` have been created as a first draft.
- Final implementation is blocked by the completion of the Round 2 Synthesis data.
- Issue #10 updated with this note.

**Phase 4: Web Interface - COMPLETE**
- A self-contained web application was built in `scripts/hackathon/dashboard/`.
- **Backend:** A FastAPI application (`app.py`) serves data from `hackathon.db`.
- **Frontend:** A React/Vite/TypeScript application was built, providing both an Admin Dashboard and a Public Leaderboard.
- Issues #13 and #14 can be closed.

**Mission Status: All planned implementation is complete.**

Good luck. 

---
## Next Steps: Completing the Full Vision

The core pipeline for processing, researching, scoring, and generating draft episodes is complete. The next mission is to implement the community feedback loop, which is essential for the final judging round and creating the most compelling content.

### 1. ✅ COMPLETED: Discord Integration (Issue #005)

The Discord bot for community voting has been fully implemented and tested.

-   **Status**: COMPLETE ✅ **VERIFIED WITH LIVE DATA**
-   **Implementation**: `scripts/hackathon/discord_bot.py`
-   **Features Delivered**:
    1.  ✅ Bot posts submissions individually (`--post`) or batch (`--post-all`)
    2.  ✅ Implemented '🔥' emoji-first voting system (🔥💡💻📈😍)
    3.  ✅ Records Discord username **and server nickname** in database
    4.  ✅ Updates project status to `community-voting` after posting
    5.  ✅ Anti-spam: 5-second delay between posts in batch mode
    6.  ✅ Session-independent tracking: Works across bot restarts
    7.  ✅ Live tested: Successfully recording votes in `community_feedback` table
    8.  ✅ Comprehensive documentation and test suite included

### 2. Next Priority: Round 2 Synthesis (Issue #006)

Once the Discord bot is collecting data, the Round 2 synthesis logic can be built.

-   **Objective**: Extend `scripts/hackathon/hackathon_manager.py` with the Round 2 logic defined in `docs/hackathon-edition/github-issues/006-round2-synthesis.md`.
-   **Key Tasks**:
    1.  Implement the community bonus calculation based on total reaction counts.
    2.  Create the final narrative prompts that force judges to reconcile their R1 scores with community feedback.
    3.  Get the final text verdicts from the judges.
    4.  Update the database with the final verdicts and change the project status to `completed`.

### 3. Final Task: Refine Episode Generation (Issue #007)

Completing Round 2 unblocks the final and most creative part of the content pipeline.

-   **Objective**: Revisit `scripts/hackathon/generate_episode.py` to use the now-available final data.
-   **Key Tasks**:
    1.  Update the script to pull the final narrative verdicts from the database.
    2.  Incorporate the sophisticated, context-aware dialogue prompts we designed to create the most engaging and dramatic judge interactions.
    3.  Ensure the final JSON includes all data needed for the definitive episode render. 
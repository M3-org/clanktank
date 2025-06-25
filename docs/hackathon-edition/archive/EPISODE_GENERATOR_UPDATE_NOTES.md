# Episode Generator Update Notes

## Goal: Full Backwards Compatibility & Hackathon Context

The `generate_episode.py` script has been significantly updated to ensure its output is **fully backwards-compatible** with the existing Clank Tank rendering pipeline, while also correctly adapting to the hackathon's unique context.

---

## Key Changes Made

### 1. Adopted the Original 5-Scene Structure

The generator now creates episodes with exactly 5 scenes, following the original Clank Tank format:

-   **Scene 1**: Introduction and main pitch (`main_stage`)
-   **Scene 2**: Interview between pitcher and host (`interview_room_solo`)
-   **Scene 3**: Conclusion of pitch with Q&A (`main_stage`)
-   **Scene 4**: Judges deliberate privately (`deliberation_room`)
-   **Scene 5**: Final PUMP/DUMP/YAWN verdicts (`main_stage`)

This ensures a consistent viewing experience and utilizes all three original show locations.

### 2. Implemented Action-Based Voting UI

Instead of a custom graphics system, the script now uses the renderer's built-in `action` system to trigger UI elements:

-   Judge dialogue now includes `"action": "PUMP"`, `"DUMP"`, or `"YAWN"`.
-   This triggers the exact voting UI seen in original episodes, simplifying the format and increasing reliability.
-   **Crucially, the scoring logic was updated to convert the judges' final weighted scores (out of 40) into these PUMP/DUMP/YAWN verdicts.** This creates the bridge between the numerical scores and the final on-screen action.

### 3. Adapted for the Hackathon Context

-   **Jin as Surrogate Pitcher**: Since hackathon teams don't present live, the script casts "Jin" as the surrogate pitcher to maintain the interactive dialogue format with the host and judges.
-   **Simplified Episode IDs**: The concept of seasons and episodes has been removed. Each episode's `id` is now taken directly from the project's `submission_id` (e.g., `test-001`), and the output filename matches (e.g., `test-001.json`).

---

## Final Usage

Generate episodes for hackathon submissions with a simple command:

```bash
# Generate an episode for a single submission
python scripts/hackathon/generate_episode.py --submission-id test-001

# Generate episodes for all scored submissions
python scripts/hackathon/generate_episode.py --all

# Specify a custom output directory
python scripts/hackathon/generate_episode.py --all --output-dir episodes/custom
```

The generated episodes will now render perfectly in the original system while maintaining all the unique aspects of the hackathon judging process.
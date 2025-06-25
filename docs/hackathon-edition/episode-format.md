# Episode Format

*This document is a consolidated summary. For full canonical specs, see the archive links below.*

This document consolidates all episode format, compatibility, and unified format notes for the hackathon judging system. It draws from the following archived documents:
- [UNIFIED_EPISODE_FORMAT.md](archive/UNIFIED_EPISODE_FORMAT.md) *(canonical spec)*
- [EPISODE_FORMAT_QUICK_REFERENCE.md](archive/EPISODE_FORMAT_QUICK_REFERENCE.md)
- [EPISODE_COMPATIBILITY_SUMMARY.md](archive/EPISODE_COMPATIBILITY_SUMMARY.md)
- [COMPATIBILITY_PLAN.md](archive/COMPATIBILITY_PLAN.md)

---

## Unified Episode Format (Backwards Compatible)

Episodes are structured as JSON with all original Clank Tank fields preserved, plus optional hackathon extensions:

```json
{
  "id": "S1E1",
  "name": "Episode Title",
  "premise": "One sentence hook",
  "summary": "Full episode description",
  "scenes": [
    {
      "location": "main_stage",
      "description": "Scene description",
      "cast": { ... },
      "dialogue": [
        { "actor": "elizahost", "line": "Welcome!", "action": "hosting" }
      ],
      "hackathon_metadata": { ... } // Optional
    }
  ],
  "hackathon_metadata": { ... } // Optional
}
```

- **All original fields are required and preserved.**
- **Hackathon features** (e.g., scores, submission IDs, bonus data) are added as `hackathon_metadata` at the root and scene level.
- **Renderer ignores unknown fields** for full compatibility.

---

## Quick Reference: Field & Character Mapping

| Original Field | Hackathon Field | Notes |
|---------------|-----------------|-------|
| id | episode_metadata.title | Direct map |
| name | episode_metadata.title | Direct map |
| scenes[] | segments[] | Different structure |
| cast | N/A | Extract from dialogue events |
| dialogue.actor | event.character | Name format differs |

**Character Name Mapping:**
| Hackathon Name | Original Name |
|---------------|---------------|
| Eliza | elizahost |
| AI Aimarc | aimarc |
| AI Aishaw | aishaw |
| Peepo | peepo |
| AI Spartan | spartan |

---

## Compatibility & Conversion
- **Unified format**: One format for both hackathon and original episodes
- **No renderer changes needed**: Original renderer ignores `hackathon_metadata`
- **Action-based UI**: Use `action` fields (e.g., "PUMP", "DUMP", "YAWN") to trigger voting overlays
- **Graphics**: Hackathon graphics (e.g., project card, scores) are mapped to overlays or scene elements

---

## Example Usage

Generate a compatible episode:
```bash
python scripts/hackathon/generate_episode.py --submission-id test-001
```

---

## See Also
- [COMPATIBILITY_PLAN.md](archive/COMPATIBILITY_PLAN.md) *(legacy/reference: detailed mapping and conversion logic)*
- [EPISODE_FORMAT_QUICK_REFERENCE.md](archive/EPISODE_FORMAT_QUICK_REFERENCE.md) *(legacy/reference: field mapping tables)*
- [UNIFIED_EPISODE_FORMAT.md](archive/UNIFIED_EPISODE_FORMAT.md) *(canonical full spec)*

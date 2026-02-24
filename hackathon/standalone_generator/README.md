# Standalone Episode Generator V2

This is a **reference implementation** of an improved, more maintainable episode generator for Clank Tank hackathon episodes.

## Key Improvements Over Original

### ✅ **Consolidated Configuration**
- All episode settings centralized in `configs/episode_config.py`
- No more scattered configuration across multiple files
- Easy to modify for different show formats

### ✅ **Clean Import Structure**
- Removed fragile `sys.path.append()` hacks
- Proper relative imports within this directory
- Self-contained with all dependencies included

### ✅ **Simplified Data Access**
- API-first approach only (no complex DB fallback)
- Clear error messages when backend is unavailable
- Reduced complexity and maintenance burden

### ✅ **Standardized Directories**
- Outputs to `episodes/hackathon/` (matching recorder expectations)
- Consistent paths throughout pipeline
- Configuration-driven directory structure

## Files Included

```
standalone_generator/
├── README.md                    # This file
├── generate_episode_v2.py       # Main generator script (improved)
└── configs/
    ├── __init__.py
    └── episode_config.py        # Consolidated configuration + embedded schema
```

**Fully self-contained!** All schema data, configuration, and dependencies are embedded in the config file.

## Usage

```bash
# From the hackathon directory
cd standalone_generator

# Generate an episode (requires backend running at localhost:8000)
python generate_episode_v2.py --submission-id ABC123

# Validate an existing episode
python generate_episode_v2.py --validate-only --episode-file episodes/hackathon/ABC123.json

# Custom output directory
python generate_episode_v2.py --submission-id ABC123 --output-dir custom/path
```

## Requirements

- Python 3.8+
- `pip install requests python-dotenv`
- Backend API running at `http://localhost:8000` (or set `config.api_base_url`)
- Environment variable: `OPENROUTER_API_KEY`

## Benefits of This Approach

1. **Future Multi-Show Support**: Configuration structure makes it easy to add new show types
2. **Maintainable**: All settings in one place, clear separation of concerns
3. **Portable**: Self-contained with no external package dependencies
4. **Safe**: Original working version is preserved unchanged
5. **Testable**: Can be developed and tested independently

## Comparison with Original

| Aspect | Original | Standalone V2 |
|--------|----------|---------------|
| Configuration | Scattered across files | Single config file |
| Imports | `sys.path.append` hack | Clean relative imports |
| Data Access | API + DB fallback | API-first only |
| Dependencies | Relies on hackathon package | Fully self-contained |
| Portability | Tied to package structure | Complete standalone |
| Multi-show Ready | No | Yes (via config) |
| Schema Management | External JSON file | Embedded in config |

## Future Enhancements

This standalone version provides the foundation for:
- Multiple show formats with different configs
- Better testing and validation
- Recording pipeline integration
- Development without affecting production

## Migration Strategy

1. Test this version thoroughly with existing submissions
2. Compare output quality with original generator
3. Once confident, can gradually replace original
4. Maintain both during transition period
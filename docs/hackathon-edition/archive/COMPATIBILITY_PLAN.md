# COMPATIBILITY PLAN

> **LEGACY/REFERENCE:** This file contains detailed mapping and migration notes. For the current summary, see [../episode-format.md](../episode-format.md).

# Hackathon Episode Compatibility Plan

## Executive Summary
This document outlines the implementation plan for making hackathon-generated episodes compatible with the existing Clank Tank rendering pipeline.

## Missing Components Analysis

### 1. Character Personas & Visual Data
**Current State**: Hackathon format only includes character names
**Original Format**: Full character definitions with models, textures, animations

**Solution**: Create character mapping file
```json
{
  "character_mappings": {
    "Eliza": {
      "full_name": "elizahost",
      "model": "models/eliza.glb",
      "default_position": "announcer_position",
      "default_action": "hosting"
    },
    "AI Aimarc": {
      "full_name": "aimarc",
      "model": "models/aimarc.glb",
      "default_position": "judge_seat_1",
      "default_action": "neutral"
    },
    "AI Aishaw": {
      "full_name": "aishaw",
      "model": "models/aishaw.glb",
      "default_position": "judge_seat_2",
      "default_action": "neutral"
    },
    "Peepo": {
      "full_name": "peepo",
      "model": "models/peepo.glb",
      "default_position": "judge_seat_3",
      "default_action": "neutral"
    },
    "AI Spartan": {
      "full_name": "spartan",
      "model": "models/spartan.glb",
      "default_position": "judge_seat_4",
      "default_action": "neutral"
    }
  }
}
```

### 2. Scene Location Mapping
**Current State**: No location information
**Original Format**: Specific locations with camera positions

**Solution**: Segment-to-scene mapping
```python
SEGMENT_SCENE_MAPPING = {
    "intro": {
        "location": "main_stage",
        "camera": "wide_shot",
        "lighting": "standard",
        "in": "fade",
        "out": "cut"
    },
    "project_review": {
        "location": "main_stage",
        "camera": "dynamic",
        "lighting": "spotlight_presenter",
        "in": "cut",
        "out": "cut"
    },
    "outro": {
        "location": "main_stage",
        "camera": "wide_shot",
        "lighting": "standard",
        "in": "cut",
        "out": "fade"
    }
}
```

### 3. Dialogue Actions
**Current State**: Plain text dialogue
**Original Format**: Actions for each line

**Solution**: Action inference system
```python
def infer_action(character, dialogue_text):
    """Infer appropriate action based on dialogue content"""
    
    # Judge scoring actions
    if any(score in dialogue_text.lower() for score in ["8 out of 10", "score", "rating"]):
        return "scoring"
    
    # Emotional reactions
    if "!" in dialogue_text and len(dialogue_text) > 50:
        return "excited"
    if "?" in dialogue_text:
        return "questioning"
    if any(word in dialogue_text.lower() for word in ["weak", "copy", "paste", "forgotten"]):
        return "critical"
    
    # Character-specific defaults
    character_defaults = {
        "elizahost": "hosting",
        "aimarc": "analytical",
        "aishaw": "skeptical",
        "peepo": "casual",
        "spartan": "intense"
    }
    
    return character_defaults.get(character.lower(), "neutral")
```

### 4. Graphics Integration
**Current State**: show_graphic events
**Original Format**: No direct graphics support

**Solution**: Graphics-to-scene converter
```python
def convert_graphic_to_scene_element(graphic_event):
    """Convert hackathon graphics to scene elements"""
    
    if graphic_event["graphic_type"] == "project_card":
        return {
            "type": "overlay",
            "asset": "ui/project_card_template.html",
            "data": graphic_event["data"],
            "duration": 5000,
            "position": "lower_third"
        }
    
    elif graphic_event["graphic_type"] == "r1_scores":
        return {
            "type": "scoreboard",
            "asset": "ui/judge_scores.html",
            "data": graphic_event["data"],
            "duration": 8000,
            "position": "fullscreen"
        }
    
    elif graphic_event["graphic_type"] == "final_score":
        return {
            "type": "celebration",
            "asset": "ui/final_score_reveal.html",
            "data": graphic_event["data"],
            "duration": 10000,
            "effects": ["confetti", "sound_fanfare"]
        }
```

## Converter Implementation

### Main Converter Class
```python
class HackathonToOriginalConverter:
    def __init__(self):
        self.character_mappings = load_character_mappings()
        self.scene_templates = load_scene_templates()
        self.project_counter = 0
        
    def convert_episode(self, hackathon_episode):
        """Convert hackathon format to original Clank Tank format"""
        
        # Extract metadata
        meta = hackathon_episode["episode_metadata"]
        
        # Build episode structure
        original_episode = {
            "id": self.generate_episode_id(meta),
            "name": meta["title"],
            "premise": self.generate_premise(meta),
            "summary": self.generate_summary(hackathon_episode),
            "scenes": []
        }
        
        # Convert each segment
        for segment in hackathon_episode["segments"]:
            scenes = self.convert_segment_to_scenes(segment)
            original_episode["scenes"].extend(scenes)
        
        return original_episode
    
    def convert_segment_to_scenes(self, segment):
        """Convert a single segment to one or more scenes"""
        
        segment_type = segment["segment_type"]
        template = self.scene_templates[segment_type]
        
        if segment_type == "project_review":
            # Complex conversion for project reviews
            return self.convert_project_review(segment, template)
        else:
            # Simple conversion for intro/outro
            return [self.convert_basic_segment(segment, template)]
```

## Testing Strategy

### 1. Unit Tests
```python
def test_character_mapping():
    """Ensure all hackathon characters map correctly"""
    converter = HackathonToOriginalConverter()
    assert converter.map_character("Eliza") == "elizahost"
    assert converter.map_character("AI Aimarc") == "aimarc"

def test_scene_generation():
    """Verify scenes generate with required fields"""
    segment = {"segment_type": "intro", "events": [...]}
    scenes = converter.convert_segment_to_scenes(segment)
    assert all(key in scenes[0] for key in ["location", "cast", "dialogue"])
```

### 2. Integration Tests
- Convert sample hackathon episode
- Validate against original schema
- Render test episodes
- Compare visual output

### 3. Performance Tests
- Conversion speed benchmarks
- Memory usage monitoring
- Batch processing capability

## Rollout Plan

### Phase 1: Core Converter (Week 1)
- [ ] Implement basic converter structure
- [ ] Add character mappings
- [ ] Create scene templates
- [ ] Basic dialogue conversion

### Phase 2: Enhanced Features (Week 2)
- [ ] Action inference system
- [ ] Graphics integration
- [ ] Timing adjustments
- [ ] Audio sync validation

### Phase 3: Production Ready (Week 3)
- [ ] Full test suite
- [ ] Performance optimization
- [ ] Documentation
- [ ] Deployment scripts

## Configuration Files Needed

### 1. `hackathon_compatibility.json`
```json
{
  "version": "1.0",
  "character_mappings": {...},
  "scene_templates": {...},
  "default_timings": {
    "dialogue_pause": 500,
    "scene_transition": 1000,
    "graphic_display": 5000
  }
}
```

### 2. `action_keywords.json`
```json
{
  "excited": ["amazing", "incredible", "wow"],
  "critical": ["weak", "poor", "lacking"],
  "thoughtful": ["interesting", "consider", "perhaps"],
  "aggressive": ["destroy", "crush", "dominate"]
}
```

## Monitoring & Validation

### Quality Metrics
- Dialogue timing accuracy
- Scene transition smoothness
- Character position consistency
- Audio/visual sync

### Error Handling
- Missing character mappings
- Invalid segment types
- Malformed graphics data
- Timing conflicts

## Future Enhancements

### Version 2.0
- AI-powered action generation
- Dynamic camera movements
- Multi-project episodes
- Judge reaction shots

### Version 3.0
- Real-time conversion API
- Preview generation
- Custom scene templates
- Advanced graphics effects

## Conclusion
This compatibility plan provides a clear path to integrate hackathon episodes with the existing Clank Tank rendering system while preserving the simplified format benefits for rapid content generation.
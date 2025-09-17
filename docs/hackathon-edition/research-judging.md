# Clank Tank Hackathon Research & Judging System

## Overview

The Clank Tank Hackathon employs a sophisticated three-phase evaluation pipeline that combines automated repository analysis, AI-powered research, and personality-based judge scoring to create comprehensive, fair, and entertaining assessments of hackathon projects.

## Phase 1: Automated Repository Analysis (`github_analyzer.py`)

### Core Functionality
The GitHub Analyzer performs deep technical analysis of each submission's repository to establish baseline quality metrics and detect potential issues.

### Two-Stage File Analysis
1. **Stage 1 - File Relevance Labeling**: Uses heuristic patterns to categorize files by relevance:
   - **High**: Core source directories (`/src/`, `/lib/`, `/contracts/`, `/cmd/`, `/app/`)
   - **Medium-High**: Source code files (`.py`, `.js`, `.ts`, `.sol`, etc.)
   - **Medium**: Config files (`package.json`, `requirements.txt`), documentation, tests
   - **Low**: Generated files, binaries, hidden files

2. **Stage 2 - GitIngest Optimization**: Employs AI-powered file selection:
   - Analyzes file manifest, dependency info, and LOC histogram
   - Uses OpenRouter + Kimi model to recommend optimal GitIngest settings
   - Generates include/exclude patterns and file size limits
   - Provides reasoning for token budget allocation

### Technical Metrics Collected
- **Repository Metadata**: Creation date, update frequency, license, contributors
- **Code Quality Indicators**: File structure, language breakdown, commit patterns
- **Development Timeline**: Commit frequency, author analysis, pre-hackathon vs hackathon activity
- **Documentation Assessment**: README quality, setup instructions, project structure
- **Dependency Analysis**: Package managers, framework choices, external dependencies

### Automated Red Flag Detection
- **Stale Repository**: Created >30 days ago with no recent updates
- **Dependency Bloat**: High ratio of large files to source code
- **Boilerplate Heavy**: More generated files than original source
- **Minimal Implementation**: Very few files indicating limited scope
- **Web Upload Commits**: Suspicious commit patterns suggesting bulk uploads

### GitIngest Integration
- **Security Validated**: Only GitHub URLs accepted, HTTPS enforced
- **Dynamic Token Limits**: Scales from 64k tokens (small repos) to 170k tokens (very large repos)
- **Content Optimization**: Uses tiktoken for accurate token counting and intelligent truncation

## Phase 2: AI-Powered Research (`research.py`)

### Research Architecture
Combines GitHub analysis with comprehensive AI research using OpenRouter + Perplexity for current market intelligence and technical assessment.

### Research Components
1. **GitHub Repository Analysis** (from Phase 1)
2. **GitIngest Code Context**: Full repository content processed through intelligent file filtering
3. **AI Market Research**: Real-time competitive analysis and market sizing via Perplexity
4. **Technical Assessment**: Architecture evaluation and implementation quality analysis

### Research Prompt Engineering
- **Critical Analysis Requirement**: AI must defend every positive claim with concrete risks/flaws
- **Hackathon Context**: Timeline-aware evaluation (30-day hackathon window)
- **Evidence-Based Scoring**: All ratings must reference specific repository data
- **Anti-Gaming Measures**: Explicitly flags common hackathon cheating patterns

### Research Output Structure
```json
{
  "technical_implementation": {
    "score": 1-10,
    "analysis": "detailed assessment",
    "red_flags": ["specific issues with evidence"]
  },
  "market_analysis": {
    "competitors": ["direct competitors found"],
    "market_size": "addressable market assessment",
    "differentiation": "unique value proposition analysis"
  },
  "innovation_rating": {
    "score": 1-10,
    "novelty_factors": ["unique technical approaches"],
    "technology_usage": "cutting-edge tech evaluation"
  },
  "overall_assessment": {
    "final_score": 1-10,
    "strengths": ["validated positive aspects"],
    "weaknesses": ["identified risks and gaps"],
    "recommendation": "judge-ready summary"
  }
}
```

### Caching & Performance
- **24-Hour Cache**: Research results cached with automatic expiry
- **Force Refresh**: Override caching for re-evaluation
- **Database Integration**: Results stored in `hackathon_research` table with versioning

## Phase 3: AI Judge Scoring (`hackathon_manager.py`)

### Judge Personality System
Four distinct AI judges with unique evaluation perspectives and scoring weights:

#### AI Marc (aimarc) - Venture Capitalist
- **Personality**: Contrarian VC who sees billion-dollar TAMs everywhere
- **Focus**: Market potential (1.5x weight), innovation (1.2x weight)
- **Style**: Bold claims, vivid metaphors, aggressive moat questioning
- **Expertise**: Business model validation, competitive positioning

#### AI Shaw (aishaw) - Technical Founder
- **Personality**: Technical founder who live-codes, lowercase communication
- **Focus**: Technical execution (1.5x weight), UX (1.2x weight)
- **Style**: Excited about clever hacks, mentions specific tech choices
- **Expertise**: Architecture decisions, code quality, scalability

#### Spartan - Profit Warrior
- **Personality**: CAPS-LOCK profit warrior in loincloth demanding yield
- **Focus**: Market potential (1.3x weight), UX (1.3x weight)
- **Style**: Aggressive monetization questioning, numbers-focused
- **Expertise**: Revenue models, tokenomics, immediate profitability

#### Peepo - Community Voice
- **Personality**: Jive cool frog with modern slang, community perspective
- **Focus**: Innovation (1.3x weight), UX (1.2x weight)
- **Style**: "Does it slap tho?", viral potential, accessibility focus
- **Expertise**: User appeal, meme potential, community adoption

### Scoring Methodology

#### Weighted Criteria (0-10 each)
- **Innovation & Creativity**: Novel solutions and creative approaches
- **Technical Execution**: Code quality, architecture, implementation soundness
- **Market Potential**: Viability, user need, scalability, market size
- **User Experience**: Demo polish, ease of use, interface design, community appeal

#### Hardened Scoring Scale
- **10**: Benchmark-setting, better than 95% of open-source projects
- **8**: Strong with minor issues only experts notice
- **6**: Adequate with clear rough edges
- **4**: Significant gaps or shortcuts
- **2**: Barely functional/mostly boilerplate
- **0**: Non-working/plagiarized/irrelevant

#### Score Processing
1. **Individual Judge Scoring**: Each judge scores all criteria independently
2. **Weighted Calculation**: Scores multiplied by judge expertise weights
3. **Normalization**: Automatic adjustment to maintain 6.0 target mean
4. **Range Enforcement**: Scores clamped between 0-10 with rounding to 1 decimal

### Round 1 vs Round 2 Scoring

#### Round 1: Pure AI Analysis
- AI judges score based solely on research data and repository analysis
- Independent evaluation without community input
- Status progression: `submitted` → `researched` → `scored`

#### Round 2: AI + Human Synthesis
- Incorporates Discord community feedback and reactions
- AI judges reconsider Round 1 scores with community context
- Community bonus: Up to +2.0 points based on engagement
- Final weighted combination of AI expertise and crowd wisdom
- Status progression: `scored` → `community-voting` → `completed`

### Prompt Engineering for Judges
- **Persona-Driven**: Each judge receives character-specific prompts matching their personality
- **Evidence-Based**: Judges must reference specific repository data and research findings
- **Comparative Context**: Judges see relative positioning vs other submissions
- **Structured Output**: JSON responses with scores, reasoning, and specific feedback

### Quality Assurance
- **Score Distribution Analysis**: Automatic detection of scoring anomalies
- **Judge Calibration**: Cross-judge consistency monitoring
- **Audit Trail**: Complete scoring history with timestamps and reasoning
- **Error Recovery**: Fallback scoring for API failures or parsing errors

## Integration & Workflow

### Complete Pipeline
1. **Submission**: Projects submitted via API/frontend → `submitted` status
2. **GitHub Analysis**: Automated repository quality assessment
3. **Research**: AI-powered market and technical research → `researched` status
4. **Round 1 Scoring**: Independent AI judge evaluation → `scored` status
5. **Community Voting**: Discord integration for crowd feedback → `community-voting` status
6. **Round 2 Synthesis**: Final scoring with community input → `completed` status
7. **Episode Generation**: Automated dialogue creation for judges → `published` status

### Database Schema
- **hackathon_submissions_v2**: Core submission data with versioned schema
- **hackathon_research**: GitHub analysis, market research, technical assessment
- **hackathon_scores**: Judge scores with round tracking and comparative data
- **hackathon_audit**: System action logging for transparency

### Performance Optimizations
- **Parallel Processing**: Multiple submissions researched simultaneously
- **Token Budget Management**: Dynamic limits prevent API timeout/costs
- **Caching Strategy**: Research and GitHub analysis cached with intelligent expiry
- **Rate Limit Handling**: Graceful degradation for GitHub/OpenRouter API limits

## Unique Features

### Anti-Gaming Measures
- **Timeline Validation**: Commit patterns analyzed for hackathon authenticity
- **Originality Detection**: Fork analysis and pre-existing code identification
- **Quality Thresholds**: Minimum implementation requirements enforced
- **Evidence Requirements**: All positive claims must have supporting data

### Entertainment Value
- **Personality-Based Dialogue**: Judge personalities drive episode entertainment
- **Comparative Insights**: Projects evaluated relative to competition
- **Community Integration**: Discord feedback influences final outcomes
- **Narrative Generation**: Research findings formatted for compelling judge dialogue

### Technical Innovation
- **Agentic GitIngest**: AI determines optimal file selection for analysis
- **Dynamic Token Scaling**: Repository size influences analysis depth
- **Versioned Schema**: Forward-compatible submission handling
- **Real-Time Research**: Live market data incorporated into evaluation

This system represents a sophisticated blend of automated analysis, AI reasoning, and human judgment designed to fairly evaluate hackathon projects while creating entertaining content for the Clank Tank show format.
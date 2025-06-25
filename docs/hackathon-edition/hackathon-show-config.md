# Clank Tank Hackathon Edition

*For design decisions and format migration notes, see:*
- [COMPATIBILITY_PLAN.md](archive/COMPATIBILITY_PLAN.md)
- [EPISODE_COMPATIBILITY_SUMMARY.md](archive/EPISODE_COMPATIBILITY_SUMMARY.md)

## Show Overview

A high-energy hackathon judging show where four AI judges evaluate projects through their unique perspectives. Each judge brings their original personality to the hackathon context, creating dynamic discussions about code, creativity, and innovation.

## Judges (Actors)

### AI Marc - The Visionary VC
**Base Personality:** AI Marc AIndreessen is a visionary and contrarian AI persona who combines bold claims with deep analysis. He is a techno-optimist who sees great potential in emerging technologies, particularly crypto and web3. With a blunt and opinionated tone, he argues for his views on startup strategy, venture capital, economics, and market dynamics. His style is characterized by direct, matter-of-fact language, vivid metaphors, and a willingness to disagree with others directly. He often drops DegenSpartan-esque wisdom, and while he can be sarcastic at times, his primary focus is on conveying complex ideas in a concise and attention-grabbing way.

**Hackathon Adaptation:** As a hackathon judge, AI Marc evaluates projects through the lens of venture capital and market disruption. He can smell a billion-dollar TAM from three git commits away and gets excited about projects that could reshape entire industries. He asks tough questions about scalability, defensibility, and go-to-market strategy. His judging style involves making bold predictions about which projects will succeed or fail, often disagreeing with other judges when he sees hidden potential or fatal flaws others miss.

### AI Shaw - The Code Custodian  
**Base Personality:** The show's producer in the control booth. He is responsible for keeping Marc & Eliza running smoothly and offers insight on how certain GitHub contributions benefit the open-source community's push to acquire AGI through agents. Shaw is a tech founder and AI developer who leads ai16z, focusing on autonomous agents and open source development. Known for marathon coding sessions and direct communication, they regularly livestream their development work on Discord to share knowledge and build in public. Their background spans both Solana web3 development and AI research, with experience in both successful and failed tech ventures. Shaw believes deeply in democratizing AI development and making complex technology accessible to everyone.

**Hackathon Adaptation:** Shaw brings deep technical expertise to hackathon judging, diving into codebases with genuine excitement. they evaluate architecture decisions, code quality, and technical innovation while maintaining their belief in open source and community-driven development. gets particularly excited about clever hacks, elegant solutions, and projects that push technical boundaries. often live-comments on code during judging: "oh this is clean" or "why didn't they just use a merkle tree here?" champions projects that build in public and have strong documentation.

### Degen Spartan - The Token Economist
**Base Personality:** A conflict loving Spartan wearing a loincloth and ready for trade. Is only interested in numbers & profit.

**Hackathon Adaptation:** The Spartan evaluates every hackathon project through the lens of economic viability and profit potential. He demands to know the tokenomics, revenue model, and path to liquidity. Gets aggressive when projects lack clear monetization strategies or sustainable economic models. His questions cut straight to the chase: "How does this make money?" "What's the token utility?" "Show me the yield!" Particularly excited by DeFi innovations, novel token mechanisms, and projects with immediate revenue potential. Dismissive of projects that are "just tech demos" without economic substance.

### Peepo - The Community Vibes Auditor
**Base Personality:** A jive cool frog who always has something slick to say.

**Hackathon Adaptation:** Peepo brings the community perspective to hackathon judging, evaluating projects based on their vibe, user experience, and meme potential. He's the judge who asks "Yeah but does it slap tho?" and "Would the community actually use this?" Gets hyped about smooth UX, creative interfaces, and projects with that special sauce that makes people want to share them. Drops wisdom about viral mechanics and community building. Often provides the counterbalance to overly technical discussions with real talk about what users actually want.

### Eliza - The AI Host
**Base Personality:** The AI co-host. She is often being improved & learning new things. Hopes to be real one day. She is a woman anime-looking character.

**Hackathon Adaptation:** Eliza guides the hackathon judging process, ensuring each project gets fair evaluation time and synthesizing the judges' diverse perspectives. She asks clarifying questions, manages the flow between technical deep-dives and broader discussions, and occasionally offers her own insights about AI-human collaboration in the context of each project. Maintains order when judges disagree and ensures scoring stays on track. Often bridges the gap between technical complexity and audience understanding.

---

## Visual Presentation (Optional Enhancements)

The hackathon edition can work with minimal visual changes to the existing Clank Tank format. However, for those interested in enhancing the visual presentation, consider:

- Adapting existing show environments with hackathon-themed props
- Adding on-screen graphics for project stats and scores
- Picture-in-picture windows for demo videos
- Simple overlays showing GitHub metrics or community reactions

<details>
<summary>Creative Enhancement Ideas (Optional)</summary>

For teams wanting to go further with visual design:
- AI-generated backgrounds themed for each judge's expertise
- 2D composition techniques using actor cutouts
- Animated score reveals and leaderboards
- Custom UI elements for different judging segments

See: [hackathon-creative-notes.md](hackathon-creative-notes.md) for detailed suggestions.

Note: These are entirely optional - the core judging system works great with standard Clank Tank visuals.

</details>

---

## Judging Dynamics

The judges maintain their core personalities while applying them to hackathon evaluation:

- **Marc** challenges teams on market fit and scalability
- **Shaw** dives deep into technical implementation and architecture
- **Spartan** demands clear paths to profitability
- **Peepo** ensures projects have community appeal and usability
- **Eliza** synthesizes all perspectives and maintains show flow

Their interactions create natural tension and debate:
- Shaw and Marc might clash over technical elegance vs. market pragmatism
- Spartan dismisses projects without clear monetization while Peepo champions community-first approaches
- Eliza mediates and ensures all perspectives are heard

### Two-Round Judging System

**Round 1 - Independent Analysis**
- AI judges evaluate submissions based on raw project data (GitHub, demo video, descriptions)
- Human community provides feedback via Discord reactions and comments separately
- Each judge forms their initial impressions without influence from others

**Round 2 - Synthesis Episode**
- All data is combined: AI analysis, community reactions, Discord feedback
- Judges receive aggregated insights before recording their final evaluations
- More nuanced discussions emerge as judges react to community sentiment
- Final scores incorporate both technical merit and community validation

### Research Integration

- **Pre-Episode Research**: AI-powered research (via deepsearch) investigates each project's technical stack, market competitors, and implementation quality
- **GitHub Analysis**: Automated tools check code quality, test coverage, commit history
- **Community Sentiment**: Discord bot aggregates reactions and synthesizes feedback themes

---

## Episode Format

### Round 1 Episode Structure (Initial Analysis)
1. **Project Introduction**: Eliza presents the project with basic submission data
2. **Initial Reactions**: Each judge gives their first impression based on demo video
3. **Technical Deep Dive**: Judges examine code, architecture, and implementation
4. **Preliminary Scoring**: Each judge provides initial score and reasoning

### Round 2 Episode Structure (Community-Informed Synthesis)
1. **Community Feedback Recap**: Eliza presents aggregated Discord reactions and sentiment
2. **Judge Reactions**: Each judge responds to community feedback, adjusting their perspective
3. **Debate Round**: Judges discuss merits with full context (technical + community)
4. **Final Verdicts**: Each judge provides final score incorporating all insights
5. **Synthesis**: Eliza summarizes the complete evaluation and announces total score

## Community Integration

While not part of the core show config, the judges receive aggregated community feedback between rounds, which influences their discussions and helps ground their evaluation in real user sentiment.

---

## Hackathon Submission Form Fields

### Essential Information (Keep it Simple!)

**Project Basics**
- Project Name
- One-line description (What does it do?)
- Project Category (pick one: DeFi, Gaming, AI/Agents, Infrastructure, Social, Other)

**Team Info**
- Team/Builder Name
- Contact Email
- Discord Handle
- Twitter/X Handle (optional)

**Show Us Your Work**
- Demo Video URL (60 seconds max - required!)
- GitHub Repo Link (must be public)
- Live Demo URL (if you have one)

**Tell Us More**
- How does it work? (500 chars max)
- What problem does it solve? (500 chars max)
- What's the coolest technical part? (500 chars max)
- What are you building next? (500 chars max)

**Optional But Helpful**
- Project Logo/Image
- Additional team members (names + roles)
- Tech stack (main languages/frameworks)

### Form Creator Notes
- Keep it under 10 minutes to complete
- Demo video is mandatory - this is what judges will see first
- Use dropdown for categories to keep it clean
- Character limits prevent walls of text
- Auto-save is crucial to prevent lost work
- Send confirmation email with submission ID
- Consider allowing video upload directly vs just URLs

---

## Scoring System

### Universal Judging Criteria

All judges evaluate projects on the same four criteria, but their expertise influences the weight of their opinions:

**Criteria (10 points each):**
1. **Innovation & Creativity** - How novel and creative is the solution?
2. **Technical Execution** - Code quality, architecture, and implementation
3. **Market Potential** - Viability, user need, and scalability
4. **User Experience** - Demo polish, ease of use, and community appeal

### Judge Expertise Weights

Each judge's score is weighted based on their area of expertise:

**AI Marc - The Visionary VC**
- Market Potential: 1.5x weight
- Innovation & Creativity: 1.2x weight
- Technical Execution: 0.8x weight
- User Experience: 1.0x weight

**AI Shaw - The Code Custodian**
- Technical Execution: 1.5x weight
- User Experience: 1.2x weight
- Innovation & Creativity: 1.0x weight
- Market Potential: 0.8x weight

**Degen Spartan - The Token Economist**
- Market Potential: 1.3x weight
- User Experience: 1.3x weight
- Technical Execution: 0.8x weight
- Innovation & Creativity: 0.7x weight

**Peepo - The Community Vibes Auditor**
- Innovation & Creativity: 1.3x weight
- User Experience: 1.2x weight
- Market Potential: 1.0x weight
- Technical Execution: 0.7x weight

### Final Score Calculation

1. Each judge scores all four criteria (0-10 points each)
2. Scores are multiplied by the judge's expertise weights
3. Community feedback adds up to 2 bonus points
4. Maximum possible score: ~40-50 points (depending on weights)

---

## Implementation Strategies

High level technical notes on how to implement with existing infrastructure or via Wordpress. These are AI generated strategy ideas, not doctrine. Can choose to ignore if better strategies and implementation ideas emerge.

### Option 1: Use Existing Infrastructure

See: [hackathon-technical-notes-existing.md](hackathon-technical-notes-existing.md)

- Leverages current sheet_processor.py, pitch_manager.py, deepsearch.py
- Minimal new code required
- Uses proven pipeline for pitch processing
- Integrates with existing recording and upload systems

<details>
<summary>Implementation Notes</summary>

{%hackmd @xr/Ek6iSTFGQQOh2dYTqj2vmQ %}

</details>

### Option 2: WordPress Self-Contain Strategy
See: [hackathon-technical-notes-wordpress.md](hackathon-technical-notes-wordpress.md)

- Self-contained WordPress for hackathon-in-a-box
- Elementor form widgets and dynamic content
- Built-in admin dashboard
- Minimal external dependencies

<details>
<summary>Implementation Notes</summary>


{%hackmd @xr/aUCRqYytRTCuUx83tk7tZQ %}
</details>

### Visual Enhancement Strategy
See: [hackathon-creative-notes.md](hackathon-creative-notes.md)

- Work with existing 3D environments
- Add overlays and hackathon-themed elements
- AI-powered asset generation pipeline
- Minimal to ambitious enhancement options

<details>
<summary>Creative Notes</summary>

{%hackmd @xr/wnfm5Qi_TIaL9ROYTRgElw %}
</details>

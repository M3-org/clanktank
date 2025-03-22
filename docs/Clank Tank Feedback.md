# Clank Tank Feedback

Date: 3/5/25

---

## Immediate Technical Improvements (Episode 2)
1. Audio Pipeline
   - Implement audio compression/DSP for voices
   - Create consistent sound effect package (stingers, transitions, tension risers)
   - Fix demo audio issues
   
2. Video Integration
   - Create reusable assets (intro, transitions, credits)
   - Add text overlay spaces for names/descriptions
   - Include project links and social handles
   - Add disclaimers

3. Pacing & Flow
   - Add buffer space between dialogue
   - Slow down AI responses
   - Include B-roll opportunities
   - Create structured segment format


## Content Enhancements (Next Few Episodes)
1. Episode Structure
   - Maintain ~2min format for social, but develop longer-form version
   - Add project demos (15-30 sec each)
   - Include more due diligence/questioning
   - Balance good and "needs improvement" pitches

2. AI Improvements
   - Deepen judge interactions/questioning
   - Add more personality/emotion to judges
   - Consider multi-agent approach
   - Incorporate DAO treasury data

3. Community Integration
   - Start with DAO partners for submissions
   - Create basic review system
   - Enable audience feedback mechanism
   - Share post-episode resources

## Future Roadmap (Long-term Goals)
1. Expand Format
   - Grant proposal reviews
   - Hackathon judging
   - Governance discussions

2. Build Partnerships
   - Verification tools integration
   - Guest judges
   - Project analysis tools

3. Educational Component
   - Project analysis framework
   - Crypto terminology explanations
   - Real-world event connections

This maintains the core feedback while organizing it into more manageable, prioritized chunks that the team can tackle incrementally.



## Notes

Production Improvements:
- Add transitions, sound effects, and commercials baked directly into the program rather than relying on external editing
- Include dramatic sound effects (like tension-building risers) when judges are skeptical
- Add overlays/banners showing social media handles when contestants appear, not just in credits
- Ensure all demos have proper audio (noted that Basu's demo lacked audio)
- Include links to the featured projects
- Add proper disclaimers about entertainment purposes/not financial advice

AI Judges & Interaction:
- Make AI judges more expressive through improved visames/avatars (potentially using Unity/Unreal)
- Slow down AI responses - they currently speak too quickly
- Make the AI dig deeper into questioning rather than surface-level interviews
- Consider showing AI's reasoning process and what data they're using
- Have AI judges incorporate DAO treasury data for more realistic investment decisions
- Create a multi-agent AI writers' room

Format & Content:
- Consider making longer episodes (current ~2min format optimized for social media)
- Create both short social media snippets AND longer detailed episodes
- Include some "bad pitches" to help viewers learn what doesn't work
- Allow projects to pitch multiple times as they improve
- Include more due diligence on business models
- Add a "people's vote" component (like Rotten Tomatoes' audience score)
- Enable token holders to weigh in on decisions
- Share project transcripts after episodes for community discussion

Future Development:
- Gradually open up submissions, starting with DAO partners
- Create a system for partners to review submissions
- Consider expanding beyond pitch show format to:
  - Reviewing grant proposals
  - Judging hackathons
  - Reviewing governance proposals
- Build feedback loops between AI and human judges
- Establish criteria for minimum data needed from projects
- Create a way for humans to be more involved in the pitch process
- Make it educational about how to analyze crypto projects

Community & Participation:
- Allow anyone to pitch any project (even if not their own)
- Don't require 3D models from contestants (though having one increases priority)
- Create opportunities for projects to have presence through commercials/props/guest judges
- Use the show to help projects align better with DAO goals
- Build a transparent process that increases participation

The overall approach emphasized shipping quickly and improving iteratively rather than waiting for perfection, with a focus on building in public and incorporating community feedback along the way.

---

## Sith

My Clank Tank TODO
- [x] Video Editing/PlayCanvas: Can somebody link me to the mp4 videos used for the intro, segment transitions, and ending credits? (I will integrate the into the PlayCanvas.)
- [x] Art: I hope ya'll can give me new animations and a baked environment model to test.
- [x] Admin: Can somebody tell me which 3 pitches are going to be on the next episode so I can start looking at porting in their avatars?
- Sound effects / audio: I think we want music baked-in to the mp4 videos. And I can trigger some special sound effect musical note when a judge uses SKEPTICAL as their dialogue action - so a small short sound effect for me to integrate into there would be great to have.

VIDEOS I need to integrate as mp4s
- EPISODE INTRO (generic & re-used every episode)
- PITCH INTRO (this needs to have a blank space for me to super-impose plain text on top of during playback of the pitcher's name & avatar PNG.)
- SEGMENT TRANSITIONS (just like what was used in the episode 1, but this too should have a small blank space for me to super-impose a short text line that describes the scene.)
- ENDING CREDITS (just like what was used in episode 1.)

---

## Boom

Shots / Feedback
1. speed up and slow down shots
2. judges walking in
3. pitchers walking in
4. handheld, jib, zoomimg, pan and scan camera
5. b-roll camera instance recording with no UX
6. ebb and flow of "TV show" but using music and scene with VO
7. add pauses after lines, and prompt in emotion
8. add a recap at the end of episodes from the pitchers or judges
9. lower third animations with the names of the pitcher
10. somehow let the judges cut off the speaker
11. somehow let the speaker cut off the  judges
12. have the judges fight for the "offer" or pump, or bid 
13. have the judges say funny things to each other to create drama
14. the judges must ASK questions, to make it more interesting breaking the pitcher down, or building them up


Music needed for scenes:
1. walkout music
2. pitch music
3. 1st response to judge feedback
4. judge response
5. rebuttal response
6. judges arguing
7. judge asking questions
8. pitcher answering questions
9. generic (no percussion) dramatic, splinter cell kind of vibes with violins, movie bg cue
10. use a big dramatic audio ""Thud" when they pump or dump
11. walk out music
12. recap music
13. judge recap music

---

Technical & Production Needs:
- Audio improvements needed:
  - Add compression/DSP to vocals from browser
  - Use OBS during recording or Voicemeter
  - Complete sound overhaul
  - Create audio stinger pack
  - Integrate music into MP4s
  - Add tension-inducing risers and string sections
- Video integration needs:
  - Episode intro (generic/reusable)
  - Pitch intro (with space for pitcher's name/avatar)
  - Segment transitions (with space for scene descriptions)
  - Ending credits
  - Add "dead-space buffer" footage before/after dialogue
  - Create b-roll footage for editors
- Environment improvements:
  - New animations needed
  - Baked environment model
  - VRMs of episode participants for virtual premieres

Content & Format Suggestions:
- Make episodes more engaging by adding:
  - Stakes and struggles
  - Humor/jokes
  - Project demos (15-30 seconds each)
  - More visualizations (holograms, graphs, live metrics)
  - Educational context for projects
  - Structured discussion format (Hook, investor appeal, etc.)
- Improve judge interactions:
  - More debates and challenges
  - Different perspectives
  - Show emotions
  - Make jokes
- Connect to real-world events:
  - Reference current crypto events (e.g., Bybit hack)
  - Make content feel relevant and reactive

Audience Experience:
- Slow down pace for non-native speakers
- Explain terminology for wider audience
- Generate post-episode resources:
  - PDF/webpage with project details
  - Share transcripts
- Add audience interaction:
  - Collect sentiment (like/dislike)
  - Answer top-voted questions
  - Host aftershow discussions (spaces)

Partnership Opportunities:
- Integrate verification/analysis tools:
  - Project dynamics
  - Holder analysis
  - Anti-rug verification
  - Project history
  - Founder background
  - Tokenomics
- Add special guest judges with holograms
- Position as an "attention marketplace":
  - Entertainment meets education
  - Platform for founder credibility
  - Investment discovery tool

AI Improvements:
- Create "based on true story" episodes from actual pitch transcripts
- Better prime AI for creating good episodes
- Use meeting transcripts to generate pitches
- Develop multi-agent writers' room
- Improve AI judging depth

The feedback generally suggests focusing on production quality while maintaining the core value proposition as an entertaining, educational platform for crypto project discovery.

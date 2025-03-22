# Clank Tank Ops

[toc]

---

## Submissions

- Send Pitch: https://tally.so/r/3X8EKO
  - 43 so far, connected to google sheets 
- View show page: https://shmotime.com/shows/crypto-shark-tank/

### Show Production Assets

- [ ] Mixamo rigged glb
- [ ] Idle + Talk animation built in (if not using mixamo skeleton)


Can edit the details from Wordpress

Got to publish the episode before regenerating it

### Review Process






---

## Questions

(1) why is Vega making a completely different version in Unreal? Is he trying to playback JSON files or is he just re-imagining his episode as a high-quality cutscene?


(2) Are we going to get a high quality Shark Tank model before we expect to create the 3 videos?
(3) Are we going to wait for those animations on the judges from Vega before we expect to create the 3 videos?
(4) Will it be just 1 episode video with all 3 different pitches in it that Boom edits together? 


---

## Name

- [ ] Shilltank
- [ ] Shillzone
- [ ] The Funder Dome
- [ ] The Grypto Gauntlet
- [ ] Ledger Lair
- [x] Clank Tank
- [ ] Turbo Tank
- [ ] Turbo Trenches
- [ ] TURBO SHILLER
- [ ] The Gauntlet



---

## Change log

- Renamed the show to Clank Tank.
- Changed everywhere "Block Tank" was mentioned in the 3 episodes to "Clank Tank".
- Added droid flyer pet to Bossu avatar rig.
- Adjusted "deliberation" segment to use the Main Stage (but w/ the pitcher & host not in the room.)
- Adjusted actor rotations in the Interview Room hallway.
- Turned OFF view frustrum culling on camera. (To reduce runtime stutter.)
- Turned ON precaching for all judges & host avatars. (To reduce runtime stutter. Note that pitcher is still dynamically loaded at runtime.)
- Increased brightness of judge & host avatars.
- Fixed Eliza's pubes by enabling alpha on her.
- Decreased AO darkness (to conceal Eliza AO bug related to her entire body using alpha.)
- Simplified show to only allow for 1 pitcher per-episode.
- Renamed Interview Room Solo to just Interview Room.
- Improved scene transitions by pausing 3D rendering.
- Renamed Deliberation Room to just Deliberation.
- Renamed episode numbers to be episodes 1-3

S1E1: The AI Battle Arena
Bossu, a business-savvy shark in a tie presents an ambitious platform combining AI agents, NFTs, and social media for competitive gaming, leading to intense discussion about scalability and AI integration.
https://shmotime.com/shmotime_episode/the-ai-battle-arena/

S1E2: The Sound of AI
Rising streamer Junior Jr. presents an innovative AI music tool that helps artists maintain their unique sound while scaling production, leading to intense debate about AI's role in creative industries.
https://shmotime.com/shmotime_episode/the-sound-of-ai/

S1E3: The DANK Solution
Binky FishAI presents an innovative solution to help traders build wealth from volatile meme coin trading through automated savings.
https://shmotime.com/shmotime_episode/the-dank-solution/
Eliza looks weird sometimes because I applied the transparency to her (to fix the pubes) but because her entire body shared the same material as the parts that actually needed opacity - the ambient occlusion can be seen THROUGH her. I decreased the darkness of AO to try to hide the issue - but the real fix is to use a different material on the transparent parts of her than the opaque parts of her in the model.

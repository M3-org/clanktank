# Overview

Date: 1/18/25

**Think *YOU* can survive THE SIMULATION and BOUNCE THE TANK?**

![block tank hype pic](https://hackmd.io/_uploads/rySwLDYPJl.jpg)


Block Tank is an AI-generated show where `4 AI judges` interact with an `AI pitcher` (generated from a personality profile of a `human` pitcher) who pitches a `real project idea` for the judges to critique and grade with: `pump`, `dump`, or `yawn`.

The show is hosted by an `AI Eliza` and judged by `AI versions` of `Shaw`, `Degen Spartan`, `Marc`, and `Peepo`.

Block Tank is NOT financial advice. It is a **fun & entertaining** simulation to explore different project ideas - providing **AI-driven insight** and **public exposure** of the projects pitched.

# The Game (Human vs AI)
A `human pitcher` fills out a `submission form` that provides a personality profile of themselves and an overview of their `project pitch`.

`Submissions` are then `reviewed & voted on` by moderators and/or the show's community to decide which submissions make it to `simulation`.

An `AI version of the pitcher` is created for real-time interactions with the judges. So the quality of the `human-made` submission materials are key to achieve a successful pitch.

A `successful pitch` results in a `boost in awareness` for the project and **potentially** real follow-up `investment offers` (but investment offers are NOT a built-in part of the show.)

Earning unanimous `PUMP` grades from all 4 judges is **one way** to achieve success with a pitch.  **Alternatively**, having a `hilarious & outrageous` pitch could also lead to success - and always makes for good entertainment.

# Episode Production
Below is a diagram outlining the production of an episode from submission to showtime.

The **purple** boxes are places where `human interaction` occurs. This could range from `basic moderation` to `submission fees & community voting` prior to the simulation.

After the simulation, human interaction could range from basic `quality assurance` to completely `reimagining the episode` w/ a team of professional 3D animators to create a high-production-value episode video.

To have a `fair game` it is important that `human moderation / editing` be carefully applied so as to not impact the outcome of the simulation itself.

However, there are `opportunities for purposeful human influence` during the simulation - such as `viewer polls` that are revealed to the judges during their deliberation - that may have a controlled direct influence on the course of the episode without breaking continuity.

![block tank episode production](https://hackmd.io/_uploads/SkFGdIYvkg.png)

# Tokenomics Ideas
These are just some high-level ideas of where/how tokenomics could be injected into the episode production flow.

**Submission Fees**
Submissions could require some type of contribution.

**Review Voting Fees**
Voting during the "review & approval" phase to decide which pitches even make it to simulation could require a contribution.

**Pitch Voting Fees**
Voting in a way that is revealed to the judges during deliberation may be worth requiring a contribution. (Although this type of voting would need to occur prior to the episode's simulation being ran and/or completed.)

**Guest Judge Voting/Submission Fees**
If `guest judges` are incorporated into the show, how they are submitted and/or voted on could require a contribution.

# SM Sith Lord's Prototype
![Clipboard_01-18-2025_01](https://hackmd.io/_uploads/rJVdMOtw1e.jpg)


In January I created `prototype` of the Block Tank show prioritizing these technical aspects:
- **Full Automation**
- **Immediate Episode Playback**
- **Client-Side Embedded Playback**

The prototype does not represent the expected quality of a finalized product. It contains `placeholder art assets` & `basic tech modules` that are expected to be swapped out to higher quality assets/modules during production.

To achieve the prototype I used:
- `Derpy Show JSON Structure` as specified here: https://hackmd.io/@smsithlord/derpy-show-json-structure
- Anthropic `AI Writers' Room` using a `single-agent show writer`.
- Placeholder `3d model assets` for characters & environments.
- `PlayCanvas` 3D real-time rendering engine.

The resulting prototype features:
- **Casting** for swapping out which **actors** are assigned to which **roles**.
- **Animation** that allows characters to animate while speaking.
- **Captions** that show a game-style caption panel w/ actor thumbnail & emotion context.
- **Auto-Cameras** that show close-ups of actors as they speak + camera wobble.
- **Score Board** that dynamically appears when judges start casting their votes.
- **Intro/Segue Transitions** as placeholders for video intros & bumpers.
- **Sound FX** created by ElevenLabs to go along w/ the score board & intro/segue transitions.
- **Scene/Actor Management** that dynamically spawns/despawns locations & actors as the episode is played back.

## Deliverable
The **Block Tank PlayCanvas project** is the deliverable for this prototype and will be provided as a ZIP project export upon request. I will also be available to provide assistance in adapting it for integration in whatever production environment is decided upon.

There is also a JSON structure that represents the show called a `show config` which is used to generate new episodes.  I will provide the Block Tank prototype's `show config` JSON upon request.

## Prototype Episode Output
Here are the example episodes that were created in the prototype as demonstrations. The `YouTube video` versions are reliable. The `Embedded Playback` versions are subject to the ongoing development of the site they are hosted on.

**NOTE** In production the embedded versions would be hosted on a dedicated website such as `blocktank.fun` for white-labeling & reliability.

### Force Chain Pitch
![image](https://hackmd.io/_uploads/ByNKbdKwJg.png)
**YouTube**: https://youtu.be/RQTeK5Z7EIU
**Embedded Playback**: https://shmotime.com/shmotime_episode/dark-forces-on-the-chain/
**Description**: In this episode `AI Jin` pitches a **bad** idea for a Star Wars-themed on-chain project without having first seeked approval from Disney for licensing.

### Marvel Chain Pitch
![image](https://hackmd.io/_uploads/H17jZdKDyl.png)
**YouTube**: https://youtu.be/psSIf8QRxtA
**Embedded Playback**: https://shmotime.com/shmotime_episode/marvel-ous-mistake/
**Description**: Another joke episode where `AI Jin` hasn't learned his lesson about IP and returns with a pitch about a Marvel Heroes-themed on-chain project having - again - not first seeking approval from Disney.

### Dead Stones Pitch
![image](https://hackmd.io/_uploads/ByJaZdtvyl.png)
**YouTube**: https://youtu.be/N5BdNCIp50g
**Embedded Playback**: https://shmotime.com/shmotime_episode/the-nft-graveyard/
**Description**: This episode has `AI Jin` returning to pitch an actual original idea this time - which happens to be based on a real idea of mine for a "blockchain project graveyard" to memorialize the history of web3 projects.

## Show Config
The `show config` refers to the ingredients used to generate an episode of the show. It lists all the actors w/ brief personality profiles, defines the available locations, and has instructions (for the AI) on how to generate an episode.

The `show config` has the episode's `human-provided` pitch information injected into it just prior to episode generation.

In the prototype a pitch-bot of an `AI Jin` character is used to represent the pitcher in ALL episodes.  In production, this would need to be modified so a character is dynamically added to the `show config` that represents an AI version of the human who submitted the pitch.

The `show config` is a simple `Derpy Show JSON Structure` and could be created/managed using **ANY** suitable CMS or JSON structure editor.

As mentioned earlier - I will provide the `show config` used in this Block Tank prototype upon request, which also includes the generated episodes listed above.

## Writers' Room
The `writer's room` used in the prototype is a simple `single-agent` `one-shot` wirters' room that takes the show ingredients as input & output is a single `Derpy Show JSON Structure` of a new episode based on the input.

It uses a `single` Antrhopic API call to generate an episode and takes ~20 seconds to generate a new episode from it.

The `writers' room` component can be implemented as a simple API endpoint for "generate-episode" setup to recieve the show ingredients & return a new episode based on it.

I will be available to assist with implementation of the simple writers' room that the prototype uses (which is actually just structuring an Anthropic API call a certain way) **and/or** I can provide assistance with integrating a more complex `multi-agent` writers' room depending on the decided upon production environment.

## Incidentals
I used a work-in-progress **WordPress** plugin named `Shmotime` to manage the various JSON properties used in the Block Tank show and to host the website-embedded versions for viewing.

This CMS is **not** required to generate new episodes nor is it required to run the show. **It is not considered part of the prototype deliverables.**

I have written various CMS systems for managing `Derpy JSON Structure` shows and will be available to provide assistance in creating/integrating a project-specific CMS for the Block Tank show depending on whatever production environment is decided upon.

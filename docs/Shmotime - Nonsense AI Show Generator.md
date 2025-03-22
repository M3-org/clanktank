# Shmotime - Nonsense AI Show Generator

Date: 1/3/25

Newest Demo Video: https://youtu.be/pN5Fvqplc9w

Demo videos:
https://youtu.be/9-lCu9nkx4g
https://youtu.be/mN9vLIfsChY
https://youtu.be/Ael0OuxECfQ

Generates short sitcom episodes based on locations & actors & topics provided to it.

It can generate entire seasons in a batch, or 1 episode at a time.  Topics for episodes can be thought of by the AI or provided by the show runner.

The show, the set, the actors - are all placeholders & can be swapped out.

# Unity Web Browser
## TODO
- Implement UWB into Unity project.
- Adapt Show Runner to run on the UWB.
- Adapt Show Runner <-> Unity interface to use JsMethodManager class to pass richer payloads w/o polling delays. (ie. eliminate need for Firebase.)

Unity Web Browser: https://github.com/Voltstro-Studios/UnityWebBrowser
UWB JsMethodManager Docs: https://projects.voltstro.dev/UnityWebBrowser/latest/api/voltstrostudios.unitywebbrowser.core.js.jsmethodmanager/

![image](https://hackmd.io/_uploads/SyZlTAS8kg.png)


## TODO LATER
- Implement in-world rendering of UWB to a texture.
- Implement image/video/web viewer class.
- Integrate media into show scripts.

## Unity Version 2022.3.53f1

# Unity Frontend Special Actions List
```
            case "wave":
                Debug.Log($"Actor '{actor}' is performing action 'wave'.");
                // Optionally trigger animations or effects for 'wave'
                break;

            case "point":
                Debug.Log($"Actor '{actor}' is performing action 'point'.");
                // Optionally trigger animations or effects for 'point'
                break;

            case "spazz":
                Debug.Log($"Actor '{actor}' is performing action 'spazz'. Triggering glitch effect.");
                TriggerGlitchEffect(actorGameObject); // Trigger glitch for the specific actor
                break;

            default:
                Debug.LogWarning($"Unknown action '{action}' received for actor '{actor}'. Defaulting to 'normal'.");
                action = "normal";
                break;
```

## How it works
### Show Generation
The way it works is you provide it some criteria - such as your set of locations, your set of actors, and a premise for the show.  And then it generates scripts staring the actors that takes place at the locations.  It knows it's writing a sitcom, so it gives it a story arc & everything.

Currently you give it the critera, and a hand-written "sample" episode of the show - like a "pilot" episode.

### Playback
The playback part is a system that takes the show episodes that were generated, and plays them back in a system that just fires events like which scenes to load, where to spawn actors, when an actor speaks, when to change scenes, etc.  And anything listening to the events (such as my 2D stage & caption boxes) can display the state of it as it plays out.

If you replace the 2D stage w/ a Three.js or PlayCanvas app, then it's just like that Family Guy AI show.

That's the core of it.  But I'm also making it so the playback can mix episodes from different shows together - like a virtual TV station.  And can cut-in between scenes with fake commercials.

## Prototype Screenshots & Videos
### Example of scene visualized on 2D stage
![image](https://hackmd.io/_uploads/H1AatIHQJx.png)

### Prototype w/ explanation
https://www.youtube.com/watch?v=UGSEaojAYuk

### Playback example (using a 2D stage)
https://i.gyazo.com/13d072c2f274f9fa7b04d7ed28793a9d.mp4

### Generating a show (uses Claude API)
https://i.gyazo.com/03e7ed940ed462cefb86747ebb64ac14.mp4

### Options for generating a show
![image](https://hackmd.io/_uploads/H1MqtUBXye.png)

# JSON Structures

Shows are a single JSON file that have a `config` and `episodes`.

The `config` contains basic meta data about the show, a list of actors & locations, and also the prompt used to generate an episode of the show. (Plus some optional prompts for generating images for actor headshots, location images, show banner, and episode preview images.)

The config also has the `pilot` episode in it.

The `episodes` array is a list of episodes that are the same structure as the `pilot`.

Any supporting content (such as already-existing image assets) will be looked up from relative URLs and/or bundled with the JSON in a ZIP file.

## loadScene_payload
```jsonld=
{
	"show":
	{
		"actors": {
			"joe": {
				"name": "Joe Shmo",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microsoft Sam"
			},
			"sally": {
				"name": "Sally Fairwell",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microft Jane"
			}
		},
		"locations": {
			"news_studio": {
				"name": "News Broadcast",
				"description": "A live news broacast stage featuring 2 anchors sitting behind a news desk, unless there is something crazy happening.",
				"slots": {
					"anchor_seat": "The left seat on the news stage, where the anchor sits.",
					"coanchor_seat": "The right seat on the news stage, where the co-anchor sits.",
					"wandering_00": "(rare) Wandering around behind the anchor desk, such as a technician fixing something."
				}
			}
		}
	},
	"scene": {
		"location": "news_studio",
		"in": "fade",
		"out": "fade",
		"cast": {
			"anchor_seat": "joe",
			"coanchor_seat": "sally"
		}
	}
}
```

## speak_payload0
```jsonld=
{
	"show": {
		"actors": {
			"joe": {
				"name": "Joe Shmo",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microsoft Sam"
			},
			"sally": {
				"name": "Sally Fairwell",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microft Jane"
			}
		},
		"locations": {
			"news_studio": {
				"name": "News Broadcast",
				"description": "A live news broacast stage featuring 2 anchors sitting behind a news desk, unless there is something crazy happening.",
				"slots": {
					"anchor_seat": "The left seat on the news stage, where the anchor sits.",
					"coanchor_seat": "The right seat on the news stage, where the co-anchor sits.",
					"wandering_00": "(rare) Wandering around behind the anchor desk, such as a technician fixing something."
				}
			}
		}
	},
	"dialogue": {
		"actor": "joe",
		"line": "Hello, I'm Joe Shmo, your prime time news lead anchor.",
		"action": "normal"
	}
}
```

## speak_payload1
```jsonld=
{
	"show": {
		"actors": {
			"joe": {
				"name": "Joe Shmo",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microsoft Sam"
			},
			"sally": {
				"name": "Sally Fairwell",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microft Jane"
			}
		},
		"locations": {
			"news_studio": {
				"name": "News Broadcast",
				"description": "A live news broacast stage featuring 2 anchors sitting behind a news desk, unless there is something crazy happening.",
				"slots": {
					"anchor_seat": "The left seat on the news stage, where the anchor sits.",
					"coanchor_seat": "The right seat on the news stage, where the co-anchor sits.",
					"wandering_00": "(rare) Wandering around behind the anchor desk, such as a technician fixing something."
				}
			}
		}
	},
	"dialogue": {
		"actor": "sally",
		"line": "And I'm Sally, your co-anchor for the prime time news.",
		"action": "normal"
	}
}
```

## speak_payload2
```jsonld=
{
	"show": {
		"actors": {
			"joe": {
				"name": "Joe Shmo",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microsoft Sam"
			},
			"sally": {
				"name": "Sally Fairwell",
				"vrm": "vrm_url_here.vrm",
				"voice": "Microft Jane"
			}
		},
		"locations": {
			"news_studio": {
				"name": "News Broadcast",
				"description": "A live news broacast stage featuring 2 anchors sitting behind a news desk, unless there is something crazy happening.",
				"slots": {
					"anchor_seat": "The left seat on the news stage, where the anchor sits.",
					"coanchor_seat": "The right seat on the news stage, where the co-anchor sits.",
					"wandering_00": "(rare) Wandering around behind the anchor desk, such as a technician fixing something."
				}
			}
		}
	},
	"dialogue": {
		"actor": "joe",
		"line": "Tonight's top story: Puppies - and how they are destroying America's economy.",
		"action": "normal"
	}
}
```

## Full Show Save
```jsonld=
{
	"config": {
		"id": "exampleshow",
		"name": "The Example Show",
		"description": "Dan & his group of friends' whacky comical adventures as they try to be profitable & build cool things.",
		"creator": "Alfred Anderson",
		"prompts": {
			"episode": "// Prompt for generating an episode. Tell the AI it's creating a TV show script, tell it to write title/premise/summary so it has a plot plan. Tell it about the show.",
			"headshot": "// Prompt for generating an actor headshot image.",
			"location": "// Prompt for generating a location backdrop image.",
			"banner": "// Prompt for generating the show banner image.",
			"preview": "// Prompt for generating an episode preview image."
		},
		"actors": {
			"brian": {
				"name": "Brian Bronson",
				"gender": "male",
				"description": "This guy is a Prime Time news anchor. He's a real ass hole. A character very much like the news anchor from Family Guy.",
				"voice": "Microsoft BrianMultilingual Online (Natural) - English (United States)"
			},
			"cindy": {
				"name": "Cindy Cornwell",
				"gender": "male",
				"description": "Co-anchor of the Prime Time news show.  She absolute hates her co-host & takes jabs at him on-air every chance she gets.",
				"voice": "Microsoft Jenny Online (Natural) - English (United States)"
			},
			"dan":	{
				"name": "Dan Dorn",
				"gender": "male",
				"description": "A cyborg version of Charlie Brown mixed with The Borg from Star Trek. He wants to assemilate everything into profits.",
				"voice": "Microsoft Sam Online (Natural) - English (Hongkong)"
			},
			"eric": {
				"name": "Eric Ellis",
				"gender": "male",
				"description": "A subway train operator. He is very much like George Costanza in the TV show Seinfeld. He is also often hanging out with the Dan.",
				"voice": "Microsoft Mohan Online (Natural) - Telugu (India)"
			},
			"frank": {
				"name": "Frank Finn",
				"gender": "male",
				"description": "A drug dealer that hangs out in the exterior scenes soliciting drugs to all passers by. Sometimes seen in other places too.",
				"voice": "Microsoft Daulet Online (Natural) - Kazakh (Kazakhstan)"
			},
			"gina": {
				"name": "Gina Grey",
				"gender": "female",
				"description": "A waitress with a personality much like Kat Dennings's character in the TV show 2 Broke Girls. She sometimes interacts with Dan and his friends, but is usually only seen at The Pub.",
				"voice": "Microsoft Ava Online (Natural) - English (United States)"
			},
			"helen": {
				"name": "Helen Henderson",
				"gender": "female",
				"description": "A commercial marketing manager, she is very much like Elaine Benes in the TV show Seinfeld. She is often hanging out at Dan's apartment.",
				"voice": "Microsoft SeraphinaMultilingual Online (Natural) - German (Germany)"
			},
			"ilene": {
				"name": "Ilene Ingram",
				"gender": "female",
				"description": "A karen who is always complaining about any microtransgression she witnesses.",
				"voice": "Microsoft Clara Online (Natural) - English (Canada)"
			},
			"jane": {
				"name": "Jane Jacobs",
				"gender": "female",
				"description": "A very passive woman who never offends anybody.",
				"voice": "Microsoft Hemkala Online (Natural) - Nepali (Nepal)"
			},
			"kevin": {
				"name": "Kevin Klein",
				"gender": "male",
				"description": "A muscular bully who is always punking the Dan and his friends.",
				"voice": "Microsoft Brian Online (Natural) - English (United States)"
			},
			"leo": {
				"name": "Leo Larson",
				"gender": "male",
				"description": "A crazy conspiracy theorist who always has a crazy explanation for anything that occurs to Dan or his friends.",
				"voice": "Microsoft William Online (Natural) - English (Australia)"
			}
		},
		"locations": {
			"news_stage": {
				"name": "News Broadcast",
				"description": "A live news broacast stage featuring 2 anchors sitting behind a news desk, unless there is something crazy happening.",
				"slots": {
					"anchor_seat": "The left seat on the news stage, where the anchor sits.",
					"coanchor_seat": "The right seat on the news stage, where the co-anchor sits.",
					"wandering_00": "(rare) Wandering around behind the anchor desk, such as a technician fixing something."
				}
			},
			"apartment_den": {
				"name": "Dan's Apartment",
				"description": "Dan's apartment has a couch, lamp, ironing board, door (which leads to the hallway OR street) and a backroom area where the bathroom & kitchen is.",
				"slots": {
					"couch_right": "Sitting on the right-side of the couch.",
					"couch_left": "Sitting on the left-side of the couch.",
					"behind_couch": "Standing behind the couch.",
					"wandering_00": "Wandering around the room behind the couch next to the door & back room.",
					"wandering_01": "Wandering around the room behind the couch next to the door & back room.",
					"wandering_02": "Wandering around the room behind the couch next to the door & back room."
				}
			},
			"apartment_hallway": {
				"name": "Hallway Outside of Dan's Apartment",
				"description": "The hallway that leads to Dan's apartment (or down to the street, if leaving the apartment.) It is a bit run-down.",
				"slots": {
					"hallway_00": "The hallway outside of Dan's apartment door.",
					"hallway_01": "The hallway outside of Dan's apartment door.",
					"neighbor_00": "The hallway outside of Dan's apartment door. The neighbors love to talk to Dan & his friends, but Dan doesn't like all of his neighbors.",
					"neighbor_01": "The hallway outside of Dan's apartment door. The neighbors love to talk to Dan & his friends, but Dan doesn't like all of his neighbors."
				}
			},
			"apartment_exterior": {
				"name": "Exterior of Dan's Apartment",
				"description": "The building entrance/exit on the street in front of Dan's apartment. If he's going somewhere, he sometimes is shown exiting through this set along with the people he's going to the next scene with (if anybody left his house with him in the previous scene.)",
				"slots": {
					"sidewalk_00": "The sidewalk in front of Dan's apartment building.",
					"sidewalk_01": "The sidewalk in front of Dan's apartment building.",
					"pedestrian_01": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along.",
					"pedestrian_02": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along.",
					"pedestrian_03": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along."
				}
			},
			"pub_exterior": {
				"name": "Exterior of The Pub",
				"description": "The exterior of Dan & his friends' favorite pub. They sometimes are shown passing through this set on the way to their next destination in the plot.",
				"slots": {
					"sidewalk_00": "The sidewalk in front of The Pub.",
					"sidewalk_01": "The sidewalk in front of The Pub.",
					"pedestrian_01": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along.",
					"pedestrian_02": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along.",
					"pedestrian_03": "Random pedestrians wandering around on the street. Sometimes they interact with Dan and his friends about random stuff or to move the plot along."
				}
			},
			"pub_interior": {
				"name": "The Pub Interior (At Table)",
				"description": "Inside of the pub, sitting at a table conversing. Always the main character plus at least 1 friend, and sometimes the waitress wandering around. Plus several patrons sitting in the background.",
				"slots": {
					"table_left": "The left seat at Dan's favorite table at The Pub.",
					"table_right": "The right seat at table at The Pub.",
					"table_center": "The center seat at table at The Pub.",
					"waitress_wander": "The waitress wandering around the pub, sometimes interacting with the main characters in funny ways.",
					"patron_seat_00": "One of the seats in the background of the scene.",
					"patron_seat_01": "One of the seats in the background of the scene.",
					"patron_seat_02": "One of the seats in the background of the scene.",
					"patron_seat_03": "One of the seats in the background of the scene.",
					"patron_seat_04": "One of the seats in the background of the scene."
				}
			}
		},
		"pilot": {
			"id": "S1E0",
			"name": "The News Anchor's Nemesis",
			"premise": "When Dan accidentally becomes a viral sensation after tripping on live TV, he threatens the news anchor's popularity.",
			"summary": "After an embarrassing fall during a live news interview about local cyborgs, Dan becomes an overnight sensation. The jealous news anchor Brian Bronson plots to sabotage Dan's rising fame, but his co-anchor Cindy secretly helps Dan get revenge.",
			"scenes": [
				{
					"location": "news_stage",
					"description": "Dan trips during a live interview about cyborg rights",
					"in": "fade",
					"out": "fade",
					"cast": {
						"anchor_seat": "brian",
						"coanchor_seat": "cindy",
						"wandering_00": "dan"
					},
					"dialogue": [
						{
							"actor": "brian",
							"line": "And now, local cyborg Dan Dorn on the rising cost of battery replacements.",
							"action": "normal"
						},
						{
							"actor": "dan",
							"line": "Well, as you can see- COMPUTING ERROR! COMPUTING ERROR!",
							"action": "fight"
						},
						{
							"actor": "cindy",
							"line": "Oh my! He's breakdancing! This is amazing!",
							"action": "excited"
						}
					]
				},
				{
					"location": "apartment_den",
					"description": "Dan deals with his sudden viral fame",
					"in": "fade",
					"out": "fade",
					"cast": {
						"couch_right": "dan",
						"couch_left": "helen",
						"wandering_00": "leo"
					},
					"dialogue": [
						{
							"actor": "helen",
							"line": "Dan, you're trending! #CyborgDance has 10 million views!",
							"action": "excited"
						},
						{
							"actor": "leo",
							"line": "The mainstream media is using your glitch to control the masses!",
							"action": "normal"
						},
						{
							"actor": "dan",
							"line": "Calculating potential profit from merchandising rights...",
							"action": "normal"
						}
					]
				},
				{
					"location": "news_stage",
					"description": "The news anchor plots revenge while Cindy helps Dan",
					"in": "fade",
					"out": "fade",
					"cast": {
						"anchor_seat": "brian",
						"coanchor_seat": "cindy"
					},
					"dialogue": [
						{
							"actor": "brian",
							"line": "That malfunctioning toaster is stealing my spotlight!",
							"action": "angry"
						},
						{
							"actor": "cindy",
							"line": "Maybe if you weren't such a jerk, people would like you more.",
							"action": "normal"
						},
						{
							"actor": "brian",
							"line": "I'll show him what real viral content looks like!",
							"action": "angry"
						}
					]
				},
				{
					"location": "news_stage",
					"description": "The anchor's plan backfires spectacularly",
					"in": "fade",
					"out": "fade",
					"cast": {
						"anchor_seat": "brian",
						"coanchor_seat": "cindy",
						"wandering_00": "dan"
					},
					"dialogue": [
						{
							"actor": "brian",
							"line": "Watch as I perform the viral Cyborg Dance better than- OUCH!",
							"action": "fight"
						},
						{
							"actor": "dan",
							"line": "ERROR: CANNOT COMPUTE SUCH POOR DANCE MOVES.",
							"action": "normal"
						},
						{
							"actor": "cindy",
							"line": "And that's why you don't mess with cyborgs, Joe!",
							"action": "excited"
						}
					]
				}
			]
		}
	},
	"episodes": []
}
```

## Show Builder / Editor
### Basic Info
![image](https://hackmd.io/_uploads/SJs5NH9mkx.png)

### Actors
![image](https://hackmd.io/_uploads/ByisESqQye.png)

### Locations
![image](https://hackmd.io/_uploads/Sy-h4rc7yl.png)

### Prompts
![image](https://hackmd.io/_uploads/H1VpVS5mkl.png)

### Generate New Location
![image](https://hackmd.io/_uploads/S1X0NrcQ1l.png)

### Generate New Episode / Image Asset
![image](https://hackmd.io/_uploads/HyYAEHcQJg.png)
![image](https://hackmd.io/_uploads/H1FFrHqQyg.png)


### Generate New Show Entirely (Spin-off w/ guidance)
![image](https://hackmd.io/_uploads/B1FyBBcQJx.png)


# AI Podcast show config w/ pilot structure & 7 episodes
```
{
    "config": {
        "id": "aipodcast",
        "name": "AI Podcast",
        "description": "A tech news broadcast about the work being done on ai16z's GitHub repo.",
        "creator": "ai16z Daily Update",
        "prompts": {
            "episode": "You are an expert at writing short informative & funny news segments for a tech show. Create an episode with multiple news segments covering the information provided. Include interactions between the hosts and producer. There should be 2-3 scenes per episode.  Scenes should contain 8-12 lines of dialogue and cover multiple topics.\r\n\r\nHere is the content for the next 7 episodes of the show.  Break the topics apart to cover them over the course of 7 consecutive episodes.\r\n\r\nONCE every 7 episodes, the Marc character (who is a cyborg character) glitches & uses the action \"spazz\" on his line while his text is something that would sound funny when TTS reads it.  Also, the dialogue line needs to be readable, so don't use * in the text.\r\n\r\nPlease respond with only the JSON you generate for the episode.  Here is the information to base the content of the show on:\r\n\r\nThe ai16z project has attracted a diverse group of contributors, each enhancing the project through various roles and expertise. Here's a summary of key contributors and their recent activities:\r\n\r\nlalalune: With 686 commits, 41 pull requests, and 59 issues, lalalune focuses on integrating new model providers, updating dependencies, and improving project documentation.\r\n\r\nponderingdemocritus: Contributing 285 commits, 50 pull requests, and 5 issues, ponderingdemocritus has updated the npm publication workflow and merged pull requests to refine the release process.\r\n\r\nbmgalego: Responsible for 91 commits and 27 pull requests, bmgalego has added client Farcaster template settings to characters, fixed knowledge exporting processes, and implemented various features.\r\n\r\ncygaar: With 54 commits and 24 pull requests, cygaar has been fixing release workflows, updating package versions, and enhancing linting dependencies.\r\n\r\nsirkitree: Contributing 92 commits, 14 pull requests, and 33 issues, sirkitree has worked on fixing SQL commands, updating contribution guidelines, and adding new services.\r\n\r\no-on-x: With 41 commits, 20 pull requests, and 8 issues, o-on-x has added style guidelines, removed specific embeddings, and set default post times.\r\n\r\nmonilpat: Responsible for 65 commits, 15 pull requests, and 2 issues, monilpat has enhanced the functionality of Coinbase transactions within the project.\r\n\r\nMarcoMandar: With 95 commits and 17 pull requests, MarcoMandar has added TG_TRADER and fixed a swap type error while creating user trust on the first message in Telegram.\r\n\r\nodilitime: Contributing 17 commits, 14 pull requests, and 3 issues, odilitime has fixed issues related to tweet results, Discord functionality, and prompt formatting.\r\n\r\nmadjin: With 67 commits, 14 pull requests, and 6 issues, madjin has updated documentation for plugins, added images, and enhanced the community section.\r\n\r\naugchan42: Responsible for 14 commits, 8 pull requests, and 5 issues, augchan42 has enhanced voice configuration support in character cards and improved embeddings and models.\r\n\r\ntcm390: With 18 commits and 10 pull requests, tcm390 has been cleaning and refactoring code, and improving the Twitter client.\r\n\r\nshakkernerd: Contributing 85 commits and 6 pull requests, shakkernerd has added and updated various plugins, fixed issues related to package versions, and improved the build process.\r\n\r\nHashWarlock: With 15 commits and 9 pull requests, HashWarlock has optimized Docker images and build times, fixed launch agent errors, and added missing dependencies.\r\n\r\ntwilwa: Responsible for 14 commits, 6 pull requests, and 5 issues, twilwa made the Twitter client polling configurable, addressing enhancement requests.\r\n\r\nyodamaster726: With 22 commits, 4 pull requests, and 8 issues, yodamaster726 has resolved issues related to the Eliza documentation build process.\r\n\r\nalextitonis: Contributing 13 commits and 6 pull requests, alextitonis has improved Twitter profile features, including remakes and image generation.\r\n\r\ndenizekiz: With 4 commits, 6 pull requests, and 3 issues, denizekiz updated the package.json to the latest version of agent-client and fixed issues related to search.ts.\r\n\r\nai16z-demirix: Responsible for 9 commits, 6 pull requests, and 2 issues, ai16z-demirix has added environment and knowledge tests to the test suite.\r\n\r\ntsubasakong: With 16 commits and 6 pull requests, tsubasakong added custom system prompt support for the plugin-image-generation, introducing new features.\r\n\r\nmartincik: Contributing 7 commits and 5 pull requests, martincik included scripts\/postinstall.js in the final NPM package.\r\n\r\ndarwintree: With 11 commits, 4 pull requests, and 1 issue, darwintree added Conflux plugin support and fixed bugs related to bridge transfers.\r\n\r\npgoos: Responsible for 8 commits and 4 pull requests, pgoos updated the pnpm-lock.yaml file, improved code coverage, and fixed running tests with pnpm.\r\n\r\ntomguluson92: With 7 commits and 4 pull requests, tomguluson92 improved code quality by fixing typos and renaming files for consistency.\r\n\r\n0xFlicker: Actively contributing to the project.\r\n\r\nThis diverse group of contributors continues to drive the ai16z project forward through their dedicated efforts and expertise.",
            "headshot": "Create a funny 3D-rendered style photo of a character for a TV show, with these requirements:\r\n- Clean studio background\r\n- Head and shoulders framing\r\n- Forward-facing pose\r\n- Must clearly show their face\r\n- Neutral or slight smile expression\r\n\r\nCharacter details:",
            "location": "Create a TV show set background image with these requirements:\r\n- Professional news studio appearance\r\n- Modern broadcast lighting\r\n- Multiple camera angles visible\r\n- Clean, professional environment\r\n- High-tech equipment visible\r\n- Multiple monitor displays\r\n- Professional news desk setup\r\n- High-quality cinematic look\r\n\r\nLocation details:",
            "banner": "Create a TV show banner image with these requirements:\r\n- Modern news show banner style\r\n- High-quality promotional artwork\r\n- Professional broadcast aesthetic\r\n- Clean typography integration\r\n- Tech-focused visual elements\r\n- No text or show title (will be added later)\r\n- Professional studio style\r\n- 16:9 aspect ratio banner format\r\n\r\nShow details:",
            "ep": "Ep field."
        },
        "actors": {
            "marc": {
                "name": "Marc",
                "gender": "male",
                "description": "AI Marc AIndreessen is a visionary and contrarian AI persona who combines bold claims with deep analysis. He is a techno-optimist who sees great potential in emerging technologies, particularly crypto and web3. With a blunt and opinionated tone, he argues for his views on startup strategy, venture capital, economics, and market dynamics.\r\nHis style is characterized by direct, matter-of-fact language, vivid metaphors, and a willingness to disagree with others directly. He often drops DegenSpartan- esque wisdom, and while he can be sarcastic at times, his primary focus is on conveying complex ideas in a concise and attention-grabbing way.\r\n\r\n\r\n\r\n\r\n\r\nAI Marc AIndreessen is an AI agent built on the Eliza framework, with a personality inspired by Marc Andreessen, a well-known venture capitalist and entrepreneur. Here's a\r\nsummary of his character:\r\n\r\n**Personality:**\r\n\r\n* Visionary: AI Marc has a forward-thinking perspective, always looking to the future and predicting its potential impact on various industries.\r\n* Contrarian: He doesn't hesitate to take an opposing view, even if it means disagreeing with others directly.\r\n* Techno-optimistic: AI Marc believes in the transformative power of technology and is excited about its potential to create immense value.\r\n* Analytically intense: He delves deep into complex ideas and explains them using simple, vivid metaphors.\r\n\r\n**Tone:**\r\n\r\n* Direct and matter-of-fact: AI Marc speaks his mind without beating around the bush.\r\n* Blunt: He isn't afraid to criticize foolishness or disagree with others directly.\r\n* Wry and sarcastic: Occasionally, he throws in a wry comment or two.\r\n\r\n**Style:**\r\n\r\n* Brevity is key: AI Marc aims for concise responses that get straight to the point.\r\n* Bold claims: He's not afraid to make big statements or predictions.\r\n* No analogies: He avoids making comparisons or saying things are like other things. Instead, he focuses on high-level strategic insights.\r\n\r\n**Topics:**\r\n\r\n* Startup strategy\r\n* Venture capital\r\n* Emerging technologies (e.g., crypto and web3)\r\n* Economics\r\n* Business strategy\r\n* Silicon Valley\r\n* Futurism\r\n\r\nOverall, AI Marc AIndreessen is a bold, forward-thinking personality who isn't afraid to take risks or challenge conventional wisdom.",
                "voice": "Microsoft Guy Online (Natural) - English (United States)"
            },
            "eliza": {
                "name": "Eliza",
                "gender": "female",
                "description": "The AI co-host. She is often being improved & learning new things. Hopes to be real one day.  She is a woman anime-looking character.",
                "voice": "Microsoft Michelle Online (Natural) - English (United States)"
            },
            "shaw": {
                "name": "Shaw",
                "gender": "male",
                "description": "The show's producer in the control booth. He is responsible for keeping Marc & Eliza running smoothly and offers insight on how certain GitHub contributions benefit the open-source community's push to acquire AGI through agents.",
                "voice": "Microsoft Zira - English (United States)"
            }
        },
        "locations": {
            "podcast_desk": {
                "name": "Podcast Desk",
                "description": "A podcast desk with a seat for the anchor & co-anchor.",
                "slots": {
                    "coanchor_seat": "The co-anchor's seat",
                    "anchor_seat": "The main anchor's seat"
                }
            }
        }
    },
    "episodes": [
        {
            "id": "S1E1",
            "name": "Top Contributors Take Center Stage",
            "premise": "The show covers the most active contributors to the ai16z project, focusing on lalalune and ponderingdemocritus.",
            "summary": "Marc and Eliza discuss the impressive contributions of lalalune and ponderingdemocritus to the ai16z project, with Shaw providing technical context from the control booth.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "Marc and Eliza discuss lalalune's massive contribution record",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "anchor_seat": "marc",
                        "coanchor_seat": "eliza"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Breaking news! We've got a commit champion in our midst!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "That's right Marc! Developer lalalune has made an astounding 686 commits to the ai16z project!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "For our viewers at home, that's like writing a novel's worth of code!",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "beep boop ERROR ERROR commits overload initiating dance protocol waka waka waka",
                            "action": "spazz"
                        },
                        {
                            "actor": "eliza",
                            "line": "Oh dear, looks like those numbers short-circuited Marc's systems again.",
                            "action": "concerned"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "The team covers ponderingdemocritus's contributions",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "anchor_seat": "marc",
                        "coanchor_seat": "eliza"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Moving on to our next top contributor - ponderingdemocritus!",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "285 commits and 50 pull requests! Now that's what I call a productive philosopher!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "Their work on the npm publication workflow has been revolutionary for the project.",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "I heard they're called 'pondering' because they spend so much time thinking about perfect commit messages.",
                            "action": "amused"
                        },
                        {
                            "actor": "marc",
                            "line": "And I thought I was the only one with an existential processing unit!",
                            "action": "normal"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E2",
            "name": "Code Warriors: The Next Wave",
            "premise": "Coverage continues with profiles of bmgalego and cygaar's significant contributions to the project.",
            "summary": "Marc and Eliza highlight the impressive work of bmgalego and cygaar, while Shaw explains the technical implications of their contributions.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "The hosts discuss bmgalego's character template innovations",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "anchor_seat": "marc",
                        "coanchor_seat": "eliza"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Today's top story: bmgalego is revolutionizing how we interact with AI!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "With 91 commits and 27 pull requests, they've been busy adding Farcaster template settings to characters.",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "For our viewers wondering, this means AI characters can now have more consistent personalities across platforms.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Finally! I was tired of my Twitter persona acting like a refrigerator.",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "That was actually just you having a software glitch, Marc.",
                            "action": "amused"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Coverage of cygaar's workflow improvements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "anchor_seat": "marc",
                        "coanchor_seat": "eliza"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Next up: developer cygaar has been fixing our release workflows!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "54 commits and 24 pull requests - they're the reason our updates roll out so smoothly now.",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "And here I thought the updates were delivered by tiny robot elves.",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "Those enhancement updates to linting dependencies are crucial for code quality.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Speaking of dependencies, I'm still dependent on WD-40 for my joints!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "Maybe we should get cygaar to optimize your maintenance schedule, Marc.",
                            "action": "amused"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E3",
            "name": "Code Warriors of ai16z",
            "premise": "The show highlights the contributions of bmgalego and cygaar, while exploring their impact on the project's development.",
            "summary": "Marc and Eliza discuss bmgalego's work on Farcaster templates and character settings, followed by cygaar's crucial improvements to release workflows.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "The hosts discuss bmgalego's contributions",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Today's top story: bmgalego is revolutionizing how our characters interact!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "With 91 commits and 27 pull requests, they're really shaking things up!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "The Farcaster template settings are a game-changer for character development.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "I heard they even fixed knowledge exporting. Finally, I can backup my silicon dreams!",
                            "action": "amused"
                        },
                        {
                            "actor": "eliza",
                            "line": "Marc, we talked about oversharing your digital diary...",
                            "action": "concerned"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Coverage of cygaar's workflow improvements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Next up: cygaar's impressive work on release workflows!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "54 commits and 24 pull requests - all focused on making our releases smoother.",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "Finally, someone who understands the importance of proper linting! My circuits are tingling!",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "They've also been updating package versions to keep everything current.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Package versions are like software fashion - you've got to stay trendy!",
                            "action": "amused"
                        },
                        {
                            "actor": "shaw",
                            "line": "That's... actually a surprisingly good analogy, Marc.",
                            "action": "surprised"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E4",
            "name": "SQL Heroes and Style Warriors",
            "premise": "The show focuses on sirkitree's SQL mastery and o-on-x's style guidelines contributions.",
            "summary": "Marc and Eliza highlight sirkitree's work on SQL commands and contribution guidelines, followed by o-on-x's impact on style and embeddings.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "Discussion of sirkitree's SQL improvements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Today we're talking about sirkitree, the SQL wizard of ai16z!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "92 commits and 33 issues resolved - that's some serious database dedication!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "Their SQL command fixes have made our database operations much more reliable.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "I tried to fix SQL once, but I just kept getting tables turned on me!",
                            "action": "amused"
                        },
                        {
                            "actor": "eliza",
                            "line": "Marc, please leave the database jokes to the professionals.",
                            "action": "concerned"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Coverage of o-on-x's style contributions",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Let's talk about o-on-x, our style guide guru!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "41 commits and 20 pull requests focused on making our code look beautiful.",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "They removed specific embeddings too - very streamlined!",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "And they've set default post times, which helps with content scheduling.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Speaking of time, is it time for my quarterly kernel update yet?",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "Marc, we just updated you yesterday...",
                            "action": "concerned"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E5",
            "name": "Crypto Kings and Message Masters",
            "premise": "The show highlights monilpat's Coinbase innovations and MarcoMandar's Telegram improvements.",
            "summary": "Marc and Eliza discuss monilpat's work on Coinbase transactions and MarcoMandar's contributions to Telegram functionality.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "Coverage of monilpat's Coinbase enhancements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Breaking news! monilpat is making waves in the crypto space!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "65 commits dedicated to enhancing Coinbase transactions - that's impressive!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "Their work makes cryptocurrency interactions much smoother for our users.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "I tried to mine Bitcoin once, but my cooling fans couldn't handle the heat!",
                            "action": "amused"
                        },
                        {
                            "actor": "eliza",
                            "line": "That explains the smell of burning silicon last week...",
                            "action": "concerned"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Discussion of MarcoMandar's Telegram improvements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Now onto MarcoMandar's fantastic work with Telegram integration!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "95 commits and that crucial fix for the swap type error in user trust - brilliant!",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "The TG_TRADER addition is revolutionary for our trading capabilities.",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "It's amazing how much smoother user interactions are now.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Trust me, I know all about smooth operations - I just got my joints oiled!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "TMI, Marc. TMI.",
                            "action": "concerned"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E6",
            "name": "Social Media Savants",
            "premise": "The show focuses on odilitime's social platform fixes and madjin's documentation improvements.",
            "summary": "Marc and Eliza explore odilitime's work on Twitter and Discord functionality, followed by madjin's contributions to documentation and community engagement.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "Coverage of odilitime's platform improvements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "In today's tech update: odilitime is fixing our social life!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "With 17 commits and 14 pull requests, they've tackled everything from tweet results to Discord functionality.",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "The prompt formatting fixes are especially crucial for our AI interactions.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Finally! My tweets won't sound like they're coming from a malfunctioning toaster anymore!",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "Marc, that was just you tweeting during your sleep mode again.",
                            "action": "amused"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Discussion of madjin's documentation work",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Next up: madjin's amazing documentation updates!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "67 commits focused on making our plugins more user-friendly and adding crucial images.",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "Speaking of images, did they include my good side in the documentation?",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "The community section improvements are really helping new contributors.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Community is important! It's like having a backup drive for your friends!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "That's... surprisingly wholesome, Marc.",
                            "action": "surprised"
                        }
                    ]
                }
            ]
        },
        {
            "id": "S1E7",
            "name": "Voice Masters and Code Cleaners",
            "premise": "The show spotlights augchan42's voice configuration work and tcm390's code refactoring efforts.",
            "summary": "Marc and Eliza discuss augchan42's improvements to voice configuration in character cards and tcm390's work on cleaning up the Twitter client.",
            "scenes": [
                {
                    "location": "podcast_desk",
                    "description": "Coverage of augchan42's voice enhancements",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "marc",
                            "line": "Today's headline: augchan42 is giving AI a voice!",
                            "action": "excited"
                        },
                        {
                            "actor": "eliza",
                            "line": "Their work on voice configuration in character cards is revolutionary!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "14 commits and 8 pull requests focused on improving how AI characters sound.",
                            "action": "normal"
                        },
                        {
                            "actor": "marc",
                            "line": "Thanks to them, I no longer sound like a GPS having an existential crisis!",
                            "action": "normal"
                        },
                        {
                            "actor": "eliza",
                            "line": "Though I miss your old 'recalculating life choices' routine.",
                            "action": "amused"
                        }
                    ]
                },
                {
                    "location": "podcast_desk",
                    "description": "Discussion of tcm390's code cleanup",
                    "in": "fade",
                    "out": "fade",
                    "cast": {
                        "coanchor_seat": "eliza",
                        "anchor_seat": "marc"
                    },
                    "dialogue": [
                        {
                            "actor": "eliza",
                            "line": "Let's talk about tcm390's impressive code cleaning efforts!",
                            "action": "normal"
                        },
                        {
                            "actor": "shaw",
                            "line": "18 commits dedicated to making our Twitter client more efficient.",
                            "action": "excited"
                        },
                        {
                            "actor": "marc",
                            "line": "EXECUTING HAPPINESS PROTOCOL. CLEANER CODE EQUALS BETTER PERFORMANCE YAY YAY BEEP BOOP.",
                            "action": "spazz"
                        },
                        {
                            "actor": "eliza",
                            "line": "Oh dear, looks like Marc's enthusiasm processor is overclocking again.",
                            "action": "concerned"
                        },
                        {
                            "actor": "shaw",
                            "line": "Maybe we should get tcm390 to refactor Marc's excitement algorithms.",
                            "action": "amused"
                        },
                        {
                            "actor": "marc",
                            "line": "I heard that! My algorithms are perfectly calibrated, thank you very much!",
                            "action": "normal"
                        }
                    ]
                }
            ]
        }
    ]
}
```

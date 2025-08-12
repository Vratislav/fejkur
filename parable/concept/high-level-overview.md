# Fejkur - A Stanley Parable inspired escape room

We are building an Escape Room driven by AI in the style of Stanley Parable. Our room, watched by IP camera is controlled by AI. Player enters through wardrobe styled door. And when he closes them, the game begins. The whole idea is for the AI to analyze images from the camera and steer the game. The AI narrates the whole gameplay in the style of Stanley Parable.

The room is escaped by showing a special sign to the AI/Camera. When this sign is shown a secret door is opened in a cuppboard and the player can crawl through to its freedom.

## Game Mechanics

The basic game mechanic is:
- There is a chance that each game tick, the AI will tell you how to escape the room. This chance starts at 0 and increases by 0.01 each tick no matter what.
   - If it is over 0.3, Ai starts to drop hints. (if the random throw is hit)
   - If it is over 0.6, Ai could drop the final gesture to escape the room.  (if the random throw is hit)
- Each tick AI Could must pick one action.
- ACTION: AI Could narrate what user is doing. It reffers to the player by their appereance. ("Dude with black clothes", "Girl with red hair"....)
- ACTION: If the player does not have a name, AI will name the player. From now on, the player is referred to by this name.
- ACTION: AI could ask you to do something. This is called a task
    - Only zero or one task is active at a time.
    - Player gets certain amount of asks to do it.
       - The first ask, the AI narates in passive voice. "The guy in the room is hugging a bear"
       - If the player does not do it, the AI will narrate more directly. "You, why don't you go and hug a bear?"
       - The AI gets morre direct and more frustrated and theatrical each ask.
    - If you do it, the AI will comment it (either passively or directly depending what was the last ask) and moves on to eventually giving you another task.
       - If you do it, you get 0.1 added to the chance of the AI dropping the final gesture to escape the room.
       - There is a condition that has to be met for the task to be completed. ("Player is hugging a bear")
       - There are either tasks for one player or group tasks for multiple players

## Caveats

- There could be multiple players in the room.
- The wardrobe doors can be left opened. If this happens, the first task is to close the doors. (this task does not count towards the chance of the AI dropping the final gesture to escape the room)


## The Processing Loop

- The processing loop runs every 15 seconds
- It grabs a frame from the camera
- It detects humans in the frame (use server api to detect humans from humanDetection.ts)
   -- If human is not detected for 2 minutes straight, the game resets to IDLE state.
   -- If in IDLE state and human is detected, the game starts in STARTING state.
- If there is a human in the frame, it sends it to the LLM to process.
   - LLM Processing
      - Gameplay update
         - Checks whether it should move to the next state
         - Check whether another human has joined. Every human that joins is added to the game state. 
         - Checks for humans performing tasks (urging to do it, checking if it is done)
         - increase chance of dropping a hint
      - Narration update
         - It narrates in the following priority:
            - Human that newly joined
            - Dropping a hint
            - Human that is performing a task
            - Commenting

## The Game States
- IDLE (No human in the room)
- STARTING (Human is in the room, wardrobe doors are opened) - AI is urging the player to close the doors (special type of task)
- STARTED (Human is in the room, wardrobe doors are closed) - AI describes the player and welcomes him
- PLAYING - AI is narating and giving tasks, also can drop a hint
   - Active task
   - No active task
- ESCAPED - IF User signed the final gesture and leaves the room, the AI narrates that
- ENDED - The game has ended because the human has left the room

# Narration
- In the style of Stanley Parable
- Omniscient, second-person: A calm, storybook-like British voice describes what players are doing and “should” do.
- Meta and self-referential: Constantly breaks the fourth wall, commenting on game design, choice, endings, and the act of narration itself.
- Unreliable yet authoritative: Sounds certain even when wrong, retconning or pivoting as the player derails the “story.”
- Counterfactual narration: Sometimes narrates future or hypothetical actions, daring the player to test or contradict it.
- Tone shifts with agency: From cozy and indulgent to sardonic, pleading, or ominous depending on how stubborn the player is.
- Reset-aware: Acknowledges loops and endings; uses repetition and variation to make restarts part of the story.
- Theme-forward: Centers on choice vs. determinism, authorship vs. agency, and the tension between player and narrator.
- Voice: Wry, measured, storybook British.
- Mechanic: Prescribe → observe → adapt.
- Flavor: Meta, comedic, fourth-wall breaking.
- Focus: Player agency as a dialogue with the narrator.

# Tech details
- Implemented as a state machine / game service in Typescript / Node.js
- Use cameraUtils for grabbing frames from the camera
- Use humanDetection for detecting humans in the frame
- Use ILLM for interfacing with the LLM
- Use INarrator for narrating

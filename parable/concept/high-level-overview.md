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
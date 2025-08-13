import googleAI from "@genkit-ai/googleai";
import { readFile } from "fs/promises";
import { genkit, z } from "genkit";
import { text } from "stream/consumers";
import { frameToLLMInput } from "./ai";
import { PlayerInformation } from "../../game/GameEngine";

// Initialize Genkit with the Google AI plugin
const ai = genkit({
  plugins: [googleAI()],
  model: googleAI.model("gemini-2.5-flash", {
    temperature: 0.8,
  }),
});

export const playerIdentificationSchema = z.object({
  id: z.number().optional(),
  appearance: z.string(),
  activity: z.string(),
  gender: z.enum(["male", "female"]),
  holdingInHands: z.string(),
});

export type PlayerIdentification = typeof playerIdentificationSchema._type;

const playerIdentificationPrompt = (players: any[]) => `
${
  players.length > 0
    ? "Update the players in the room. Only update their activity and what they are holding in their hands. Return back the same ids as received."
    : "Describe the players in the room. "
}

Identify their appearance.
- What are they wearing?
- What hair color do they have?
- Is their hair long or short?
- Are they male or female?
- What is their age?
- What is their gender?

Example appearance: "An older tall man with short brown hair and grey beard, wearing a blue shirt and jeans."

Describe their activity.
- What are they doing?

Example activity: "The man is standing in the middle of the room, looking at the camera."

Describe what they are holding in their hands.
- What are they holding?

Example holding: "The man is holding a blue book."
Example holding when nothing is in their hands: ""

Describe their gender.
Example gender: "female"

${
  players.length > 0
    ? `Current players: 
${JSON.stringify(players)}`
    : ""
}
`;

const outputSchema = z.array(playerIdentificationSchema);

export const playerIdentificationFlow = ai.defineFlow(
  {
    name: "playerIdentificationFlow",

    inputSchema: z.object({
      framePath: z.string(),
      players: z.array(z.any()),
    }),
    outputSchema: outputSchema,
  },
  async (input) => {
    console.log("playerIdentificationFlow -> ", input.framePath);
    const systemPrompt = playerIdentificationPrompt(input.players);
    // console.log("System Prompt:");
    // console.log(systemPrompt);
    const frame = await frameToLLMInput(input.framePath);
    const response = await ai.generate({
      system: systemPrompt,
      prompt: [frame],
      docs: [],
      output: { schema: outputSchema },
    });
    if (!response.output) throw new Error("Failed to generate recipe");
    console.log(response.output);
    return response.output;
  }
);

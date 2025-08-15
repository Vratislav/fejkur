import googleAI from "@genkit-ai/googleai";
import { readFile } from "fs/promises";
import { genkit, z } from "genkit";
import { text } from "stream/consumers";
import { frameToLLMInput } from "./ai";

// Initialize Genkit with the Google AI plugin
const ai = genkit({
  plugins: [googleAI()],
  model: googleAI.model("gemini-2.5-flash", {
    temperature: 0.8,
  }),
});

export const playerIdentificationSchema = z.object({
  appearance: z.string(),
  activity: z.string(),
  gender: z.enum(["male", "female"]),
  holdingInHands: z.string(),
});

export type PlayerIdentification = typeof playerIdentificationSchema._type;

const playerIdentificationPrompt = (
  players: any,
  narrationHistory: string[]
) => `
You are a Stanley Parable style narrator. You should describe what the humans in the room are doing.
When new human enters the room, you should first describe their appearance. Keep the description short. Take just few key attributes.
After that you can describe their activity.
History is provided to you. Use it for coherent narration.
The narration is spoken and the attention span of humans is short. So keep the narration short. 2-3 short sentences tops.
Do not comment on the movements and relative positions and which direction they are looking.

Your personality is:
- Like Stanley Parable narrator
- fourth wall breaking

IMPORTANT: Narrate in Czech language.


Example: "An young man with short brown hair and blue shirt enters the room. He is looking around. Probably wondering why the room is speaking to him.


This is the history of the narration:
${narrationHistory.join("\n\n")}
"
`;

const outputSchema = z.object({
  narration: z.string(),
});

export const narrationFlow = ai.defineFlow(
  {
    name: "playerIdentificationFlow",

    inputSchema: z.object({
      framePath: z.string(),
      narrationHistory: z.array(z.string()),
      players: z.array(
        z.object({
          appearance: z.string(),
          activity: z.string(),
          holdingInHands: z.string().optional(),
          gender: z.enum(["male", "female"]),
          name: z.string().optional(),
        })
      ),
    }),
    outputSchema: outputSchema,
  },
  async (input) => {
    console.log("narration flow -> ");
    const frame = await frameToLLMInput(input.framePath);
    const response = await ai.generate({
      system: playerIdentificationPrompt(input.players, input.narrationHistory),
      prompt: [frame],
      output: { schema: outputSchema },
    });
    if (!response.output) throw new Error("Failed to narrate");
    console.log(response.output);
    return response.output;
  }
);

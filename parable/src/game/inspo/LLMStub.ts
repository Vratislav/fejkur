import z from "zod";
import { ILLM, LLMCallResult, LLMHistoryItem } from "../lLLM";

export class StubLLM implements ILLM {
  async callLLM<TResponse>(opts: {
    systemPrompt: string;
    history: LLMHistoryItem[];
    prompt: string;
    responseFormat?: z.ZodSchema<TResponse>;
    imagePath?: string | undefined;
  }): Promise<LLMCallResult<TResponse>> {
    const simulated: any = {
      observation: "A person stands in the room.",
      taskCompleted: false,
      narration:
        "You, yes you, the one pretending not to listen—close the wardrobe doors, would you? It will make us both feel better.",
      hint: null,
    };
    const validated = opts.responseFormat
      ? opts.responseFormat.parse(simulated)
      : simulated;
    return { content: validated } as LLMCallResult<TResponse>;
  }
}

import z from "zod";

export interface ILLM {
  callLLM<TResponse>(opts: {
    systemPrompt: string;
    history: LLMHistoryItem[];
    prompt: string;
    responseFormat?: z.ZodSchema<TResponse>;
    imagePath?: string;
  }): Promise<LLMCallResult<TResponse>>;
}

export interface LLMCallResult<TResponse> {
  content: TResponse;
}

export interface LLMHistoryItem {
  role: "user" | "assistant";
  content: string;
}

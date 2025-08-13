import { readFile } from "fs/promises";

export async function frameToLLMInput(framePath: string) {
  const data = await readFile(framePath);
  return {
    media: { url: `data:image/jpeg;base64,${data.toString("base64")}` },
  };
}

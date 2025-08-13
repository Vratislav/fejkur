import { ElevenLabsClient, stream } from "elevenlabs";
import { INarrator } from "../../INarrator";

export class ConsoleNarrator implements INarrator {
  useTextToSpeech: boolean;
  client?: ElevenLabsClient;

  constructor(useTextToSpeech: boolean) {
    this.useTextToSpeech = useTextToSpeech;
  }

  async narrate(whatToSay: string): Promise<void> {
    // eslint-disable-next-line no-console
    console.log(`[NARRATOR] ${whatToSay}`);
    if (this.useTextToSpeech) {
      if (!this.client) {
        this.client = new ElevenLabsClient({
          apiKey: process.env.ELEVENLABS_API_KEY,
        });
      }
      const audioStream = await this.client.textToSpeech.convertAsStream(
        "7e2p09M5txOQndhE2bMk",
        {
          text: whatToSay,
          model_id: "eleven_turbo_v2_5",
        }
      );
      await stream(audioStream);
    }
  }
}

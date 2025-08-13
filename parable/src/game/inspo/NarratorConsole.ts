import { INarrator } from "../INarrator";

export class ConsoleNarrator implements INarrator {
  async narrate(whatToSay: string): Promise<void> {
    // eslint-disable-next-line no-console
    console.log(`[NARRATOR] ${whatToSay}`);
  }
}

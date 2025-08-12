export interface INarrator {
  narrate(whatToSay: string): Promise<void>;
}

import { HumanDetectionResult } from "../humanDetection";
import { IHumanDetector } from "./IHumanDetector";

export class RealHumanDetector implements IHumanDetector {
  async detectHumans(frame: string): Promise<HumanDetectionResult> {
    return { humansDetected: false, humansCount: 0 };
  }
}

export class NoHumanDetector implements IHumanDetector {
  async detectHumans(frame: string): Promise<HumanDetectionResult> {
    return { humansDetected: false, humansCount: 0 };
  }
}

export class OneHumanDetector implements IHumanDetector {
  async detectHumans(frame: string): Promise<HumanDetectionResult> {
    return { humansDetected: true, humansCount: 1 };
  }
}

import { HumanDetectionResult } from "../humanDetection";

export interface IHumanDetector {
  detectHumans(frame: string): Promise<HumanDetectionResult>;
}

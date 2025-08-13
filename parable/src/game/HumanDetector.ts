import {
  HumanDetectionResult,
  HumanDetectionOptions,
  detectHumans,
} from "../humanDetection";
import { IHumanDetector } from "./IHumanDetector";

export class RealHumanDetector implements IHumanDetector {
  private readonly options: HumanDetectionOptions;

  constructor(options?: HumanDetectionOptions) {
    const envConf = process.env.FEJKUR_YOLO_CONF
      ? Number(process.env.FEJKUR_YOLO_CONF)
      : undefined;

    this.options = {
      serverUrl: process.env.FEJKUR_YOLO_SERVER_URL,
      confidence: envConf,
      ...options,
      useServer: true,
    };
  }

  async detectHumans(frame: string): Promise<HumanDetectionResult> {
    return await detectHumans(frame, this.options);
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

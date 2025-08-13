import { HumanDetectionResult } from "../humanDetection";
import { INarrator } from "../INarrator";
import { ILLM } from "../lLLM";
import { ICameraFrameProvider } from "./ICameraFrameProvider";
import { IHumanDetector } from "./IHumanDetector";

export interface GameEngineOpts {
  frameProvider: ICameraFrameProvider;
  llm: ILLM;
  narrator: INarrator;
  humanDetector: IHumanDetector;
  tickMs: number;
  maxFrameStalenessMs: number;
  maxTimeIntervalWithoutHumanMs: number;
}

export enum GameEngineState {
  IDLE,
  STARTING,
  STARTED,
  PLAYING,
  ESCAPED,
  ENDED,
}

export class GameEngine {
  readonly opts: GameEngineOpts;
  readonly frameProvider: ICameraFrameProvider;
  readonly humanDetector: IHumanDetector;
  lastTickWithHumanTimestamp: number = 0;
  intervalHandle?: NodeJS.Timeout;
  state: GameEngineState = GameEngineState.IDLE;

  constructor(opts: GameEngineOpts) {
    this.opts = opts;
    this.humanDetector = opts.humanDetector;
    this.frameProvider = opts.frameProvider;
  }

  async startEngine() {
    this.intervalHandle = setInterval(async () => {
      const frame = await this.frameProvider.getLatestFrame();
      if (Date.now() - frame.timestamp > this.opts.maxFrameStalenessMs) {
        console.log(`Frame is stale, skipping: ${frame.path}`);
        return;
      }
      //Run the human detection
      const humanDetectionResult = await this.humanDetector.detectHumans(
        frame.path
      );
      await this.checkForHumanStalenessAndResetGame(humanDetectionResult);
      await this.doGameTick(frame.path, humanDetectionResult);
    }, this.opts.tickMs);
  }

  async resetGame() {
    this.transitionToState(GameEngineState.IDLE);
    console.log("GAME RESET");
  }

  async checkForHumanStalenessAndResetGame(detection: HumanDetectionResult) {
    if (detection.humansDetected) {
      this.lastTickWithHumanTimestamp = Date.now();
    }
    const timeSinceLastHuman = Date.now() - this.lastTickWithHumanTimestamp;
    if (timeSinceLastHuman > this.opts.maxTimeIntervalWithoutHumanMs) {
      console.log("No humans detected for too long. Reseting the game.");
      await this.resetGame();
    }
  }

  private transitionToState(newState: GameEngineState) {
    const oldState = this.state;
    console.log(`⏩ STATE ${oldState} => ${newState}`);
    this.state = newState;
  }

  async doGameTick(frame: string, detection: HumanDetectionResult) {
    if (this.state == GameEngineState.IDLE && detection.humansDetected) {
      this.transitionToState(GameEngineState.STARTED);
    }
    if (this.state == GameEngineState.STARTED) {
      await this.doStartedGameTick(frame, detection);
    }
  }

  async doStartedGameTick(frame: string, detection: HumanDetectionResult) {
    this.transitionToState(GameEngineState.PLAYING);
  }
}

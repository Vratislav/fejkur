import { playerIdentificationFlow } from "../ai/flows/playerIdentificationFlow";
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
  stepThroughTicks?: boolean;
}

export interface PlayerInformation {
  appearance: string;
  activity: string;
  holdingInHands?: string;
  gender: "male" | "female";
  name?: string;
}

export enum GameEngineState {
  IDLE = "IDLE",
  STARTING = "STARTING",
  STARTED = "STARTED",
  PLAYING = "PLAYING",
  ESCAPED = "ESCAPED",
  ENDED = "ENDED",
}

export class GameEngine {
  readonly opts: GameEngineOpts;
  readonly frameProvider: ICameraFrameProvider;
  readonly humanDetector: IHumanDetector;
  lastTickWithHumanTimestamp: number = Date.now();
  amountOfTicksWithHuman: number = 0;
  dropHintChance: number = 0.0;
  intervalHandle?: NodeJS.Timeout;
  players: PlayerInformation[] = [];
  state: GameEngineState = GameEngineState.IDLE;

  constructor(opts: GameEngineOpts) {
    this.opts = opts;
    this.humanDetector = opts.humanDetector;
    this.frameProvider = opts.frameProvider;
  }

  async startEngine() {
    console.log("FEJKUR GAME ENGINE STARTED");
    if (this.opts.stepThroughTicks) {
      console.log("STEP THROUGH ENABLED!");
    }
    await this.doTick();
  }

  async doTick() {
    const processTickStart = Date.now();
    const frame = await this.frameProvider.getLatestFrame();
    if (Date.now() - frame.timestamp > this.opts.maxFrameStalenessMs) {
      console.log(`Frame is stale, skipping: ${frame.path}`);
      return;
    }
    //Run the human detection
    const humanDetectionResult = await this.humanDetector.detectHumans(
      frame.path
    );
    console.log(`Humans: ${humanDetectionResult.humansCount}`);
    await this.checkForHumanStalenessAndResetGame(humanDetectionResult);
    await this.doGameTick(frame.path, humanDetectionResult);
    const processTickEnd = Date.now();
    const processTickDuration = processTickEnd - processTickStart;
    console.log(`Tick took ${processTickDuration}ms`);
    if (this.opts.stepThroughTicks) {
      console.log("press any Key...");
      //Wait for enter key to be pressed
      process.stdin.once("data", async () => {
        this.intervalHandle = setTimeout(async () => {
          await this.doTick();
        }, 0);
      });
    } else {
      this.intervalHandle = setTimeout(async () => {
        await this.doTick();
      }, Math.max(0, this.opts.tickMs - processTickDuration));
    }
  }

  async resetGame() {
    this.transitionToState(GameEngineState.IDLE);
    this.amountOfTicksWithHuman = 0;
    this.players = [];
    console.log("GAME RESET");
  }

  async checkForHumanStalenessAndResetGame(detection: HumanDetectionResult) {
    if (detection.humansDetected) {
      this.lastTickWithHumanTimestamp = Date.now();
      this.amountOfTicksWithHuman++;
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
    if (
      this.state == GameEngineState.IDLE &&
      detection.humansDetected &&
      this.amountOfTicksWithHuman >= 2
    ) {
      this.transitionToState(GameEngineState.STARTED);
    }
    if (this.state == GameEngineState.STARTED) {
      await this.doStartedGameTick(frame, detection);
      return;
    }
  }

  private async identifyPlayers(frame: string): Promise<PlayerInformation[]> {
    const playersFromLLM = await playerIdentificationFlow({
      framePath: frame,
    });

    return playersFromLLM.map((player): PlayerInformation => {
      return {
        ...player,
        holdingInHands: player.holdingInHands || undefined,
      };
    });
  }

  async doStartedGameTick(frame: string, detection: HumanDetectionResult) {
    this.players = await this.identifyPlayers(frame);

    if (this.players.length > 0) {
      console.log("Players identified:");
      console.log(this.players);
      this.transitionToState(GameEngineState.PLAYING);
    }
  }
}

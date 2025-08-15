import { narrationFlow } from "../ai/flows/narrationFlow";
import { playerIdentificationFlow } from "../ai/flows/playerIdentificationFlow";
import { HumanDetectionResult } from "../humanDetection";
import { INarrator } from "../INarrator";
import { ILLM } from "../lLLM";
import { Frame, ICameraFrameProvider } from "./ICameraFrameProvider";
import { IHumanDetector } from "./IHumanDetector";

export interface GameEngineOpts {
  frameProvider: ICameraFrameProvider;
  llm: ILLM;
  narrator: INarrator;
  humanDetector: IHumanDetector;
  tickMs: number;
  delayTickAfterNarrationMs: number;
  maxFrameStalenessMs: number;
  maxTimeIntervalWithoutHumanMs: number;
  stepThroughTicks?: boolean;
}

export interface PlayerInformation {
  id: number;
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
  readonly narrator: INarrator;
  lastTickWithHumanTimestamp: number = Date.now();
  amountOfTicksWithHuman: number = 0;
  dropHintChance: number = 0.0;
  currentTickDelayMs: number = 0;
  intervalHandle?: NodeJS.Timeout;
  narrationHistory: string[] = [];
  players: PlayerInformation[] = [];
  state: GameEngineState = GameEngineState.IDLE;

  constructor(opts: GameEngineOpts) {
    this.opts = opts;
    this.humanDetector = opts.humanDetector;
    this.frameProvider = opts.frameProvider;
    this.narrator = opts.narrator;
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

    let frame: Frame | undefined = undefined;
    try {
      frame = await this.frameProvider.getLatestFrame();
    } catch (e) {
      console.log("Error getting frame: ", e);
      return;
    }
    if (frame) {
      if (Date.now() - frame.timestamp > this.opts.maxFrameStalenessMs) {
        console.log(`Frame is stale, skipping: ${frame.path}`);
        return;
      }
      try {
        //Run the human detection
        const humanDetectionResult = await this.humanDetector.detectHumans(
          frame.path
        );
        console.log(`Humans: ${humanDetectionResult.humansCount}`);
        await this.checkForHumanStalenessAndResetGame(humanDetectionResult);

        await this.doGameTick(frame.path, humanDetectionResult);
      } catch (e) {
        console.log("Error in GameEngine.doTick(): ", e);
      }
    }

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
      const nextTickInMs =
        Math.max(0, this.opts.tickMs - processTickDuration) +
        this.currentTickDelayMs;
      console.log(`Next tick in: ${nextTickInMs}ms`);
      this.intervalHandle = setTimeout(async () => {
        await this.doTick();
      }, nextTickInMs);
    }
  }

  async resetGame() {
    this.transitionToState(GameEngineState.IDLE);
    this.amountOfTicksWithHuman = 0;
    this.currentTickDelayMs = 0;
    this.players = [];
    this.narrationHistory = [];
    console.log("GAME RESET");
  }

  async checkForHumanStalenessAndResetGame(detection: HumanDetectionResult) {
    if (detection.humansDetected) {
      this.lastTickWithHumanTimestamp = Date.now();
      this.amountOfTicksWithHuman++;
    }
    const timeSinceLastHuman = Date.now() - this.lastTickWithHumanTimestamp;
    if (timeSinceLastHuman > this.opts.maxTimeIntervalWithoutHumanMs) {
      if (this.state != GameEngineState.IDLE) {
        console.log("No humans detected for too long. Reseting the game.");
        await this.resetGame();
      }
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
    if (this.state == GameEngineState.PLAYING) {
      await this.doPlayingGameTick(frame, detection);
    }
  }

  private async identifyPlayers(
    frame: string,
    currentPlayers: PlayerInformation[]
  ): Promise<PlayerInformation[]> {
    const playersFromLLM = await playerIdentificationFlow({
      framePath: frame,
      players: currentPlayers,
    });
    let runningPlayerId = 1;
    return playersFromLLM.map((player): PlayerInformation => {
      const toReturn = {
        id: player.id ?? runningPlayerId,
        ...player,
        holdingInHands: player.holdingInHands || undefined,
      };
      runningPlayerId++;
      return toReturn;
    });
  }

  async doPlayingGameTick(frame: string, detection: HumanDetectionResult) {
    //this.players = await this.identifyPlayers(frame, this.players);
    if (detection.humansCount > 0) {
      const narration = await narrationFlow({
        framePath: frame,
        players: this.players,
        narrationHistory: this.narrationHistory,
      });
      this.narrationHistory.push(narration.narration);
      this.narrator.narrate(narration.narration);
      this.currentTickDelayMs = this.opts.delayTickAfterNarrationMs;
    } else {
      this.currentTickDelayMs = 0;
    }
  }

  async doStartedGameTick(frame: string, detection: HumanDetectionResult) {
    //this.players = await this.identifyPlayers(frame, this.players);

    if (detection.humansCount > 0) {
      console.log("Players identified:");
      console.log(this.players);
      const narration = await narrationFlow({
        framePath: frame,
        players: this.players,
        narrationHistory: this.narrationHistory,
      });
      this.narrationHistory.push(narration.narration);
      this.narrator.narrate(narration.narration);
      this.currentTickDelayMs = this.opts.delayTickAfterNarrationMs;
      this.transitionToState(GameEngineState.PLAYING);
    }
  }
}

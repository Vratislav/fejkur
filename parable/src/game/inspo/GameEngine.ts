import { INarrator } from "../../INarrator";
import { ILLM } from "../../lLLM";
import { grabFrame, createRtspUrl } from "../../cameraUtils";
import { detectHumans } from "../../humanDetection";
import {
  ActiveTask,
  GamePhase,
  GameState,
  GameplayConfig,
  Player,
  TaskDefinition,
  defaultGameplayConfig,
} from "./GameTypes";
import { TaskStore } from "./TaskStore";

export class GameEngine {
  private state: GameState;
  private readonly narrator: INarrator;
  private readonly llm: ILLM;
  private readonly config: GameplayConfig;
  private readonly taskStore: TaskStore;
  private shouldStop: boolean = false;
  private readonly getRtspUrl: () => string;

  constructor(opts: {
    narrator: INarrator;
    llm: ILLM;
    config?: Partial<GameplayConfig>;
    taskStore?: TaskStore;
    getRtspUrl?: () => string;
  }) {
    this.narrator = opts.narrator;
    this.llm = opts.llm;
    this.config = { ...defaultGameplayConfig, ...(opts.config || {}) };
    this.taskStore = opts.taskStore || new TaskStore();
    this.getRtspUrl =
      opts.getRtspUrl ||
      (() => {
        const cameraIp = process.env.CAMERA_IP;
        const cameraUsername = "admin";
        const cameraPassword = process.env.CAMERA_PASSWORD || "";
        const cameraPort = parseInt(process.env.CAMERA_PORT || "554");
        const cameraPath = process.env.CAMERA_PATH || "/stream";
        if (!cameraIp || !cameraPassword) {
          throw new Error("Missing camera configuration");
        }
        return createRtspUrl(
          cameraIp,
          cameraUsername,
          cameraPassword,
          cameraPort,
          cameraPath
        );
      });

    this.state = {
      phase: GamePhase.IDLE,
      players: [],
      hintChance: 0,
      lastNarrations: [],
    };
  }

  async start(): Promise<void> {
    await this.taskStore.loadAllTasks();
    this.shouldStop = false;
    // eslint-disable-next-line no-constant-condition
    while (!this.shouldStop) {
      await this.tick();
      await new Promise((r) => setTimeout(r, this.config.tickMs));
    }
  }

  stop(): void {
    this.shouldStop = true;
  }

  private async tick(): Promise<void> {
    const now = Date.now();
    const rtsp = this.getRtspUrl();
    const framePath = await grabFrame(rtsp);
    this.state.lastFramePath = framePath;

    const detection = await detectHumans(framePath, {
      useServer: this.config.yoloUseServer,
    });

    if (detection.humansDetected) {
      this.state.lastHumanSeenAt = now;
    }

    // Phase transitions
    if (!detection.humansDetected) {
      if (
        this.state.lastHumanSeenAt &&
        now - this.state.lastHumanSeenAt > this.config.idleResetMs
      ) {
        this.transitionTo(GamePhase.IDLE);
        this.state.players = [];
        this.state.activeTask = undefined;
        this.state.hintChance = 0;
      }
      await this.narrateIfNeeded(
        "The room sits empty, patiently awaiting a protagonist."
      );
      return;
    }

    switch (this.state.phase) {
      case GamePhase.IDLE:
        this.transitionTo(GamePhase.STARTING);
        await this.narrator.narrate(
          "Someone has arrived. Oh, how delightful. Please, close the wardrobe doors so we can begin properly."
        );
        this.ensureActivePlayer();
        this.ensureStartingTask();
        break;
      case GamePhase.STARTING:
        this.ensureActivePlayer();
        await this.processGameplay(detection.humansCount);
        break;
      case GamePhase.STARTED:
      case GamePhase.PLAYING:
        this.ensureActivePlayer();
        await this.processGameplay(detection.humansCount);
        break;
      case GamePhase.ESCAPED:
      case GamePhase.ENDED:
        // Do nothing; wait for reset
        break;
    }
  }

  private transitionTo(next: GamePhase): void {
    if (this.state.phase !== next) {
      this.state.phase = next;
    }
  }

  private ensureActivePlayer(): void {
    if (this.state.players.length === 0) {
      const p: Player = { id: "player1", joinedAt: Date.now() };
      this.state.players.push(p);
    }
  }

  private ensureStartingTask(): void {
    if (!this.state.activeTask) {
      const starting: TaskDefinition = {
        id: "close-doors",
        title: "Close the wardrobe doors",
        description: "Ensure the wardrobe doors are closed to begin.",
        isGroupTask: false,
        maxAsks: 3,
        condition: { type: "special", specialKey: "doors_closed" },
        hints: [
          "Try pushing both doors until they click.",
          "Yes, those large wooden things.",
        ],
      };
      this.state.activeTask = {
        task: starting,
        askCount: 0,
        isCompleted: false,
        startedAt: Date.now(),
      };
    }
  }

  private async processGameplay(humansCount: number): Promise<void> {
    // Increase hint chance per tick
    this.state.hintChance = Math.min(1, this.state.hintChance + 0.01);

    if (this.state.phase === GamePhase.STARTING) {
      // If doors "closed" special condition satisfied, transition to STARTED
      if (await this.evaluateActiveTask()) {
        await this.narrator.narrate(
          "Splendid. With the doors closed, we can begin in earnest. Welcome, dear player."
        );
        this.state.activeTask = undefined;
        this.transitionTo(GamePhase.STARTED);
        return;
      }
      await this.askOrNarrateActiveTask();
      return;
    }

    this.transitionTo(GamePhase.PLAYING);

    // Priority: hints/final gesture if random throw hits and threshold reached
    const throwHit = this.randomHit(this.state.hintChance);
    if (throwHit && this.state.hintChance > 0.6) {
      await this.narrator.narrate(
        "There exists a most dignified gesture—show it to me, and a secret door shall oblige."
      );
      return;
    }
    if (throwHit && this.state.hintChance > 0.3) {
      await this.narrator.narrate(
        "A hint, then: symbols have power here. The right sign could be... liberating."
      );
      return;
    }

    // Handle task lifecycle
    if (this.state.activeTask) {
      const completed = await this.evaluateActiveTask();
      if (completed) {
        await this.narrator.narrate(
          "Ah, you actually did it. How wonderfully inconvenient for my dramatic tension."
        );
        this.state.hintChance = Math.min(1, this.state.hintChance + 0.1);
        this.state.activeTask = undefined;
      } else {
        await this.askOrNarrateActiveTask();
      }
    } else {
      await this.maybeAssignNewTask();
    }
  }

  private async maybeAssignNewTask(): Promise<void> {
    const tasks = await this.taskStore.loadAllTasks();
    if (tasks.length === 0) return;
    const candidate = tasks[Math.floor(Math.random() * tasks.length)];
    const newActive: ActiveTask = {
      task: candidate,
      askCount: 0,
      isCompleted: false,
      startedAt: Date.now(),
    };
    this.state.activeTask = newActive;
    await this.askOrNarrateActiveTask();
  }

  private async askOrNarrateActiveTask(): Promise<void> {
    if (!this.state.activeTask) return;
    const a = this.state.activeTask;
    a.askCount += 1;
    a.lastAskAt = Date.now();
    if (a.askCount === 1) {
      a.lastNarrationStyle = "passive";
      await this.narrator.narrate(
        `The person is thinking about: ${a.task.title.toLowerCase()}.`
      );
    } else if (a.askCount === 2) {
      a.lastNarrationStyle = "direct";
      await this.narrator.narrate(
        `You there—would you ${a.task.title.toLowerCase()}?`
      );
    } else {
      a.lastNarrationStyle = "theatrical";
      await this.narrator.narrate(
        `At the risk of sounding dramatic—which I absolutely am—please, ${a.task.title.toLowerCase()}!`
      );
      const hint = a.task.hints[a.askCount - 3];
      if (hint) {
        await this.narrator.narrate(hint);
      }
    }
  }

  private async evaluateActiveTask(): Promise<boolean> {
    if (!this.state.activeTask) return false;
    const active = this.state.activeTask;
    const cond = active.task.condition;

    if (cond.type === "special") {
      // Development fallback: allow env or repeated asks to simulate completion
      if (cond.specialKey === "doors_closed") {
        const simulated = process.env.SIMULATE_DOORS_CLOSED === "1";
        if (simulated || active.askCount >= 3) {
          active.isCompleted = true;
          active.completedAt = Date.now();
          return true;
        }
      }
      return false;
    }

    if (cond.type === "vision_llm") {
      // Send current frame to LLM with a structured schema
      const schema = {
        parse: (x: any) => x as { taskCompleted: boolean },
      } as any;
      const res = await this.llm.callLLM<{ taskCompleted: boolean }>({
        systemPrompt:
          "You are a vision assistant that truthfully answers whether the described action is being performed.",
        history: [],
        prompt: cond.prompt || "",
        responseFormat: schema,
        imagePath: this.state.lastFramePath,
      });
      if (res.content.taskCompleted) {
        active.isCompleted = true;
        active.completedAt = Date.now();
        return true;
      }
      return false;
    }

    return false;
  }

  private async narrateIfNeeded(text: string): Promise<void> {
    if (
      this.state.lastNarrations[this.state.lastNarrations.length - 1] === text
    )
      return;
    this.state.lastNarrations.push(text);
    if (this.state.lastNarrations.length > 5) this.state.lastNarrations.shift();
    await this.narrator.narrate(text);
  }

  private randomHit(p: number): boolean {
    return Math.random() < p;
  }
}

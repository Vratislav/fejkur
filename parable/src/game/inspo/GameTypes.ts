import z from "zod";

export enum GamePhase {
  IDLE = "IDLE",
  STARTING = "STARTING",
  STARTED = "STARTED",
  PLAYING = "PLAYING",
  ESCAPED = "ESCAPED",
  ENDED = "ENDED",
}

export type Player = {
  id: string;
  description?: string;
  joinedAt: number;
};

export type TaskConditionType = "vision_llm" | "special";

export const TaskConditionSchema = z.object({
  type: z.custom<TaskConditionType>(
    (v) => v === "vision_llm" || v === "special"
  ),
  prompt: z.string().optional(),
  specialKey: z.string().optional(),
});

export const TaskDefinitionSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  isGroupTask: z.boolean().default(false),
  maxAsks: z.number().int().min(1).max(10).default(4),
  condition: TaskConditionSchema,
  hints: z.array(z.string()).default([]),
});

export type TaskDefinition = z.infer<typeof TaskDefinitionSchema>;

export type ActiveTask = {
  task: TaskDefinition;
  startedAt: number;
  askCount: number;
  lastAskAt?: number;
  lastNarrationStyle?: "passive" | "direct" | "theatrical";
  isCompleted: boolean;
  completedAt?: number;
};

export type GameState = {
  phase: GamePhase;
  players: Player[];
  lastHumanSeenAt?: number;
  lastFramePath?: string;
  activeTask?: ActiveTask;
  hintChance: number; // 0..1
  lastNarrations: string[];
};

export type GameplayConfig = {
  tickMs: number;
  idleResetMs: number; // 2 minutes default
  yoloUseServer: boolean;
};

export const defaultGameplayConfig: GameplayConfig = {
  tickMs: 15000,
  idleResetMs: 2 * 60 * 1000,
  yoloUseServer: true,
};

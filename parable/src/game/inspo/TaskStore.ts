import * as path from "path";
import * as fs from "fs-extra";
import { TaskDefinition, TaskDefinitionSchema } from "./GameTypes";

export class TaskStore {
  private readonly tasksDir: string;
  private cache: Map<string, TaskDefinition> = new Map();

  constructor(tasksDir?: string) {
    this.tasksDir = tasksDir || path.resolve(process.cwd(), "gameTasks");
  }

  async loadAllTasks(): Promise<TaskDefinition[]> {
    const exists = await fs.pathExists(this.tasksDir);
    if (!exists) {
      await fs.ensureDir(this.tasksDir);
      return [];
    }

    const entries = await fs.readdir(this.tasksDir);
    const jsonFiles = entries.filter((f) => f.toLowerCase().endsWith(".json"));
    const results: TaskDefinition[] = [];

    for (const file of jsonFiles) {
      const abs = path.join(this.tasksDir, file);
      try {
        const raw = await fs.readFile(abs, "utf8");
        const parsed = JSON.parse(raw);
        const validated = TaskDefinitionSchema.parse(parsed);
        results.push(validated);
        this.cache.set(validated.id, validated);
      } catch (err) {
        // Skip invalid files but log for visibility
        // eslint-disable-next-line no-console
        console.warn(`Invalid task file ${file}:`, err);
      }
    }
    return results;
  }

  getById(taskId: string): TaskDefinition | undefined {
    return this.cache.get(taskId);
  }
}

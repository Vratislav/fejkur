import path from "path";
import { spawn } from "child_process";
import { promises as fs } from "fs";
import axios from "axios";

export type HumanDetectionResult = {
  humansDetected: boolean;
  humansCount: number;
};

export type HumanDetectionOptions = {
  useServer?: boolean;
  serverUrl?: string;
  confidence?: number;
};

/**
 * Counts humans in a YOLO label file content. Each line starting with "0" represents a person.
 */
export function parseHumanCountFromYoloTxt(labelFileContent: string): number {
  if (!labelFileContent) return 0;
  const lines = labelFileContent
    .split(/\r?\n/g)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  // Lines starting with class id 0 (followed by whitespace) are humans
  const humanLines = lines.filter((l) => /^0\b/.test(l));
  return humanLines.length;
}

async function runYoloDetectWithPoetry(absSourcePath: string): Promise<void> {
  const cwd = path.resolve(process.cwd(), "fejkur-yolo");
  await ensureDirectoryExists(cwd);

  const args = [
    "run",
    "yolo",
    "detect",
    "predict",
    "model=./models/yolo11n.pt",
    "save_json=True",
    "save_txt=True",
    "save_conf=True",
    "conf=0.5",
    `source=${absSourcePath}`,
  ];

  await new Promise<void>((resolve, reject) => {
    const child = spawn("poetry", args, {
      cwd,
      stdio: "ignore",
      shell: false,
    });
    child.on("error", (err) => reject(err));
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`YOLO command failed with exit code ${code}`));
    });
  });
}

async function ensureDirectoryExists(dirPath: string): Promise<void> {
  try {
    const stat = await fs.stat(dirPath);
    if (!stat.isDirectory()) {
      throw new Error(`${dirPath} exists but is not a directory`);
    }
  } catch (err: any) {
    if (err?.code === "ENOENT") {
      throw new Error(`Working directory not found: ${dirPath}`);
    }
    throw err;
  }
}

async function getLatestPredictDirAbsolute(): Promise<string | null> {
  const detectRoot = path.resolve(
    process.cwd(),
    "fejkur-yolo",
    "runs",
    "detect"
  );
  try {
    const entries = await fs.readdir(detectRoot, { withFileTypes: true });
    const predictDirs = entries
      .filter((e) => e.isDirectory() && e.name.startsWith("predict"))
      .map((e) => e.name)
      .map((name) => ({
        name,
        num: Number.parseInt(name.replace(/^predict/, ""), 10),
      }))
      .filter((x) => Number.isFinite(x.num))
      .sort((a, b) => a.num - b.num);

    if (predictDirs.length === 0) return null;
    const latest = predictDirs[predictDirs.length - 1].name;
    return path.join(detectRoot, latest);
  } catch (err: any) {
    if (err?.code === "ENOENT") return null;
    throw err;
  }
}

async function readLabelFileContentForSource(
  absSourcePath: string
): Promise<string | null> {
  const latestPredictDir = await getLatestPredictDirAbsolute();
  if (!latestPredictDir) return null;

  const baseFile = path.basename(absSourcePath);
  const baseTxt = baseFile.replace(/\.[^.]+$/, ".txt");
  const labelPath = path.join(latestPredictDir, "labels", baseTxt);

  try {
    return await fs.readFile(labelPath, "utf8");
  } catch (err: any) {
    if (err?.code === "ENOENT") return null;
    throw err;
  }
}

async function detectViaServer(
  absSourcePath: string,
  options?: HumanDetectionOptions
): Promise<HumanDetectionResult> {
  const serverUrl =
    options?.serverUrl ||
    process.env.FEJKUR_YOLO_SERVER_URL ||
    "http://127.0.0.1:8001/detect";
  const confidence = options?.confidence ?? 0.5;
  type Response = {
    humansDetected: boolean;
    humansCount: number;
  };
  const { data } = await axios.post<Response>(serverUrl, {
    source_path: absSourcePath,
    conf: confidence,
    save_txt: true,
    save_conf: true,
  });
  return { humansDetected: data.humansDetected, humansCount: data.humansCount };
}

export async function detectHumans(
  sourcePath: string,
  options?: HumanDetectionOptions
): Promise<HumanDetectionResult> {
  // Resolve the source path to an absolute path before passing to YOLO
  const absSourcePath = path.isAbsolute(sourcePath)
    ? sourcePath
    : path.resolve(process.cwd(), sourcePath);

  const shouldUseServer =
    options?.useServer === true ||
    /^(1|true|yes)$/i.test(process.env.FEJKUR_YOLO_USE_SERVER || "");

  if (shouldUseServer) {
    return await detectViaServer(absSourcePath, options);
  }

  await runYoloDetectWithPoetry(absSourcePath);

  const labelContent = await readLabelFileContentForSource(absSourcePath);
  const humansCount = labelContent
    ? parseHumanCountFromYoloTxt(labelContent)
    : 0;
  return {
    humansDetected: humansCount > 0,
    humansCount,
  };
}

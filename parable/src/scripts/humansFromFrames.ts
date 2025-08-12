import path from "path";
import { promises as fs } from "fs";
import { detectHumans } from "../humanDetection";

async function listFrameFiles(framesDir: string): Promise<string[]> {
  try {
    const dirents = await fs.readdir(framesDir, { withFileTypes: true });
    const imageFiles = dirents
      .filter((d) => d.isFile())
      .map((d) => d.name)
      .filter((name) => /\.(jpe?g|png|bmp|gif|webp)$/i.test(name))
      .sort((a, b) => a.localeCompare(b));
    return imageFiles.map((name) => path.join(framesDir, name));
  } catch (err: any) {
    if (err?.code === "ENOENT") {
      throw new Error(`Frames directory not found: ${framesDir}`);
    }
    throw err;
  }
}

async function main(): Promise<void> {
  const framesDir = path.resolve(process.cwd(), "frames");
  const framePaths = await listFrameFiles(framesDir);

  if (framePaths.length === 0) {
    console.log("No frames found.");
    return;
  }

  const overallStartMs = Date.now();
  let sumFrameProcessingMs = 0;
  let processed = 0;
  for (const framePath of framePaths) {
    const frameStartMs = Date.now();
    try {
      const result = await detectHumans(framePath, { useServer: true });
      console.log(`${framePath} humans=${result.humansCount}`);
    } catch (err: any) {
      console.error(`${framePath} error=${err?.message || String(err)}`);
    } finally {
      const elapsedMs = Date.now() - frameStartMs;
      sumFrameProcessingMs += elapsedMs;
    }
    processed += 1;
  }

  const totalDurationMs = Date.now() - overallStartMs;
  const avgFrameMs = processed > 0 ? sumFrameProcessingMs / processed : 0;

  console.log(`totalFrames=${processed}`);
  console.log(`totalDurationMs=${totalDurationMs}`);
  console.log(`avgFrameMs=${avgFrameMs.toFixed(2)}`);
}

main().catch((err) => {
  console.error("humansFromFrames failed:", err);
  process.exit(1);
});

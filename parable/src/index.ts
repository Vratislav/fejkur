import { createRtspUrl } from "./cameraUtils";
import dotenv from "dotenv";
import { GameEngine } from "./game/GameEngine";
import { ConsoleNarrator } from "./game/inspo/NarratorConsole";
import { StubLLM } from "./game/inspo/LLMStub";
import { TestCameraFrameProvider } from "./game/CameraFrameProvider";
import { RealHumanDetector } from "./game/HumanDetector";

// Load environment variables
dotenv.config();

function getRtspUrlFromEnv() {
  // Load camera configuration from environment variables
  const cameraIp = process.env.CAMERA_IP;
  const cameraUsername = "admin";
  const cameraPassword = process.env.CAMERA_PASSWORD;
  const cameraPort = parseInt(process.env.CAMERA_PORT || "554");
  const cameraPath = process.env.CAMERA_PATH || "/stream";

  if (!cameraIp || !cameraUsername || !cameraPassword) {
    throw new Error("Missing required camera configuration in .env file");
  }

  const rtspUrl = createRtspUrl(
    cameraIp,
    cameraUsername,
    cameraPassword,
    cameraPort,
    cameraPath
  );
  console.log(`Using RTSP URL: ${rtspUrl.replace(cameraPassword, "***")}`);
  return rtspUrl;
}

async function main() {
  try {
    console.log("Starting game engine...");
    const llm = new StubLLM();
    const engine = new GameEngine({
      frameProvider: new TestCameraFrameProvider(),
      humanDetector: new RealHumanDetector(),
      llm: new StubLLM(),
      narrator: new ConsoleNarrator(true),
      tickMs: 15_000,
      maxFrameStalenessMs: 5_000,
      maxTimeIntervalWithoutHumanMs: 60_000,
      stepThroughTicks: Boolean(process.env.GAME_ENGINE_STEP_THROUGH),
    });
    await engine.startEngine();
  } catch (error) {
    console.error("Failed to capture frame:", error);
    process.exit(1);
  }
}

// Run the main function
main();

import { grabFrame, createRtspUrl } from "./cameraUtils";
import dotenv from "dotenv";

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
    console.log("Starting camera frame capture...");

    const framePath = await grabFrame(getRtspUrlFromEnv());
    console.log(`Frame captured successfully and saved to: ${framePath}`);
  } catch (error) {
    console.error("Failed to capture frame:", error);
    process.exit(1);
  }
}

// Run the main function
main();

import dotenv from "dotenv";
// Load environment variables
dotenv.config();
import { playerIdentificationFlow } from "../ai";

const path =
  "/Users/kal/repos/fejkur/parable/frames/frame_2025-08-12_09-45-25-974.jpg";

playerIdentificationFlow({ framePath: path });

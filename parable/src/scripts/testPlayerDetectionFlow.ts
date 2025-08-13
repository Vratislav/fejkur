import dotenv from "dotenv";
// Load environment variables
dotenv.config();
import { playerIdentificationFlow } from "../ai/flows/playerIdentificationFlow";

const path =
  "/Users/kal/repos/fejkur/parable/frames/frame_2025-08-12_09-45-25-974.jpg";

playerIdentificationFlow({ framePath: path, players: [] }).then((result) => {
  //assign id to the players
  const playersWithIds = result.map((player, index) => ({
    ...player,
    id: index + 1,
  }));
  console.log(playersWithIds);
  playerIdentificationFlow({ framePath: path, players: playersWithIds });
});

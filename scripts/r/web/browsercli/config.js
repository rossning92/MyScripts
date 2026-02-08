import os from "os";
import path from "path";

export const USER_DATA_DIR = path.join(
  os.homedir(),
  ".browsercli-user-data",
);
export const DEFAULT_DELAY_MS = 3000;
export const DEBUG_PORT = 21222;
export const BROWSER_URL = `http://127.0.0.1:${DEBUG_PORT}`;

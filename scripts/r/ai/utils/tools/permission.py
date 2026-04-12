from pathlib import Path
from typing import List
from utils.jsonutil import load_json

ALLOWED_COMMANDS_FILE = Path(__file__).parent / "allowed_commands.json"
ALLOWED_COMMANDS: List[str] = load_json(str(ALLOWED_COMMANDS_FILE), default=[])

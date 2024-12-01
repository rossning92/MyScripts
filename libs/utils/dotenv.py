import os
from typing import List


def load_dotenv(dotenv_path=".env", env=None):
    if env is None:
        env = os.environ

    with open(dotenv_path, "r") as dotenv_file:
        for line in dotenv_file:
            # Ignore empty lines or comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Split the line into key and value
            key, value = line.split("=", 1)
            key = key.strip()
            # Remove surrounding quotes if any
            value = value.strip().strip('"').strip("'")

            env[key] = value


def set_dotenv(key, val, dotenv_path=".env"):
    updated = False
    lines: List[str] = []
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            for i, line in enumerate(lines):
                if not line or line.startswith("#"):
                    continue

                k, _ = line.split("=", 1)
                if k == key:
                    updated = True
                    lines[i] = f"{key}={val}"
                    break

    if not updated:
        lines.append(f"{key}={val}")

    with open(dotenv_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

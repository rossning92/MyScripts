import os


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

import os
from datetime import datetime
from platform import platform


def get_env_info() -> str:
    return f"""# Environment Information

Platform: {platform()}
Current working directory: {os.getcwd()}
Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

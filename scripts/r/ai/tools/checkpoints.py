import os
import zipfile
from datetime import datetime
from typing import List

CHECKPOINTS_DIR = os.path.join(".coder", "checkpoints")


def backup_files(files: List[str]):
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    checkpoint_file = os.path.join(
        CHECKPOINTS_DIR, f"checkpoint_{datetime.now().timestamp()}.zip"
    )

    with zipfile.ZipFile(checkpoint_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            rel_path = os.path.relpath(file_path, start=os.getcwd())
            zipf.write(file_path, arcname=rel_path)


def restore_files_to_timestamp(timestamp: float) -> None:
    restore_point = datetime.fromtimestamp(timestamp)

    # Find all checkpoints created after the given timestamp
    checkpoints = []
    for entry in os.listdir(CHECKPOINTS_DIR):
        if entry.startswith("checkpoint_") and entry.endswith(".zip"):
            checkpoint_time_str = float(entry[len("checkpoint_") : -len(".zip")])
            checkpoint_time = datetime.fromtimestamp(checkpoint_time_str)
            if checkpoint_time > restore_point:
                checkpoints.append((checkpoint_time, entry))
    if not checkpoints:
        return

    # Restore all checkpoints
    for checkpoint_time, checkpoint_file in checkpoints:
        checkpoint_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
        with zipfile.ZipFile(checkpoint_path, "r") as zipf:
            zipf.extractall()

    # Remove the restored checkpoints
    for _, checkpoint_file in checkpoints:
        checkpoint_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
        os.remove(checkpoint_path)

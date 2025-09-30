import logging
import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Tuple

CHECKPOINTS_DIR = os.path.join(".config", "coder", "checkpoints")
HISTORY_DIR = os.path.join(".config", "coder", "history")


def backup_files(files: List[str]):
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    timestamp = str(datetime.now().timestamp())

    history_timestamp_dir = os.path.join(HISTORY_DIR, timestamp)
    os.makedirs(history_timestamp_dir, exist_ok=True)

    checkpoint_file = f"checkpoint_{timestamp}.zip"
    checkpoint_full_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
    with zipfile.ZipFile(checkpoint_full_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            # Write to the zip file
            logging.info(f'Adding file "{file_path}" to checkpoint "{checkpoint_file}"')
            rel_path = os.path.relpath(file_path, start=os.getcwd())
            zipf.write(file_path, arcname=rel_path)

            # Make a copy in the history directory
            history_file_path = os.path.join(history_timestamp_dir, rel_path)
            os.makedirs(os.path.dirname(history_file_path), exist_ok=True)
            shutil.copy2(file_path, history_file_path)


def restore_files_since_timestamp(timestamp: float) -> None:
    restore_point = datetime.fromtimestamp(timestamp)
    logging.info(f"Restoring files since {restore_point.isoformat()}")

    # Find all checkpoints created after the given timestamp
    checkpoints = []
    if os.path.exists(CHECKPOINTS_DIR):
        for entry in os.listdir(CHECKPOINTS_DIR):
            if entry.startswith("checkpoint_") and entry.endswith(".zip"):
                checkpoint_time_str = float(entry[len("checkpoint_") : -len(".zip")])
                checkpoint_time = datetime.fromtimestamp(checkpoint_time_str)
                if checkpoint_time >= restore_point:
                    checkpoints.append((checkpoint_time, entry))
    if not checkpoints:
        return

    # Restore all checkpoints backward in time
    checkpoints.sort(key=lambda x: x[0], reverse=True)
    for checkpoint_time, checkpoint_file in checkpoints:
        checkpoint_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
        with zipfile.ZipFile(checkpoint_path, "r") as zipf:
            for file_info in zipf.infolist():
                logging.info(
                    f'Restoring file "{file_info.filename}" from checkpoint "{checkpoint_file}"'
                )
                zipf.extract(file_info)

    # Remove the restored checkpoints
    for _, checkpoint_file in checkpoints:
        checkpoint_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
        os.remove(checkpoint_path)


def get_oldest_files_since_timestamp(timestamp: float) -> List[Tuple[str, str]]:
    seen = set()
    old_files: List[Tuple[str, str]] = []
    if os.path.exists(HISTORY_DIR):
        for entry in sorted(os.listdir(HISTORY_DIR)):
            entry_time = float(entry)
            if entry_time >= timestamp:
                sub_history_dir = os.path.join(HISTORY_DIR, entry)
                for root, _, files in os.walk(sub_history_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, start=sub_history_dir)
                        if rel_path not in seen:
                            seen.add(rel_path)
                            old_files.append((sub_history_dir, rel_path))
    return old_files

import logging
import os
import zipfile
from datetime import datetime
from typing import List

CHECKPOINTS_DIR = os.path.join(".coder", "checkpoints")


def backup_files(files: List[str]):
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    checkpoint_file = f"checkpoint_{datetime.now().timestamp()}.zip"
    checkpiont_full_path = os.path.join(CHECKPOINTS_DIR, checkpoint_file)
    with zipfile.ZipFile(checkpiont_full_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            logging.info(f'Adding file "{file_path}" to checkpoint "{checkpoint_file}"')
            rel_path = os.path.relpath(file_path, start=os.getcwd())
            zipf.write(file_path, arcname=rel_path)


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

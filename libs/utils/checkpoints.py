import logging
import os
import shutil
from datetime import datetime
from typing import List, Tuple

HISTORY_DIR = os.path.join(".config", "coder", "history")
MAX_HISTORY = 50


def _get_history_entries() -> List[Tuple[float, str]]:
    if not os.path.exists(HISTORY_DIR):
        return []

    entries = []
    for entry in os.listdir(HISTORY_DIR):
        try:
            timestamp = float(entry)
            entries.append((timestamp, entry))
        except ValueError:
            continue
    return entries


def _cleanup_old_history():
    history_entries = sorted(_get_history_entries())
    if len(history_entries) <= MAX_HISTORY:
        return

    # Remove oldest entries
    num_to_remove = len(history_entries) - MAX_HISTORY
    for _, entry in history_entries[:num_to_remove]:
        entry_path = os.path.join(HISTORY_DIR, entry)
        logging.info(f"Removing old history entry: {entry}")
        shutil.rmtree(entry_path)


def backup_files(files: List[str]):
    os.makedirs(HISTORY_DIR, exist_ok=True)

    timestamp = str(datetime.now().timestamp())

    history_timestamp_dir = os.path.join(HISTORY_DIR, timestamp)
    os.makedirs(history_timestamp_dir, exist_ok=True)

    for file_path in files:
        rel_path = os.path.relpath(file_path, start=os.getcwd())
        logging.info(f'Backing up file "{rel_path}" to history')

        # Make a copy in the history directory
        history_file_path = os.path.join(history_timestamp_dir, rel_path)
        os.makedirs(os.path.dirname(history_file_path), exist_ok=True)
        shutil.copy2(file_path, history_file_path)

    _cleanup_old_history()


def restore_files_since_timestamp(timestamp: float) -> None:
    restore_point = datetime.fromtimestamp(timestamp)
    logging.info(f"Restoring files since {restore_point.isoformat()}")

    # Find all history entries created after the given timestamp
    history_entries = [e for e in _get_history_entries() if e[0] >= timestamp]
    if not history_entries:
        return

    # Restore all history backward in time
    history_entries.sort(key=lambda x: x[0], reverse=True)
    for _, entry in history_entries:
        sub_history_dir = os.path.join(HISTORY_DIR, entry)
        for root, _, files in os.walk(sub_history_dir):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, start=sub_history_dir)
                logging.info(f'Restoring file "{rel_path}" from history entry "{entry}"')
                shutil.copy2(src_path, os.path.join(os.getcwd(), rel_path))

        # Remove the restored history entry
        shutil.rmtree(sub_history_dir)


def get_oldest_files_since_timestamp(timestamp: float) -> List[Tuple[str, str]]:
    seen = set()
    old_files: List[Tuple[str, str]] = []
    history_entries = sorted([e for e in _get_history_entries() if e[0] >= timestamp])
    for _, entry in history_entries:
        sub_history_dir = os.path.join(HISTORY_DIR, entry)
        for root, _, files in os.walk(sub_history_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, start=sub_history_dir)
                if rel_path not in seen:
                    seen.add(rel_path)
                    old_files.append((sub_history_dir, rel_path))
    return old_files

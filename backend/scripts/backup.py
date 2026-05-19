import os
import shutil
import sqlite3
import gzip
from datetime import datetime
from pathlib import Path


BACKUP_DIR = os.environ.get("BACKUP_DIR", "/backups")
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "7"))


def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(backup_subdir, exist_ok=True)

    for root, dirs, files in os.walk(DATA_DIR):
        for filename in files:
            if filename.endswith(".db"):
                db_path = os.path.join(root, filename)
                backup_path = os.path.join(backup_subdir, f"{filename}.gz")

                try:
                    temp_path = os.path.join(backup_subdir, filename)
                    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                    backup_conn = sqlite3.connect(temp_path)
                    conn.backup(backup_conn)
                    backup_conn.close()
                    conn.close()

                    with open(temp_path, "rb") as f_in:
                        with gzip.open(backup_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    os.remove(temp_path)
                    print(f"Backed up: {filename} -> {backup_path}")
                except Exception as e:
                    print(f"Failed to backup {filename}: {e}")

    cleanup_old_backups()
    print(f"Backup completed: {timestamp}")


def cleanup_old_backups():
    cutoff = datetime.now().timestamp() - (RETENTION_DAYS * 86400)
    backup_path = Path(BACKUP_DIR)

    if not backup_path.exists():
        return

    for entry in backup_path.iterdir():
        if entry.is_dir():
            try:
                dir_time = datetime.strptime(entry.name, "%Y%m%d_%H%M%S").timestamp()
                if dir_time < cutoff:
                    shutil.rmtree(entry)
                    print(f"Removed old backup: {entry.name}")
            except ValueError:
                pass


if __name__ == "__main__":
    create_backup()

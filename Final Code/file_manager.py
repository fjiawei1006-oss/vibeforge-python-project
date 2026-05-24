# file_manager.py
import json
import os
from datetime import datetime

from models import Melody, Chord


class FileManager:
    """
    Save and load compositions as JSON.
    """

    def __init__(self, save_dir="saved"):
        self.base_dir = os.path.dirname(__file__)
        self.save_dir = os.path.join(self.base_dir, save_dir)
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

    def _safe_title(self, title: str) -> str:
        cleaned = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in title.strip())
        return cleaned[:40] if cleaned else "untitled"

    def save(self, title: str, melody: Melody, chords: list, metadata: dict) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self._safe_title(title)}_{ts}.json"
        path = os.path.join(self.save_dir, filename)

        payload = {
            "title": title,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "melody": melody.to_dict(),
            "chords": [c.to_dict() if isinstance(c, Chord) else c for c in chords],
            "metadata": metadata or {},
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return filename
        except (IOError, PermissionError) as e:
            print(f"[Save Error] {e}")
            return ""

    def load(self, filename: str) -> dict:
        path = os.path.join(self.save_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("[Load Error] File not found.")
            return {}
        except json.JSONDecodeError:
            print("[Load Error] Corrupted JSON file.")
            return {}
        except IOError as e:
            print(f"[Load Error] {e}")
            return {}

    def list_saved(self):
        entries = []
        try:
            for name in os.listdir(self.save_dir):
                if name.endswith(".json"):
                    path = os.path.join(self.save_dir, name)
                    title = name
                    date = ""
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        title = data.get("title", name)
                        date = data.get("saved_at", "")
                    except Exception:
                        pass
                    entries.append({"filename": name, "title": title, "date": date})
            entries.sort(key=lambda x: x["filename"], reverse=True)
            return entries
        except OSError as e:
            print(f"[List Error] {e}")
            return []

    def delete(self, filename: str) -> bool:
        path = os.path.join(self.save_dir, filename)
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            print("[Delete Error] File not found.")
            return False
        except OSError as e:
            print(f"[Delete Error] {e}")
            return False

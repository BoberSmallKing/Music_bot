import json
from pathlib import Path

SONGS_FILE = Path("songs.json")


def load_song_list() -> list[str]:
    if SONGS_FILE.exists():
        try:
            with SONGS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(x) for x in data]
        except Exception:
            return []
    return []


def save_song_list(songs: list[str]) -> None:
    try:
        with SONGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
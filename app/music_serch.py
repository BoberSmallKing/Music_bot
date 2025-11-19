import yt_dlp
import re
from pathlib import Path

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)


def sanitize_filename_keep_spaces(name: str) -> str:
    """
    Оставляет пробелы, убирает только реально опасные и мусорные символы
    Результат: Mansour - Cheshman Siah.mp3  →  Mansour - Cheshman Siah.mp3 (или очень близко)
    """
    # 1. Убираем строго запрещённые в файловых системах символы
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    
    # 2. Убираем лишние декоративные символы, которые часто ломают парсинг
    name = re.sub(r'[\[\]\'’"„”«»♪♥❤✨•·–—~]', '', name)
    
    # 3. Сх Убираем множественные пробелы и пробелы по краям
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    # 4. Заменяем только вертикальную черту и амперсанд на безопасные варианты
    name = name.replace('|', '-').replace('&', 'and')
    
    # 5. Если остались скобки в конце — можно оставить, они обычно не мешают
    #     (если хочешь убрать — раскомментируй строку ниже)
    # name = re.sub(r'\s*[\(\[\{].*?[\)\]\}]', '', name)
    
    # 6. Защита от слишком длинного имени
    if len(name) > 180:
        name = name[:180].rstrip()
    
    # 7. Если вдруг стало пустым
    if not name:
        name = "Unknown Track"
        
    return name + ".mp3" if not name.lower().endswith(('.mp3', '.m4a', '.webm')) else name


def download_audio_from_youtube(query: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'outtmpl': str(DOWNLOADS_DIR / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        video_info = info['entries'][0] if info.get('_type') == 'playlist' and info.get('entries') else info
        
        original_title = video_info.get('title', 'Unknown')
        clean_title = sanitize_filename_keep_spaces(original_title)
        final_path = DOWNLOADS_DIR / clean_title

        # Ищем только что скачанный файл и переименовываем
        candidates = sorted(
            DOWNLOADS_DIR.glob("*.mp3"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if candidates:
            latest_file = candidates[0]
            if latest_file.name != clean_title:
                try:
                    latest_file.rename(final_path)
                except FileExistsError:
                    # Если файл с таким именем уже есть — добавляем номер
                    stem = final_path.stem
                    final_path = DOWNLOADS_DIR / f"{stem}_{len(candidates)}.mp3"
                    latest_file.rename(final_path)

        print(f"Скачано → {final_path.name}")
        return final_path.name
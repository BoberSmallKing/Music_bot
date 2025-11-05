import yt_dlp
from pathlib import Path

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

def download_audio_from_youtube(query: str) -> tuple[str, str]:
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
        'ffmpeg_location': r"D:\Desktop\ffmpeg\bin\ffmpeg.exe",
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)

        if info.get('_type') == 'playlist' and info.get('entries'):
            video_info = info['entries'][0]
        else:
            video_info = info
        
        title = video_info.get('title', 'Unknown Title')
        filename = f"{title}.mp3"
        return filename
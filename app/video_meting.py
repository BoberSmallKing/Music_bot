from telethon import TelegramClient
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import MediaStream
from pytgcalls.types import Update
from pytgcalls import filters as call_filters
from pathlib import Path
from dotenv import load_dotenv
import os


load_dotenv()

list_musics = ["Marius Bear - Boys Do Cry - Switzerland 🇨🇭 - Official Music Video - Eurovision 2022.mp3", "Tom Odell - Another Love (Official Video).mp3"]
app = None
current_track_index = 0

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
session_name = 'bot_session'
CHAT_ID = os.getenv("CHAT_ID")

async def start_call_manager():
    global app
    client = TelegramClient(session_name, API_ID, API_HASH)
    app = PyTgCalls(client)
    
    @app.on_update(call_filters.stream_end())
    async def handler(client: PyTgCalls, update: Update):
        global current_track_index
        print(f"Трек завершён: {update}")

        current_track_index = (current_track_index + 1) % len(list_musics)
        audio_path = Path("downloads") / list_musics[current_track_index]
        print(f"▶️ Воспроизведение следующего трека: {audio_path}")

        try:
            await app.play(
                CHAT_ID,
                MediaStream(str(audio_path), audio_flags=MediaStream.Flags.AUTO_DETECT)
            )
        except Exception as e:
            print(f"Ошибка при воспроизведении трека {audio_path}: {e}")

    await client.start()
    await app.start()
    print("📞 PyTgCalls запущен!")

async def play_audio_in_call():
    global current_track_index
    if not list_musics:
        print("Список треков пуст!")
        return
    audio_path = Path("downloads") / list_musics[current_track_index]
    print(f"Воспроизведение первого трека: {audio_path}")
    try:
        await app.play(
            CHAT_ID,
            MediaStream(str(audio_path), audio_flags=MediaStream.Flags.AUTO_DETECT)
        )
    except Exception as e:
        print(f"Ошибка при воспроизведении трека {audio_path}: {e}")
    await idle()

async def pause_audio():
    await app.pause(CHAT_ID)

async def resume_audio():
    await app.resume(CHAT_ID)

async def leave_audio():
    await app.leave_call(CHAT_ID)
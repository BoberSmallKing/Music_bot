from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram import F, Router
from .music_serch import download_audio_from_youtube
from .video_meting import play_audio_in_call, list_musics, pause_audio, resume_audio, leave_audio, next_track
from .song_store import save_song_list
from .admin import admin_required
from .keyboards import get_menu_keyboard
from dotenv import load_dotenv
import html
from pathlib import Path
import re
import os

load_dotenv()


router = Router()


current_dir = Path(__file__).parent  

photo_path = current_dir.parent / "menu_photo.jpg"

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)
channel_id = os.getenv("CHAT_ID")

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip()

def ext_from_mime(mime: str) -> str:
    mapping = {
        "audio/mpeg": ".mp3",
    }
    return mapping.get(mime, ".mp3")


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_name = html.escape(message.from_user.full_name)
    await message.answer(
        f"Привет {user_name}! 🎶\nЭто музыкальный бот, который умеет искать и включать музыку!",
    )

@router.message(F.text == "menu" or Command("menu"))
async def menu_handler(message: Message):
    photo = FSInputFile(photo_path)
    if channel_id:
        sent_message = await message.bot.send_photo(
            chat_id=channel_id,
            photo=photo,
            caption="🎧 Главное меню:",
            reply_markup=get_menu_keyboard()
        )
    else:
        await message.answer_photo(
            photo=photo,
            caption="🎧 Главное меню:",
            reply_markup=get_menu_keyboard()
        )

@router.message(Command("add"))
async def add_music(message: Message):
    if len(list_musics) >= 5:
        await message.answer("❌ Очередь уже заполнена! Пожалуйста, удалите лишние треки.")
        return

    if message.audio:
        audio = message.audio
        base_name = audio.file_name or audio.title or f"audio_{audio.file_unique_id}"
        ext = Path(base_name).suffix or ext_from_mime(audio.mime_type or "")
        safe_name = sanitize_filename(Path(base_name).stem) + ext
        dest_path = DOWNLOADS_DIR / safe_name
        await message.bot.send_message(chat_id=channel_id, text="⬇️ Сохраняю ваш аудиофайл...")
        try:
            await message.bot.download(audio, destination=dest_path)
            list_musics.append(dest_path.name)
            save_song_list(list_musics)
            await message.bot.send_message(chat_id=channel_id ,text=f"✅ Файл '{dest_path.name}' добавлен в очередь!")
        except Exception as e:
            await message.answer(f"❌ Ошибка при сохранении файла: {str(e)}")
    elif message.text and len(message.text.split()) > 1:
        query = " ".join(message.text.split()[1:])
        await message.bot.send_message(chat_id=channel_id, text="🔍 Ищу и скачиваю музыку...")
        try:
            filename = download_audio_from_youtube(query)
            list_musics.append(filename)
            save_song_list(list_musics)
            await message.bot.send_message(chat_id=channel_id, text=f"✅ Песня '{filename}' найдена и добавлена в очередь!")
        except Exception as e:
            await message.answer(f"❌ Ошибка при скачивании: {str(e)}")
    else:
        await message.answer("❌ Пожалуйста, укажите название песни после /add или прикрепите аудиофайл.")




@router.callback_query(lambda c: c.data == "show_queue")
@admin_required()
async def show_queue_callback(callback: CallbackQuery):
    if not list_musics:
        await callback.message.answer("Очередь пуста! 💤")
        await callback.answer()
        return

    queue_text = "🎵 Текущая очередь песен:\n"
    for i, music in enumerate(list_musics, 1):
        queue_text += f"{i}. {music.replace('.mp3', '')}\n"

    await callback.message.answer(queue_text)
    await callback.answer()


@router.callback_query(lambda c: c.data == "play_all")
@admin_required()
async def play_all_callback(callback: CallbackQuery):
    if not list_musics:
        await callback.answer("Очередь пуста! 💤")
        await callback.answer()
        return

    await callback.answer("▶️ Воспроизвожу все песни по очереди...")
    await play_audio_in_call()
    await callback.answer()


@router.callback_query(F.data == "clear_queue")
@admin_required()
async def play_all_callback(callback: CallbackQuery):
    for fname in list_musics:
        try:
            os.remove(DOWNLOADS_DIR / fname)
        except Exception:
            pass
    list_musics.clear()
    save_song_list(list_musics)
    await callback.answer("Очищена очередь!")



@router.callback_query(F.data =="pause_audio")
@admin_required()
async def pause_track(callback: CallbackQuery):
    await pause_audio()
    await callback.answer("⏸ Воспроизведение приостановлено")

@router.callback_query(F.data =="resume_audio")
@admin_required()
async def resume_track(callback: CallbackQuery):
    await resume_audio()
    await callback.answer("▶️ Воспроизведение возобновлено")


@router.callback_query(F.data =="exit")
@admin_required()
async def exit(callback: CallbackQuery):
    await leave_audio()
    await callback.answer("🚪Выйти из звонка")

@router.message(Command("delete"))
async def delete_track(message: Message):
    if not list_musics:
        await message.answer("Очередь пуста! 💤")
        return

    # Показать очередь, если команда без номера
    if len(message.text.split()) == 1:
        queue_text = "🎵 Текущая очередь песен:\n"
        for i, music in enumerate(list_musics, 1):
            queue_text += f"{i}. {music.replace('.mp3', '')}\n"
        await message.bot.send_message(chat_id=channel_id, text=f"{queue_text}\nВведите команду /delete <номер трека>, чтобы удалить трек.")    
        return
    try:
        index = int(message.text.split()[1]) - 1
        if 0 <= index < len(list_musics):
            deleted_track = list_musics.pop(index)
            try:
                os.remove(DOWNLOADS_DIR / deleted_track)
            except Exception:
                pass
            save_song_list(list_musics)
            await message.bot.send_message(
                chat_id=channel_id,
                text=f"🗑 Трек '{deleted_track.replace('.mp3', '')}' удален из очереди!"
            )
        else:
            await message.bot.send_message(chat_id=channel_id, text="❌ Неверный номер трека! Пожалуйста, выберите номер из списка.")
    except (ValueError, IndexError):
        await message.bot.send_message(chat_id=channel_id, text="❌ Пожалуйста, введите число, соответствующее номеру трека (например, /delete 1).")

@router.callback_query(F.data == "next_track")
@admin_required()
async def next_track_callback(callback: CallbackQuery):
    if not list_musics:
        await callback.answer("❌ Очередь пуста! Добавьте треки с помощью /add.")
        return

    try:
        track_name = await next_track()
        await callback.answer(f"▶️ Воспроизведение следующего трека: {track_name.replace('.mp3', '')}")
    except Exception as e:
        await callback.answer(f"❌ Ошибка при переключении трека: {str(e)}")
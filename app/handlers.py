from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F, Router
from .music_serch import download_audio_from_youtube
from .video_meting import play_audio_in_call, list_musics, pause_audio, resume_audio, leave_audio
from .keyboards import get_menu_keyboard
from .admin import admin_required
import html
from pathlib import Path
import re



router = Router()


class Reg(StatesGroup):
    enter_music = State()
    delete_track = State()

current_dir = Path(__file__).parent  

photo_path = current_dir.parent / "menu_photo.jpg"

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

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


@router.message(Command("menu"))
@admin_required()
async def show_menu(message: Message):
    photo = FSInputFile(photo_path)
    await message.answer_photo(photo=photo, caption="🎧 Главное меню:", reply_markup=get_menu_keyboard())


@router.callback_query(lambda c: c.data == "add_music")
@admin_required()
async def add_music_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.enter_music)
    await callback.message.answer("Введите песню, которую хотите найти 🎵")
    await callback.answer()


@router.message(Reg.enter_music, F.audio)
@admin_required()
async def enter_music_audio(message: Message, state: FSMContext):
    if len(list_musics) >= 5:
        await message.answer("❌ Очередь уже заполнена! Пожалуйста, удалите лишние треки.")
        return

    audio = message.audio
    base_name = audio.file_name or audio.title or f"audio_{audio.file_unique_id}"
    ext = Path(base_name).suffix or ext_from_mime(audio.mime_type or "")
    safe_name = sanitize_filename(Path(base_name).stem) + ext
    dest_path = DOWNLOADS_DIR / safe_name

    await message.answer("⬇️ Сохраняю ваш аудиофайл...")
    try:
        await message.bot.download(audio, destination=dest_path)
        list_musics.append(dest_path.name)
        await state.clear()
        await message.answer(f"✅ Файл '{dest_path.name}' добавлен в очередь!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении файла: {str(e)}")

@router.message(Reg.enter_music, F.document)
@admin_required()
async def enter_music_document(message: Message, state: FSMContext):
    if len(list_musics) >= 5:
        await message.answer("❌ Очередь уже заполнена! Пожалуйста, удалите лишние треки.")
        return

    doc = message.document
    allowed_ext = {".mp3", }
    file_name = doc.file_name or f"file_{doc.file_unique_id}"
    ext = Path(file_name).suffix.lower()
    if ext not in allowed_ext:
        await message.answer("❌ Это не аудиофайл поддерживаемого формата. Пришлите .mp3")
        return

    safe_name = sanitize_filename(Path(file_name).stem) + ext
    dest_path = DOWNLOADS_DIR / safe_name

    await message.answer("⬇️ Сохраняю ваш файл...")
    try:
        await message.bot.download(doc, destination=dest_path)
        list_musics.append(dest_path.name)
        await state.clear()
        await message.answer(f"✅ Файл '{dest_path.name}' добавлен в очередь!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении файла: {str(e)}")

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_name = html.escape(message.from_user.full_name)
    await message.answer(
        f"Привет {user_name}! 🎶\nЭто музыкальный бот, который умеет искать и включать музыку!",
    )


@router.message(Command("menu"))
@admin_required()
async def show_menu(message: Message):
    photo = FSInputFile(photo_path)
    await message.answer_photo(photo=photo, caption="🎧 Главное меню:", reply_markup=get_menu_keyboard())


@router.callback_query(lambda c: c.data == "add_music")
@admin_required()
async def add_music_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.enter_music)
    await callback.message.answer("Введите песню, которую хотите найти 🎵")
    await callback.answer()


@router.message(Reg.enter_music)
@admin_required()
async def enter_music(message: Message, state: FSMContext):
    query = message.text
    await message.answer("🔍 Ищу и скачиваю музыку...")
    try:
        filename = download_audio_from_youtube(query)
        if len(list_musics) >= 5:
            await message.answer("❌ Очередь уже заполнена! Пожалуйста, удалите лишние треки.")
            return
        list_musics.append(filename)
        await state.update_data(audio_filename=filename)
        await message.answer(f"✅ Песня '{filename}' найдена и добавлена в очередь!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при скачивании: {str(e)}")
    finally:
        await state.clear()


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
        await callback.message.answer("Очередь пуста! 💤")
        await callback.answer()
        return

    await callback.message.answer("▶️ Воспроизвожу все песни по очереди...")
    await play_audio_in_call()
    await callback.answer()


@router.callback_query(F.data == "clear_queue")
@admin_required()
async def play_all_callback(callback: CallbackQuery):
    list_musics.clear()
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
async def resume_track(callback: CallbackQuery):
    await leave_audio()
    await callback.answer("🚪Выйти из звонка")

@router.callback_query(F.data == "clear_count_queue")
@admin_required()
async def clear_count_queue(callback: CallbackQuery, state: FSMContext):
    if not list_musics:
        await callback.message.answer("Очередь пуста! 💤")
        await callback.answer()
        return

    queue_text = "🎵 Текущая очередь песен:\n"
    for i, music in enumerate(list_musics, 1):
        queue_text += f"{i}. {music.replace('.mp3', '')}\n"
    await callback.message.answer(f"{queue_text}\nВведите номер трека, который хотите удалить:")
    await state.set_state(Reg.delete_track)
    await callback.answer()

@router.message(Reg.delete_track)
@admin_required()
async def delete_track(message: Message, state: FSMContext):
    try:
        index = int(message.text) - 1 
        if 0 <= index < len(list_musics):
            deleted_track = list_musics.pop(index)
            await message.answer(f"🗑 Трек '{deleted_track.replace('.mp3', '')}' удален из очереди!")
        else:
            await message.answer("❌ Неверный номер трека! Пожалуйста, выберите номер из списка.")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число, соответствующее номеру трека.")
    finally:
        await state.clear()
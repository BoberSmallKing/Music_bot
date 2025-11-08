from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="▶️ Сыграть все", callback_data="play_all")],
        [InlineKeyboardButton(text="🎵 Очередь", callback_data="show_queue")],
        [InlineKeyboardButton(text="🗑️ Очистить очередь", callback_data="clear_queue")],
        [InlineKeyboardButton(text="▶️ play", callback_data="resume_audio"), InlineKeyboardButton(text="⏸️ pause", callback_data="pause_audio")],
        [InlineKeyboardButton(text="⏭️ Следуйщая", callback_data="next_track"), InlineKeyboardButton(text="🚪 Выйти", callback_data="exit")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
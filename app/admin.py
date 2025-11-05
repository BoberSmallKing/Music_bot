from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from functools import wraps
from typing import Callable, Any, Union


async def is_chat_admin(bot: Bot, user_id: int, chat_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором или создателем чата.
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print(f"[AdminCheck] Ошибка проверки прав администратора: {e}")
        return False


def admin_required(alert_text: str = "❌ У вас нет прав администратора!"):
    """
    Декоратор проверки администратора чата или канала (включая обсуждения).
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(event: Union[Message, CallbackQuery], *args: Any, **kwargs: Any):
            bot: Bot = event.bot

            # Определяем chat_id
            chat_id = (
                event.message.chat.id if isinstance(event, CallbackQuery)
                else event.chat.id
            )

            # --- Определяем user_id ---
            user_id = None
            if hasattr(event, "from_user") and event.from_user:
                user_id = event.from_user.id
            elif hasattr(event, "sender_chat") and event.sender_chat:
                # Если пишет канал (в обсуждениях)
                user_id = event.sender_chat.id

            if user_id is None:
                print("[AdminCheck] Не удалось определить пользователя.")
                if isinstance(event, CallbackQuery):
                    await event.answer(alert_text, show_alert=True)
                return

            # Проверяем права
            if await is_chat_admin(bot, user_id, chat_id):
                return await func(event, *args, **kwargs)
            else:
                if isinstance(event, CallbackQuery):
                    await event.answer(alert_text, show_alert=True)
                # Можно убрать, если не хочешь текст при сообщениях
                elif isinstance(event, Message):
                    await event.reply(alert_text)

        return wrapper
    return decorator

from aiogram.types import Message, CallbackQuery
from functools import wraps
from typing import Callable, Any, Union

# Укажи здесь свои Telegram ID администраторов
ADMIN_IDS: set[int] = {2106925564}


def admin_required(alert_text: str = "❌ У вас нет прав администратора!"):
    """
    Декоратор для проверки администратора в личных сообщениях (private chat).
    Работает как с Message, так и с CallbackQuery.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(event: Union[Message, CallbackQuery], *args: Any, **kwargs: Any):
            # Определяем чат
            chat = event.message.chat if isinstance(event, CallbackQuery) else event.chat

            # Проверяем, что чат приватный
            if chat.type != "private":
                text = "⚠️ Эта команда доступна только в личных сообщениях."
                if isinstance(event, CallbackQuery):
                    await event.answer(text, show_alert=True)
                else:
                    await event.answer(text)
                return

            # Проверяем ID пользователя
            user_id = getattr(event.from_user, "id", None)
            if user_id in ADMIN_IDS:
                return await func(event, *args, **kwargs)

            # Если пользователь не админ
            if isinstance(event, CallbackQuery):
                await event.answer(alert_text, show_alert=True)
            else:
                await event.answer(alert_text)
        return wrapper
    return decorator

from aiogram.types import CallbackQuery
from functools import wraps

def admin_required():
    """
    Декоратор для проверки, является ли пользователь администратором канала
    при вызове callback-кнопок.
    """
    def decorator(handler):
        @wraps(handler)
        async def wrapper(callback: CallbackQuery, *args, **kwargs):
            bot = callback.message.bot
            chat_id = callback.message.chat.id
            user_id = callback.from_user.id

            try:
                admins = await bot.get_chat_administrators(chat_id)
                admin_ids = [admin.user.id for admin in admins]
                if user_id in admin_ids:
                    return await handler(callback, *args, **kwargs)
                else:
                    await callback.answer(
                        "❌ У вас нет прав для выполнения этого действия!"
                    )
                    await callback.answer()
            except Exception as e:
                await callback.answer(
                    f"❌ Ошибка при проверке прав администратора: {str(e)}"
                )
                await callback.answer()

        return wrapper
    return decorator
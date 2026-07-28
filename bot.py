import logging
import re
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ВАШИ НАСТРОЙКИ ---
TOKEN = "8807518141:AAHLfuZraY9p_dmNELs5XL2Vd7vil1Uo0jo"
CHANNEL_USERNAME = "@RaskolDM"
ADMIN_ID = 8428373910
# -----------------


async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверка, подписан ли пользователь на канал."""
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id
        )
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    is_subscribed = await check_subscription(user.id, context)

    if not is_subscribed:
        # Для неподписанных оставляем инлайн-кнопку подписаться, чтобы было удобно перейти в канал
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
                )
            ],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")], # Обратите внимание: проверка подписки в таком виде останется через инлайн, либо можно сделать текстом.
        ]
        # Проще сделать проверку подписки текстом или кнопкой. Давайте сделаем через обычную кнопку:
        pass

    # Перепишем логику для обычной клавиатуры:
    if not is_subscribed:
        keyboard = [["✅ Проверить подписку"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ Чтобы пользоваться ботом, вы должны быть подписаны на наш канал: {CHANNEL_USERNAME}\n\n"
            "После подписки нажмите кнопку ниже:",
            reply_markup=reply_markup,
        )
        return

    await send_main_menu(update)


async def send_main_menu(update: Update):
    """Отправка главного меню с обычной клавиатурой"""
    keyboard = [
        ["💬 Написать рассылку", "🚫 Не нажимать"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:", reply_markup=reply_markup
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений и нажатий на кнопки клавиатуры"""
    text = update.message.text
    user = update.effective_user

    # 1. Проверка подписки по текстовой кнопке
    if text == "✅ Проверить подписку":
        is_subscribed = await check_subscription(user.id, context)
        if is_subscribed:
            await send_main_menu(update)
        else:
            await update.message.reply_text("❌ Вы всё еще не подписаны на канал!")
        return

    # 2. Кнопка «Написать рассылку»
    if text == "💬 Написать рассылку":
        context.user_data["waiting_for_text"] = True
        await update.message.reply_text(
            "✍️ Отправьте ваше сообщение, и оно будет передано администратору:"
        )
        return

    # 3. Кнопка «Не нажимать»
    if text == "🚫 Не нажимать":
        await update.message.reply_text("Бурмалда")
        return

    # 4. Обработка ввода текста после нажатия «Написать рассылку»
    if context.user_data.get("waiting_for_text"):
        context.user_data["waiting_for_text"] = False

        username_str = f"@{user.username}" if user.username else "отсутствует"
        user_info = (
            f"📩 Новое сообщение от пользователя!\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Юзернейм: {username_str}\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"💬 Текст:\n{text}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID, text=user_info, parse_mode="Markdown"
        )

        await update.message.reply_text(
            "✅ Ваше сообщение успешно отправлено администратору!"
        )
        await send_main_menu(update)


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция для ответа администратора пользователю через Reply"""
    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message and update.message.reply_to_message.text:
        reply_text = update.message.reply_to_message.text
        
        match = re.search(r"🆔 ID:\s*`?(\d+)`?", reply_text)
        if match:
            target_user_id = int(match.group(1))
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📩 Ответ от администратора:\n\n{update.message.text}",
                )
                await update.message.reply_text("✅ Ответ успешно отправлен пользователю!")
            except Exception as e:
                await update.message.reply_text(f"Не удалось отправить ответ: {e}")
        else:
            await update.message.reply_text("❌ Не удалось распознать ID пользователя в этом сообщении.")


def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    
    # Обработка ответов администратора
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(user_id=ADMIN_ID) & filters.REPLY,
            admin_reply,
        )
    )
    
    # Обработка обычных текстовых сообщений и нажатий на кнопки клавиатуры
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()

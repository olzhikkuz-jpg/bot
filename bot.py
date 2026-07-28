import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8807518141:AAHLfuZraY9p_dmNELs5XL2Vd7vil1Uo0jo"
CHANNEL_USERNAME = "@RaskolDM"
ADMIN_ID = 8428373910

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
    user = update.effective_user
    is_subscribed = await check_subscription(user.id, context)

    if not is_subscribed:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
                )
            ],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Чтобы пользоваться ботом, вы должны быть подписаны на наш канал!",
            reply_markup=reply_markup,
        )
        return

    await send_main_menu(update, context)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 Написать рассылку", callback_data="btn_write")],
        [InlineKeyboardButton("🚫 Не нажимать", callback_data="btn_dont_click")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(
            "Добро пожаловать! Выберите действие:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Добро пожаловать! Выберите действие:", reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "check_sub":
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await query.message.delete()
            update.message = query.message
            await start_command(update, context)
        else:
            await query.answer(
                "Вы всё еще не подписаны на канал!", show_alert=True
            )

    elif query.data == "btn_write":
        context.user_data["waiting_for_text"] = True
        await query.message.reply_text(
            "✍️ Отправьте ваше сообщение, и оно будет передано администратору:"
        )

    elif query.data == "btn_dont_click":
        await query.message.reply_text("Бурмалда")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_text"):
        user = update.effective_user
        text = update.message.text

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
        await send_main_menu(update, context)

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text
        try:
            for line in reply_text.split("\n"):
                if "🆔 ID:" in line:
                    target_user_id = int(line.split("`")[1])
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"📩 Ответ от администратора:\n\n{update.message.text}",
                    )
                    await update.message.reply_text("✅ Ответ успешно отправлен пользователю!")
                    return
        except Exception as e:
            await update.message.reply_text(f"Не удалось отправить ответ: {e}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(user_id=ADMIN_ID) & filters.REPLY,
            admin_reply,
        )
    )
    
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
    )

    application.run_polling()

if __name__ == "__main__":
    main()

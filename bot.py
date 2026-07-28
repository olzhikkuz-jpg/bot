username_str = f"@{user.username}" if user.username else "отсутствует"
        user_info = (
            f"📩 Новое сообщение от пользователя!\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Юзернейм: {username_str}\n"
            f"🆔 ID: {user.id}\n\n"
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
    """Функция для ответа админа (пересылка ответа пользователю через бота)"""
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


if name == "main":
    main()

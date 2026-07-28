# Формируем информацию для администратора
    user_info = (
        f"📩 Новое сообщение от пользователя!\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Юзернейм: @{user.username if user.username 'отсутствует'}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 Текст:\n{text}"
    )

    # Отправляем сообщение вам (админу)
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

  # Чтобы ответить, администратор должен сделать Reply (ответ) на сообщение бота,
  # содержащее ID пользователя. Бот автоматически извлечет ID из текста сообщения.
  if update.message.reply_to_message:
    reply_text = update.message.reply_to_message.text
    try:
      # Ищем ID в тексте сообщения по тегу "🆔 ID:"
      for line in reply_text.split("\n"):
        if "🆔 ID:" in line:
          target_user_id = int(
              line.split("`")[1]
          )  # Достаем ID из обратных кавычек
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

  # Регистрация обработчиков
  application.add_handler(CommandHandler("start", start_command))
  application.add_handler(CallbackQueryHandler(button_handler))
  
  # Обработка ответов администратора (если админ отвечает реплаем)
  application.add_handler(
      MessageHandler(
          filters.TEXT & filters.User(user_id=ADMIN_ID) & filters.REPLY,
          admin_reply,
      )
  )
  
  # Обработка обычного текста от пользователей
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
  )

  # Запуск бота
  application.run_polling()


if name == "main":
  main()
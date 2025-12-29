from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

# 1) Import start_chat_libre en el bloque start
if "start_chat_libre" not in s:
    s = s.replace(
        "    menu_command\n)",
        "    menu_command,\n    start_chat_libre\n)"
    )

# 2) Import handle_free_chat
if "from app.handlers.chat_handler import handle_free_chat" not in s:
    idx = s.find("from app.handlers.products import")
    if idx == -1:
        raise SystemExit("No encontré: from app.handlers.products import")
    s = s[:idx] + "from app.handlers.chat_handler import handle_free_chat\n\n" + s[idx:]

# 3) Handler callback chat_libre
if 'pattern="^chat_libre$"' not in s:
    s = s.replace(
        'application.add_handler(CallbackQueryHandler(show_contact, pattern="^menu_contacto$"))',
        'application.add_handler(CallbackQueryHandler(show_contact, pattern="^menu_contacto$"))\napplication.add_handler(CallbackQueryHandler(start_chat_libre, pattern="^chat_libre$"))'
    )

# 4) Handler mensajes: insertar justo antes del run_polling (sin depender de logger.info)
needle = 'application.run_polling(allowed_updates=["message", "callback_query"])'
insert = 'application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_chat))\n\n' + needle
if "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_chat)" not in s:
    if needle not in s:
        raise SystemExit("No encontré run_polling para insertar antes.")
    s = s.replace(needle, insert)

p.write_text(s, encoding="utf-8")
print("✅ main.py parcheado correctamente")

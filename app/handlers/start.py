"""
Telegram Bot Handlers
Handler para el comando /start
"""

async def start_handler(update, context):
    """Handler para el comando /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'¡Hola {user.first_name}! Bienvenido a Milhoja Dres Bot.'
    )

# TODO: Implementar handlers completos

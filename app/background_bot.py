"""
Bot de Telegram corriendo en background thread mientras FastAPI escucha en puerto 8000
"""
import asyncio
import logging
import threading
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.routes.telegram_routes import start_command, handle_user_message
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def polling_main():
    """Inicia el bot en modo POLLING"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN no configurado")
        return

    logger.info("🚀 Iniciando bot de Telegram en POLLING mode...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
    )

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("✅ Bot en POLLING mode - esperando mensajes...")
        try:
            await asyncio.Event().wait()  # Run forever
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido")


def start_bot_background():
    """
    Inicia el bot en un thread separado para que no bloquee FastAPI
    """
    def run_bot():
        try:
            asyncio.run(polling_main())
        except Exception as e:
            logger.error(f"❌ Error en bot: {e}")
    
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    logger.info("💫 Bot thread iniciado en background")

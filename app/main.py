"""
Bot principal de Telegram para Milhoja Dres
"""
import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler
)
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importar handlers (ahora funciona limpiamente)
from app.handlers.start import (
    start_command,
    show_main_menu,
    show_order_menu,
    show_my_orders,
    show_info,
    show_contact,
    help_command,
    menu_command
)
from app.handlers.products import (
    show_products_by_category,
    show_product_detail,
    add_to_cart,
    view_cart,
    clear_cart,
    confirm_order
)


def main():
    """
    Función principal para iniciar el bot
    """
    # Obtener token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN no encontrado en .env")
        return
    
    # Crear aplicación
    application = Application.builder().token(token).build()
    
    # ========================================
    # COMANDOS
    # ========================================
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # ========================================
    # CALLBACKS - MENÚ PRINCIPAL
    # ========================================
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^menu_volver$"))
    application.add_handler(CallbackQueryHandler(show_order_menu, pattern="^menu_hacer_pedido$"))
    application.add_handler(CallbackQueryHandler(show_my_orders, pattern="^menu_mis_pedidos$"))
    application.add_handler(CallbackQueryHandler(show_info, pattern="^menu_informacion$"))
    application.add_handler(CallbackQueryHandler(show_contact, pattern="^menu_contacto$"))
    
    # ========================================
    # CALLBACKS - PRODUCTOS
    # ========================================
    application.add_handler(CallbackQueryHandler(show_products_by_category, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(show_product_detail, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    
    # ========================================
    # CALLBACKS - CARRITO
    # ========================================
    application.add_handler(CallbackQueryHandler(view_cart, pattern="^view_cart$"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_order$"))
    
    # ========================================
    # INICIAR BOT
    # ========================================
    logger.info("🚀 Bot iniciado correctamente")
    logger.info("🔗 Esperando mensajes...")
    
    # Iniciar polling
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()

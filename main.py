"""
Bot principal de Telegram para Milhojaldres
"""

import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
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

# Importar handlers de start y productos
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

# Importar handlers de pre-órdenes
from app.handlers.preorders import (
    start_preorder,
    select_customer_type,
    receive_email,
    handle_phone_selection,
    receive_phone,
    receive_company,
    show_location_selection,
    select_location,
    select_date,
    select_time,
    confirm_preorder,
    cancel_preorder,
    SELECTING_TYPE,
    ENTERING_EMAIL,
    ENTERING_PHONE,
    ENTERING_COMPANY,
    SELECTING_LOCATION,
    SELECTING_DATE,
    SELECTING_TIME,
    CONFIRMING_PREORDER
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
    # CONVERSATION HANDLER - PRE-ÓRDENES
    # ========================================
    preorder_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_preorder, pattern="^start_preorder$")
        ],
        states={
            SELECTING_TYPE: [
                CallbackQueryHandler(select_customer_type, pattern="^preorder_type_")
            ],
            ENTERING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)
            ],
            ENTERING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
            ],
            ENTERING_COMPANY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_company)
            ],
            SELECTING_LOCATION: [
                CallbackQueryHandler(handle_phone_selection, pattern="^preorder_use_saved_phone$"),
                CallbackQueryHandler(handle_phone_selection, pattern="^preorder_enter_new_phone$"),
                CallbackQueryHandler(select_location, pattern="^preorder_loc_")
            ],
            SELECTING_DATE: [
                CallbackQueryHandler(select_date, pattern="^preorder_date_"),
                CallbackQueryHandler(show_location_selection, pattern="^preorder_change_location$")
            ],
            SELECTING_TIME: [
                CallbackQueryHandler(select_time, pattern="^preorder_time_"),
                CallbackQueryHandler(select_date, pattern="^preorder_change_date$")
            ],
            CONFIRMING_PREORDER: [
                CallbackQueryHandler(confirm_preorder, pattern="^preorder_confirm$"),
                CallbackQueryHandler(start_preorder, pattern="^preorder_edit$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(view_cart, pattern="^view_cart$"),
            CallbackQueryHandler(show_main_menu, pattern="^menu_volver$"),
            CommandHandler("start", start_command)
        ],
        name="preorder_conversation",
        persistent=False
    )
    
    application.add_handler(preorder_conv_handler)

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

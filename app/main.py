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

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS - HANDLERS PRINCIPALES
# ==========================================

from app.handlers.start import (
    start_command,
    show_main_menu,
    show_order_menu,
    show_my_orders,
    show_info,
    show_contact,
    help_command,
    menu_command,
    start_chat_libre
)


from app.handlers.chat_handler import handle_free_chat

# ==========================================
# IMPORTS - HANDLERS PRODUCTOS Y CARRITO
# ==========================================

from app.handlers.products import (
    show_products_by_category,
    show_product_detail,
    add_to_cart,
    view_cart,
    clear_cart,
    confirm_order
)

# ==========================================
# IMPORTS - HANDLERS ADMIN
# ==========================================

from app.handlers.admin import (
    admin_panel,
    admin_view_orders,
    admin_order_detail,
    admin_change_status,
    admin_stats,
    ADMIN_IDS
)

# ==========================================
# IMPORTS - HANDLERS PRE-ÓRDENES
# ==========================================

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

# ==========================================
# IMPORTS - HANDLERS CHAT IA
# ==========================================

from app.handlers.chat_handler import (
    start_chat,
    handle_chat_message,
    exit_chat
)

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

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

    # ==========================================
    # SECTION 1: COMANDOS BASE
    # ==========================================
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))

    # ==========================================
    # SECTION 2: CONVERSATION HANDLER - PRE-ÓRDENES
    # ==========================================
    
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

    # ============ CHAT LIBRE ============
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_chat))


    # ==========================================
    # SECTION 3: CALLBACKS - MENÚ PRINCIPAL
    # ==========================================
    
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^menu_volver$"))
    application.add_handler(CallbackQueryHandler(show_order_menu, pattern="^menu_hacer_pedido$"))
    application.add_handler(CallbackQueryHandler(show_my_orders, pattern="^menu_mis_pedidos$"))
    application.add_handler(CallbackQueryHandler(show_info, pattern="^menu_informacion$"))
    application.add_handler(CallbackQueryHandler(show_contact, pattern="^menu_contacto$"))

    # ==========================================
    # SECTION 4: CALLBACKS - PRODUCTOS
    # ==========================================
    
    application.add_handler(CallbackQueryHandler(show_products_by_category, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(show_product_detail, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))

    # ==========================================
    # SECTION 5: CALLBACKS - CARRITO
    # ==========================================
    
    application.add_handler(CallbackQueryHandler(view_cart, pattern="^view_cart$"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_order$"))

    # ==========================================
    # SECTION 6: CALLBACKS - ADMIN
    # ==========================================
    
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(admin_view_orders, pattern="^admin_orders_"))
    application.add_handler(CallbackQueryHandler(admin_order_detail, pattern="^admin_order_detail_"))
    application.add_handler(CallbackQueryHandler(admin_change_status, pattern="^admin_change_status_"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))

    # ==========================================
    # SECTION 7: CALLBACKS - CHAT IA
    # ==========================================
    
    application.add_handler(CallbackQueryHandler(start_chat, pattern="^chat_libre$"))
    application.add_handler(CallbackQueryHandler(exit_chat, pattern="^exit_chat$"))

    # ==========================================
    # SECTION 8: INICIAR BOT
    # ==========================================
    
    logger.info("🚀 Bot iniciado correctamente")
    logger.info("🔗 Esperando mensajes...")

    # ==========================================
    # SECTION 9: MESSAGE HANDLER (SIEMPRE AL FINAL)
    # ==========================================
    # IMPORTANTE: Este handler debe ir AL FINAL para no bloquear callbacks
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message))

    # Log TODOS los callbacks
    async def log_update(update, context):
        if update.callback_query:
            logger.info(f"🔍 CALLBACK: {update.callback_query.data}")

    application.add_handler(CallbackQueryHandler(log_update), group=-1)

    # RUN POLLING
    application.run_polling(allowed_updates=["message", "callback_query"])


   
# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == '__main__':
    main()

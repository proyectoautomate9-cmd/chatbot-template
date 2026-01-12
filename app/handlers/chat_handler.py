"""
Handler para chat libre con IA
"""


import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.services.ai_service import AIService


logger = logging.getLogger(__name__)
ai_service = AIService()



async def start_chat_libre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Inicia el modo de chat libre con IA
    """
    query = update.callback_query
    await query.answer()
    
    # Marcar que el usuario está en modo chat libre
    context.user_data['chat_libre_mode'] = True
    context.user_data['chat_history'] = []  # Inicializar historial
    
    keyboard = [
        [InlineKeyboardButton("❌ Salir del Chat", callback_data="exit_chat")],
        [InlineKeyboardButton("🔙 Menú Principal", callback_data="menu_volver")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "💬 *Modo Chat Libre Activado*\n\n"
        "Ahora puedes hablar libremente conmigo. "
        "Responderé usando inteligencia artificial.\n\n"
        "Escribe cualquier pregunta o mensaje."
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    logger.info(f"Usuario {update.effective_user.id} inició chat libre")



async def handle_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja mensajes en modo chat libre (cuando el usuario escribe sin estar en conversación)
    """
    # Solo procesar si NO está en una conversación activa
    if context.user_data.get('in_conversation'):
        return
    
    user_message = update.message.text
    user_id = update.effective_user.id
    
    try:
        # Mostrar que el bot está escribiendo
        await update.message.chat.send_action("typing")
        
        # Obtener respuesta de IA
        response_data = ai_service.get_response(
            query=user_message,
            user_id=user_id,
            chat_history=context.user_data.get('chat_history', [])
        )
        
        response = response_data.get('respuesta', 'Lo siento, no pude procesar tu mensaje.')
        intent = response_data.get('intent', 'info')
        suggestions = response_data.get('suggested_products', [])
        
        # Actualizar historial (guardamos el raw json string para contexto futuro si es necesario, 
        # o solo texto. Por ahora texto es mas seguro para no confundir al modelo con json parciales)
        if 'chat_history' not in context.user_data:
            context.user_data['chat_history'] = []
        
        context.user_data['chat_history'].append({'role': 'user', 'content': user_message})
        # Guardamos la respuesta textual en el historial
        context.user_data['chat_history'].append({'role': 'assistant', 'content': response})
        
        # Mantener solo últimos 10 mensajes
        if len(context.user_data['chat_history']) > 10:
            context.user_data['chat_history'] = context.user_data['chat_history'][-10:]
            
        # Generar botones si hay intención de compra
        reply_markup = None
        if intent == 'purchase' and suggestions:
            keyboard = []
            for prod in suggestions:
                p_id = prod.get('product_id')
                p_name = prod.get('name', 'Producto')
                qty = prod.get('quantity', 1)
                
                if p_id:
                     keyboard.append([
                        InlineKeyboardButton(
                            f"🛒 Agregar {p_name} (x{qty})", 
                            callback_data=f"smart_add_{p_id}_{qty}"
                        )
                    ])
            
            if keyboard:
                keyboard.append([InlineKeyboardButton("🔙 Menú Principal", callback_data="menu_volver")])
                reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar respuesta
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        
        logger.info(f"Chat libre procesado. Intent: {intent}")
        
    except Exception as e:
        logger.error(f"Error en handle_free_chat: {e}")
        await update.message.reply_text(
            "❌ Ocurrió un error procesando tu mensaje. "
            "Por favor intenta de nuevo."
        )



async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja mensajes cuando el usuario está en modo chat libre activo
    """
    # Solo procesar si está en modo chat libre
    if not context.user_data.get('chat_libre_mode'):
        # Si no está en modo chat libre, pasar al handle_free_chat
        return await handle_free_chat(update, context)
    
    user_message = update.message.text
    user_id = update.effective_user.id
    
    try:
        # Mostrar que el bot está escribiendo
        await update.message.chat.send_action("typing")
        
        # Obtener respuesta de IA
        response_data = ai_service.get_response(
            query=user_message,
            user_id=user_id,
            chat_history=context.user_data.get('chat_history', [])
        )
        
        response = response_data.get('respuesta', 'Lo siento, no pude procesar tu mensaje.')
        
        # Actualizar historial
        if 'chat_history' not in context.user_data:
            context.user_data['chat_history'] = []
        
        context.user_data['chat_history'].append({'role': 'user', 'content': user_message})
        context.user_data['chat_history'].append({'role': 'assistant', 'content': response})
        
        # Mantener solo últimos 10 mensajes
        if len(context.user_data['chat_history']) > 10:
            context.user_data['chat_history'] = context.user_data['chat_history'][-10:]
        
        # Botón para salir del chat
        keyboard = [
            [InlineKeyboardButton("❌ Salir del Chat", callback_data="exit_chat")],
            [InlineKeyboardButton("🔙 Menú Principal", callback_data="menu_volver")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar respuesta con botones
        await update.message.reply_text(
            response,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        logger.info(f"Mensaje de chat procesado para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error en handle_chat_message: {e}")
        await update.message.reply_text(
            "❌ Ocurrió un error procesando tu mensaje. "
            "Por favor intenta de nuevo."
        )



async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sale del modo de chat libre
    """
    query = update.callback_query
    await query.answer()
    
    # Desactivar modo chat libre
    context.user_data['chat_libre_mode'] = False
    context.user_data['chat_history'] = []  # Limpiar historial
    
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("💬 Chat Libre", callback_data="chat_libre")],
        [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="✅ Has salido del modo chat libre.\n\n¿Qué te gustaría hacer?",
        reply_markup=reply_markup
    )
    
    logger.info(f"Usuario {update.effective_user.id} salió del chat libre")

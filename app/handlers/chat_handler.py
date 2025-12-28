"""Handler para Chat IA"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.database import get_supabase
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

# Inicializar AIService
ai_service = None

def get_ai_service():
    """Lazy load AIService"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service


async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia chat IA"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"💬 Usuario {update.effective_user.id} inició chat IA")
    
    context.user_data['chat_mode'] = True
    context.user_data['chat_history'] = []
    
    text = (
        f"💬 **CHAT IA ACTIVADO**\n\n"
        f"Pregúntame sobre:\n"
        f"• Horarios\n"
        f"• Métodos de pago\n"
        f"• Ubicación\n"
        f"• Productos\n\n"
        f"✍️ Escribe tu pregunta:"
    )
    
    keyboard = [
        [InlineKeyboardButton("❌ Salir", callback_data="exit_chat")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu_volver")]
    ]
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de chat"""
    if not context.user_data.get('chat_mode', False):
        return
    
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"💬 Usuario {user.id}: {message_text}")
    
    try:
        supabase = get_supabase()
        user_response = supabase.table("users").select("user_id").eq("telegram_id", user.id).execute()
        user_id = user_response.data[0]['user_id'] if user_response.data else user.id
        
        await update.message.chat.send_action("typing")
        
        chat_history = context.user_data.get('chat_history', [])
        response = ai_service.get_response(message_text, user_id, chat_history)
        
        respuesta = response['respuesta']
        confianza = response['confianza']
        fuente = response['fuente']
        
        chat_history.append({'role': 'user', 'content': message_text})
        chat_history.append({'role': 'assistant', 'content': respuesta})
        context.user_data['chat_history'] = chat_history[-10:]
        
        emoji = "📚" if fuente == "kb" else "🤖"
        threshold = float(os.getenv("CHAT_CONFIDENCE_THRESHOLD", "0.8"))
        
        if confianza < threshold:
            respuesta += "\n\n⚠️ _WhatsApp: 3014170313 para más info_"
        
        keyboard = [
            [InlineKeyboardButton("❌ Salir", callback_data="exit_chat")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu_volver")]
        ]
        
        await update.message.reply_text(
            f"{emoji} {respuesta}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Respuesta: fuente={fuente}, confianza={confianza}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Error. Intenta de nuevo.")

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sale del chat"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"👋 Usuario {update.effective_user.id} salió del chat")
    
    context.user_data['chat_mode'] = False
    
    text = "👋 **CHAT FINALIZADO**\n\n¿Qué deseas hacer?"
    
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("💬 Chat IA", callback_data="chat_libre")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu_volver")]
    ]
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

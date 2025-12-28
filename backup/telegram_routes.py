import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from openai import AsyncOpenAI
from app.services.database import DatabaseService
from config.prompts import get_system_prompt, get_returning_customer_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clientes
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = DatabaseService()


async def get_ai_response(user_message: str, user_name: str, user_id: int) -> str:
    """Obtiene respuesta inteligente de OpenAI con contexto de BD"""
    try:
        # Obtener usuario de BD
        user = db.get_user(user_id)
        
        # Determinar prompt según el usuario
        if user:
            # Cliente recurrente
            orders = db.get_user_orders(user['user_id'], limit=1)
            last_order = orders[0]['productos'] if orders else None
            system_prompt = get_returning_customer_prompt(user_name, str(last_order))
        else:
            # Cliente nuevo
            system_prompt = get_system_prompt(user_name)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ Error con OpenAI: {e}")
        return f"¡Hola {user_name}! 👋 Estoy teniendo problemas técnicos, pero estoy aquí para ayudarte con Milhojaldres 🍰"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /start"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Usuario"
    chat_id = update.effective_chat.id
    
    logger.info(f"👤 Comando /start de {user_name} (ID: {user_id})")
    
    # Verificar si usuario existe en BD
    db_user = db.get_user(user_id)
    
    if not db_user:
        # Usuario nuevo → Crear en BD
        db.create_user(
            telegram_id=user_id,
            nombre=user_name
        )
        logger.info(f"🆕 Usuario nuevo creado: {user_name}")
        response = f"¡Hola {user_name}! 👋 Bienvenido a Milhojaldres 🍰\n\n¿En qué puedo ayudarte hoy?"
    else:
        logger.info(f"👤 Usuario existente: {user_name}")
        response = f"¡Bienvenido de nuevo {user_name}! 👋\n\n¿En qué puedo ayudarte?"
    
    await update.message.reply_text(response)


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes de usuario"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Usuario"
    message_text = update.message.text
    chat_id = update.effective_chat.id
    
    logger.info(f"📨 Mensaje de {user_name}: {message_text}")
    
    # Verificar si usuario existe en BD
    db_user = db.get_user(user_id)
    
    if not db_user:
        # Usuario nuevo → Crear en BD
        db.create_user(
            telegram_id=user_id,
            nombre=user_name
        )
        logger.info(f"🆕 Usuario nuevo creado en BD: {user_name}")
    else:
        logger.info(f"👤 Usuario existente: {user_name}")
    
    # Obtener respuesta de IA
    logger.info(f"🤖 Consultando OpenAI...")
    ai_response = await get_ai_response(message_text, user_name, user_id)
    logger.info(f"💡 Respuesta IA: {ai_response}")
    
    # Enviar respuesta
    await update.message.reply_text(ai_response)

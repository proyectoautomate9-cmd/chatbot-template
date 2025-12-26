"""
Handlers para comandos de inicio y menú principal
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.database import get_supabase
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /start
    """
    user = update.effective_user
    
    # Registrar usuario en la base de datos si no existe
    supabase = get_supabase()
    
    try:
        # Verificar si el usuario ya existe
        response = supabase.table("users")\
            .select("*")\
            .eq("telegram_id", user.id)\
            .execute()
        
        if not response.data:
            # Crear nuevo usuario
            new_user = {
                'telegram_id': user.id,
                'nombre': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Usuario'
            }
            supabase.table("users").insert(new_user).execute()
            logger.info(f"Nuevo usuario registrado: {user.id}")
    
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
    
    # Mostrar mensaje de bienvenida
    welcome_text = (
        f"👋 ¡Hola {user.first_name}!\n\n"
        "🍰 Bienvenido a **Milhoja Dres Bot**\n\n"
        "Tu asistente personal para ordenar deliciosas milhojas "
        "y bebidas artesanales.\n\n"
        "¿Qué te gustaría hacer hoy?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el menú principal
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    text = (
        f"🏠 **MENÚ PRINCIPAL**\n\n"
        f"Hola {user.first_name}, ¿qué deseas hacer?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_order_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el menú de categorías de productos
    """
    query = update.callback_query
    await query.answer()
    
    supabase = get_supabase()
    
    # Obtener categorías activas
    response = supabase.table("product_categories")\
        .select("*")\
        .eq("is_active", True)\
        .order("display_order")\
        .execute()
    
    categories = response.data
    
    text = "🛒 **HACER UN PEDIDO**\n\n"
    text += "Selecciona una categoría:\n"
    
    keyboard = []
    
    for cat in categories:
        emoji = cat.get('icon_emoji', '📦')
        name = cat['name']
        cat_id = cat['category_id']
        
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"cat_{cat_id}"
            )
        ])
    
    # Botón para ver carrito
    cart_count = len(context.user_data.get('cart', []))
    if cart_count > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"🛒 Ver Carrito ({cart_count})",
                callback_data="view_cart"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra pedidos activos y último entregado (optimizado)
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    supabase = get_supabase()
    
    try:
        # Obtener user_id
        user_response = supabase.table("users")\
            .select("user_id")\
            .eq("telegram_id", user.id)\
            .execute()
        
        if not user_response.data:
            text = "❌ Usuario no encontrado.\n\nPor favor usa /start para registrarte."
            keyboard = [[InlineKeyboardButton("🏠 Inicio", callback_data="menu_volver")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
            return
        
        user_id = user_response.data[0]['user_id']
        
        # Obtener pedidos
        response = supabase.table("orders")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("fecha_orden", desc=True)\
            .limit(10)\
            .execute()
        
        orders = response.data
        
        if not orders:
            # PRIMER PEDIDO
            text = "📦 **MIS PEDIDOS**\n\n"
            text += "🎉 ¡Aún no has hecho ningún pedido!\n\n"
            text += "Explora nuestro menú y descubre nuestras deliciosas milhojas.\n\n"
            text += "💡 _Tu primera orden está a un click de distancia_"
            
            keyboard = [
                [InlineKeyboardButton("🛒 Hacer mi Primer Pedido", callback_data="menu_hacer_pedido")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
            ]
        else:
            # Separar pedidos
            active_orders = [o for o in orders if o['estado'] in ['pending', 'confirmed', 'preparing', 'ready']]
            last_delivered = next((o for o in orders if o['estado'] == 'delivered'), None)
            
            text = "📦 **MIS PEDIDOS**\n\n"
            
            # PEDIDOS ACTIVOS
            if active_orders:
                text += "━━━ **EN PROCESO** ━━━\n\n"
                for order in active_orders:
                    order_id = order['order_id']
                    status = order['estado']
                    total = order['total']
                    created = order['fecha_orden'][:10] if order.get('fecha_orden') else 'N/A'
                    
                    # Emoji y texto de estado
                    status_info = {
                        'pending': ('🕐', 'Pendiente de confirmación'),
                        'confirmed': ('✅', 'Confirmado'),
                        'preparing': ('👨‍🍳', 'En preparación'),
                        'ready': ('📦', 'Listo para entrega')
                    }
                    emoji, status_text = status_info.get(status, ('❓', status))
                    
                    text += f"{emoji} **Orden #{order_id}**\n"
                    text += f"   📅 {created}\n"
                    text += f"   💰 ${total:,.0f}\n"
                    text += f"   Estado: _{status_text}_\n\n"
                
                text += "━━━━━━━━━━━━━━━━\n\n"
            else:
                text += "✅ ¡Todo al día!\n"
                text += "No tienes pedidos pendientes.\n\n"
                text += "━━━━━━━━━━━━━━━━\n\n"
            
            # ÚLTIMO PEDIDO ENTREGADO
            if last_delivered:
                order_id = last_delivered['order_id']
                total = last_delivered['total']
                fecha_str = last_delivered.get('fecha_orden', '')
                
                # Calcular días desde la entrega
                if fecha_str:
                    try:
                        # Manejar diferentes formatos de fecha
                        if 'T' in fecha_str:
                            fecha_orden = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                        else:
                            fecha_orden = datetime.strptime(fecha_str[:10], '%Y-%m-%d')
                        
                        dias = (datetime.now(fecha_orden.tzinfo if fecha_orden.tzinfo else None) - fecha_orden).days
                        
                        if dias == 0:
                            tiempo_text = "Hoy"
                        elif dias == 1:
                            tiempo_text = "Ayer"
                        else:
                            tiempo_text = f"Hace {dias} días"
                    except:
                        tiempo_text = fecha_str[:10]
                else:
                    tiempo_text = "Recientemente"
                
                text += "✨ **ÚLTIMO PEDIDO ENTREGADO**\n\n"
                text += f"✅ Orden #{order_id}\n"
                text += f"💰 ${total:,.0f}\n"
                text += f"📅 {tiempo_text}\n\n"
                text += "💡 _¿Te gustó? ¡Vuelve a pedir!_"
            
            # Botones
            keyboard = []
            
            # Si no hay activos, destacar "Hacer Pedido"
            if not active_orders:
                keyboard.append([
                    InlineKeyboardButton(
                        "🛒 Hacer Nuevo Pedido",
                        callback_data="menu_hacer_pedido"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        "➕ Agregar Otro Pedido",
                        callback_data="menu_hacer_pedido"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton(
                    "🏠 Menú Principal",
                    callback_data="menu_volver"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Error obteniendo pedidos: {e}")
        import traceback
        traceback.print_exc()
        
        text = (
            "❌ Error al cargar tus pedidos.\n\n"
            "Por favor intenta de nuevo más tarde."
        )
        
        keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )


async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra información sobre el negocio
    """
    query = update.callback_query
    await query.answer()
    
    text = (
        "ℹ️ **INFORMACIÓN**\n\n"
        "🍰 **Milhoja Dres**\n\n"
        "Milhojas artesanales hechas con amor y los mejores ingredientes.\n\n"
        "📍 **Ubicación:**\n"
        "Bogotá, Colombia\n\n"
        "⏰ **Horarios:**\n"
        "Lunes a Viernes: 8:00 AM - 6:00 PM\n"
        "Sábados: 9:00 AM - 5:00 PM\n"
        "Domingos: Cerrado\n\n"
        "🚚 **Entregas:**\n"
        "Realizamos entregas a domicilio en Bogotá\n"
        "Tiempo estimado: 30-45 minutos\n\n"
        "💳 **Métodos de pago:**\n"
        "• Efectivo\n"
        "• Transferencia\n"
        "• Tarjeta (contra entrega)\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra información de contacto
    """
    query = update.callback_query
    await query.answer()
    
    text = (
        "📞 **CONTACTO**\n\n"
        "¿Necesitas ayuda o tienes alguna pregunta?\n\n"
        "📱 **WhatsApp:**\n"
        "+57 300 123 4567\n\n"
        "📧 **Email:**\n"
        "info@milhojaldres.com\n\n"
        "📷 **Instagram:**\n"
        "@milhojaldres\n\n"
        "🌐 **Facebook:**\n"
        "Milhoja Dres\n\n"
        "¡Estamos para servirte!"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /help
    """
    help_text = (
        "📚 **AYUDA**\n\n"
        "**Comandos disponibles:**\n\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar esta ayuda\n"
        "/menu - Ver menú principal\n\n"
        "**¿Cómo hacer un pedido?**\n\n"
        "1. Selecciona 'Hacer un Pedido'\n"
        "2. Elige una categoría\n"
        "3. Selecciona productos\n"
        "4. Revisa tu carrito\n"
        "5. Confirma tu pedido\n\n"
        "¡Así de fácil! 🎉"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /menu
    """
    user = update.effective_user
    
    text = (
        f"🏠 **MENÚ PRINCIPAL**\n\n"
        f"Hola {user.first_name}, ¿qué deseas hacer?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

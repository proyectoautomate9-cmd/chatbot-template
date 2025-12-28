"""
Handlers para panel de administración
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.database import get_supabase
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Lista de IDs de Telegram que son administradores
ADMIN_IDS = [1567330114]  # TU TELEGRAM ID


def is_admin(user_id: int) -> bool:
    """Verifica si el usuario es administrador"""
    return user_id in ADMIN_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el panel principal de administración
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if not is_admin(user_id):
        await query.answer("⛔ No tienes permisos de administrador", show_alert=True)
        return
    
    await query.answer()
    
    supabase = get_supabase()
    
    # Obtener estadísticas rápidas
    try:
        # Total de órdenes
        orders_response = supabase.table("orders").select("*", count="exact").execute()
        total_orders = orders_response.count
        
        # Órdenes pendientes
        pending_response = supabase.table("orders").select("*", count="exact").eq("estado", "pending").execute()
        pending_orders = pending_response.count
        
        # Órdenes hoy
        today = datetime.now().strftime('%Y-%m-%d')
        today_response = supabase.table("orders").select("*", count="exact").gte("created_at", today).execute()
        today_orders = today_response.count
        
        text = "👨‍💼 **PANEL DE ADMINISTRACIÓN**\n\n"
        text += "📊 **Estadísticas:**\n\n"
        text += f"📦 Total Órdenes: **{total_orders}**\n"
        text += f"⏳ Pendientes: **{pending_orders}**\n"
        text += f"📅 Hoy: **{today_orders}**\n\n"
        text += "Selecciona una opción:"
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        text = "👨‍💼 **PANEL DE ADMINISTRACIÓN**\n\n"
        text += "Selecciona una opción:"
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Ver Órdenes Pendientes", callback_data="admin_orders_pending")
        ],
        [
            InlineKeyboardButton("✅ Ver Órdenes Confirmadas", callback_data="admin_orders_confirmed")
        ],
        [
            InlineKeyboardButton("📦 Ver Todas las Órdenes", callback_data="admin_orders_all")
        ],
        [
            InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def admin_view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra lista de órdenes según filtro
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ No tienes permisos", show_alert=True)
        return
    
    await query.answer()
    
    # Determinar filtro
    filter_type = query.data.split('_')[-1]  # pending, confirmed, all
    
    supabase = get_supabase()
    
    try:
        # Construir query según filtro
        query_builder = supabase.table("orders")\
            .select("*, users(nombre, telegram_id)")\
            .order("created_at", desc=True)\
            .limit(10)
        
        if filter_type == "pending":
            query_builder = query_builder.eq("estado", "pending")
            title = "⏳ ÓRDENES PENDIENTES"
        elif filter_type == "confirmed":
            query_builder = query_builder.eq("estado", "confirmed")
            title = "✅ ÓRDENES CONFIRMADAS"
        else:
            title = "📦 TODAS LAS ÓRDENES"
        
        response = query_builder.execute()
        orders = response.data
        
        if not orders:
            text = f"{title}\n\n"
            text += "No hay órdenes para mostrar."
        else:
            text = f"{title}\n\n"
            text += f"Mostrando últimas {len(orders)} órdenes:\n\n"
            
            for order in orders:
                order_id = order['order_id']
                estado = order['estado']
                total = order['total']
                fecha = order.get('created_at', 'N/A')[:10]
                
                # Info del usuario
                user_info = order.get('users', {})
                nombre = user_info.get('nombre', 'N/A')
                
                # Emoji según estado
                estado_emoji = {
                    'pending': '⏳',
                    'confirmed': '✅',
                    'completed': '🎉',
                    'cancelled': '❌'
                }.get(estado, '📦')
                
                text += f"{estado_emoji} **Orden #{order_id}**\n"
                text += f"👤 {nombre}\n"
                text += f"💰 ${total:,.0f}\n"
                text += f"📅 {fecha}\n"
                text += f"━━━━━━━━━━━━━━\n\n"
        
        keyboard = []
        
        # Botones de órdenes individuales (primeras 5)
        for i, order in enumerate(orders[:5]):
            order_id = order['order_id']
            keyboard.append([
                InlineKeyboardButton(
                    f"Ver Detalles Orden #{order_id}",
                    callback_data=f"admin_order_detail_{order_id}"
                )
            ])
        
        # Botones de navegación
        keyboard.append([
            InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo órdenes: {e}")
        text = "❌ Error al cargar órdenes.\n\nIntenta de nuevo."
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)


async def admin_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra detalles completos de una orden
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ No tienes permisos", show_alert=True)
        return
    
    await query.answer()
    
    # Extraer order_id
    order_id = int(query.data.split('_')[-1])
    
    supabase = get_supabase()
    
    try:
        # Obtener orden con usuario
        order_response = supabase.table("orders")\
            .select("*, users(nombre, telegram_id)")\
            .eq("order_id", order_id)\
            .single()\
            .execute()
        
        order = order_response.data
        
        # Obtener items de la orden
        items_response = supabase.table("order_items")\
            .select("*, products(nombre)")\
            .eq("order_id", order_id)\
            .execute()
        
        items = items_response.data
        
        # Construir mensaje
        estado = order['estado']
        total = order['total']
        fecha = order.get('created_at', 'N/A')[:16]
        
        user_info = order.get('users', {})
        nombre = user_info.get('nombre', 'N/A')
        telegram_id = user_info.get('telegram_id', 'N/A')
        
        # Emoji según estado
        estado_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'completed': '🎉',
            'cancelled': '❌'
        }.get(estado, '📦')
        
        text = f"📋 **DETALLE ORDEN #{order_id}**\n\n"
        text += f"Estado: {estado_emoji} **{estado.upper()}**\n\n"
        text += f"👤 **Cliente:**\n"
        text += f"Nombre: {nombre}\n"
        text += f"Telegram ID: `{telegram_id}`\n\n"
        text += f"📅 **Fecha:** {fecha}\n\n"
        text += f"📦 **Productos:**\n\n"
        
        for item in items:
            product_name = item.get('products', {}).get('nombre', 'N/A')
            cantidad = item['cantidad']
            precio = item['precio_unitario']
            subtotal = item['subtotal']
            
            text += f"• {product_name} x{cantidad}\n"
            text += f"  ${precio:,.0f} → **${subtotal:,.0f}**\n\n"
        
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"💰 **TOTAL: ${total:,.0f}**\n"
        
        # Botones de acciones
        keyboard = []
        
        # Cambiar estado según el actual
        if estado == 'pending':
            keyboard.append([
                InlineKeyboardButton(
                    "✅ Marcar como Confirmada",
                    callback_data=f"admin_change_status_{order_id}_confirmed"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    "❌ Cancelar Orden",
                    callback_data=f"admin_change_status_{order_id}_cancelled"
                )
            ])
        elif estado == 'confirmed':
            keyboard.append([
                InlineKeyboardButton(
                    "🎉 Marcar como Completada",
                    callback_data=f"admin_change_status_{order_id}_completed"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("⬅️ Volver a Lista", callback_data="admin_orders_all")
        ])
        keyboard.append([
            InlineKeyboardButton("🏠 Panel Admin", callback_data="admin_panel")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle de orden: {e}")
        import traceback
        traceback.print_exc()
        text = "❌ Error al cargar detalles de la orden."
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)


async def admin_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cambia el estado de una orden
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ No tienes permisos", show_alert=True)
        return
    
    # Extraer order_id y nuevo estado
    parts = query.data.split('_')
    order_id = int(parts[3])
    new_status = parts[4]
    
    supabase = get_supabase()
    
    try:
        # Actualizar estado
        update_response = supabase.table("orders")\
            .update({"estado": new_status})\
            .eq("order_id", order_id)\
            .execute()
        
        await query.answer(f"✅ Orden #{order_id} actualizada a {new_status}", show_alert=True)
        
        # Volver a mostrar detalles
        context.user_data['temp_callback'] = f"admin_order_detail_{order_id}"
        await admin_order_detail(update, context)
        
    except Exception as e:
        logger.error(f"Error actualizando estado: {e}")
        await query.answer("❌ Error al actualizar", show_alert=True)


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra estadísticas completas
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ No tienes permisos", show_alert=True)
        return
    
    await query.answer()
    
    supabase = get_supabase()
    
    try:
        # Total órdenes
        total_response = supabase.table("orders").select("*", count="exact").execute()
        total = total_response.count
        
        # Por estado
        pending = supabase.table("orders").select("*", count="exact").eq("estado", "pending").execute().count
        confirmed = supabase.table("orders").select("*", count="exact").eq("estado", "confirmed").execute().count
        completed = supabase.table("orders").select("*", count="exact").eq("estado", "completed").execute().count
        cancelled = supabase.table("orders").select("*", count="exact").eq("estado", "cancelled").execute().count
        
        # Total vendido
        orders_data = supabase.table("orders").select("total").execute().data
        total_ventas = sum(order['total'] for order in orders_data)
        
        # Promedio
        promedio = total_ventas / total if total > 0 else 0
        
        text = "📊 **ESTADÍSTICAS DEL NEGOCIO**\n\n"
        text += f"📦 **Total Órdenes:** {total}\n\n"
        text += f"**Por Estado:**\n"
        text += f"⏳ Pendientes: {pending}\n"
        text += f"✅ Confirmadas: {confirmed}\n"
        text += f"🎉 Completadas: {completed}\n"
        text += f"❌ Canceladas: {cancelled}\n\n"
        text += f"━━━━━━━━━━━━━━━━\n\n"
        text += f"💰 **Total Vendido:** ${total_ventas:,.0f}\n"
        text += f"📈 **Promedio/Orden:** ${promedio:,.0f}\n"
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        text = "❌ Error al cargar estadísticas."
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

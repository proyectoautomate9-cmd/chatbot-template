"""
Handlers para gestión de pre-órdenes mayoristas
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.database import get_supabase
from app.services.discount_service import DiscountService
from app.services.pdf_generator import PDFGenerator
from app.services.email_service import EmailService
import logging
from datetime import datetime, timedelta, date, time as dt_time

logger = logging.getLogger(__name__)

# Estados del ConversationHandler
(
    SELECTING_TYPE,
    ENTERING_EMAIL,
    ENTERING_PHONE,
    ENTERING_COMPANY,
    SELECTING_LOCATION,
    SELECTING_DATE,
    SELECTING_TIME,
    CONFIRMING_PREORDER
) = range(8)


async def start_preorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de pre-orden mayorista"""
    query = update.callback_query
    await query.answer()
    
    cart = context.user_data.get('cart', [])
    
    if not cart:
        text = "🛒 Tu carrito está vacío.\n\nAgrega productos primero."
        keyboard = [
            [InlineKeyboardButton("🛍️ Ver Productos", callback_data="menu_hacer_pedido")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ConversationHandler.END
    
    # Calcular descuentos
    total_quantity = sum(item['cantidad'] for item in cart)
    subtotal, desc_pct, desc_monto, total = DiscountService.calculate_discount(cart)
    
    # Guardar en context
    context.user_data['preorder_subtotal'] = subtotal
    context.user_data['preorder_descuento_pct'] = desc_pct
    context.user_data['preorder_descuento_monto'] = desc_monto
    context.user_data['preorder_total'] = total
    
    text = "📋 **CREAR PRE-ORDEN MAYORISTA**\n\n"
    text += f"🛒 Productos: {len(cart)} items ({total_quantity} unidades)\n"
    text += f"💰 Subtotal: ${subtotal:,.0f}\n"
    
    if desc_pct > 0:
        text += f"🎉 Descuento: {desc_pct}% = -${desc_monto:,.0f}\n"
    
    text += f"💵 **Total: ${total:,.0f}**\n\n"
    text += "─────────────────────\n\n"
    text += DiscountService.get_discount_info_text(total_quantity)
    text += "\n─────────────────────\n\n"
    text += "**¿Eres cliente individual o mayorista?**"
    
    keyboard = [
        [InlineKeyboardButton("👤 Individual", callback_data="preorder_type_individual")],
        [InlineKeyboardButton("🏢 Mayorista/Empresa", callback_data="preorder_type_mayorista")],
        [InlineKeyboardButton("⬅️ Volver", callback_data="view_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_TYPE


async def select_customer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja selección de tipo de cliente"""
    query = update.callback_query
    await query.answer()
    
    customer_type = query.data.split('_')[-1]
    context.user_data['preorder_tipo'] = customer_type
    
    user = update.effective_user
    supabase = get_supabase()
    
    user_response = supabase.table("users")\
        .select("*")\
        .eq("telegram_id", user.id)\
        .execute()
    
    if user_response.data:
        db_user = user_response.data[0]
        context.user_data['preorder_nombre'] = db_user.get('nombre', user.first_name)
        context.user_data['preorder_telefono'] = db_user.get('telefono', '')
    else:
        context.user_data['preorder_nombre'] = user.first_name or 'Cliente'
        context.user_data['preorder_telefono'] = ''
    
    text = "📧 **DATOS DE CONTACTO**\n\n"
    text += f"Tipo: {'🏢 Mayorista' if customer_type == 'mayorista' else '👤 Individual'}\n"
    text += f"Nombre: {context.user_data['preorder_nombre']}\n\n"
    text += "Por favor, **escribe tu email** para enviarte la cotización:"
    
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return ENTERING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y valida el email del cliente"""
    email = update.message.text.strip()
    
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ Email inválido. Por favor escribe un email válido:\n\nEjemplo: juan@email.com"
        )
        return ENTERING_EMAIL
    
    context.user_data['preorder_email'] = email
    
    await update.message.reply_text(
        "📱 **TELÉFONO**\n\nPor favor, escribe tu número de teléfono:\n\nEjemplo: 315 234 5678"
    )
    return ENTERING_PHONE


async def handle_phone_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja si usa teléfono guardado o escribe nuevo"""
    # Placeholder - implementar si es necesario
    pass


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el teléfono del cliente"""
    phone = update.message.text.strip()
    context.user_data['preorder_telefono_final'] = phone
    
    if context.user_data.get('preorder_tipo') == 'mayorista':
        await update.message.reply_text(
            "🏢 **EMPRESA (Opcional)**\n\nEscribe el nombre de tu empresa o escribe 'omitir':"
        )
        return ENTERING_COMPANY
    else:
        return await show_location_selection_from_message(update, context)


async def receive_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe nombre de empresa (opcional)"""
    company = update.message.text.strip()
    
    if company.lower() != 'omitir':
        context.user_data['preorder_empresa'] = company
    
    return await show_location_selection_from_message(update, context)


async def show_location_selection_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ubicaciones después de recibir mensaje"""
    supabase = get_supabase()
    locations = supabase.table("pickup_locations")\
        .select("*")\
        .eq("activo", True)\
        .order("orden_display")\
        .execute()
    
    text = "📍 **PUNTO DE RECOGIDA**\n\nSelecciona dónde quieres recoger tu pedido:"
    
    keyboard = []
    for loc in locations.data:
        keyboard.append([
            InlineKeyboardButton(
                f"{loc['nombre']} - {loc['barrio']}",
                callback_data=f"preorder_loc_{loc['location_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return SELECTING_LOCATION


async def show_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ubicaciones después de callback"""
    query = update.callback_query
    
    supabase = get_supabase()
    locations = supabase.table("pickup_locations")\
        .select("*")\
        .eq("activo", True)\
        .order("orden_display")\
        .execute()
    
    text = "📍 **PUNTO DE RECOGIDA**\n\nSelecciona dónde quieres recoger tu pedido:"
    
    keyboard = []
    for loc in locations.data:
        keyboard.append([
            InlineKeyboardButton(
                f"{loc['nombre']} - {loc['barrio']}",
                callback_data=f"preorder_loc_{loc['location_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return SELECTING_LOCATION


async def select_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja selección de ubicación"""
    query = update.callback_query
    await query.answer()
    
    location_id = int(query.data.split('_')[-1])
    context.user_data['preorder_location_id'] = location_id
    
    supabase = get_supabase()
    location = supabase.table("pickup_locations")\
        .select("*")\
        .eq("location_id", location_id)\
        .single()\
        .execute()
    
    loc_data = location.data
    
    text = "📅 **FECHA DE RECOGIDA**\n\n"
    text += f"📍 Lugar: {loc_data['nombre']}\n"
    text += f"   {loc_data['direccion']}, {loc_data.get('barrio', '')}\n\n"
    text += "Selecciona la fecha:"
    
    keyboard = []
    today = date.today()
    
    for i in range(1, 8):
        fecha = today + timedelta(days=i)
        dia_nombre = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha.weekday()]
        keyboard.append([
            InlineKeyboardButton(
                f"{dia_nombre} {fecha.strftime('%d/%m/%Y')}",
                callback_data=f"preorder_date_{fecha.isoformat()}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return SELECTING_DATE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja selección de fecha"""
    query = update.callback_query
    await query.answer()
    
    fecha_str = query.data.split('_')[-1]
    fecha = date.fromisoformat(fecha_str)
    context.user_data['preorder_fecha'] = fecha
    
    text = "🕐 **HORA DE RECOGIDA**\n\n"
    text += f"📅 Fecha: {fecha.strftime('%d/%m/%Y')}\n\n"
    text += "Selecciona la hora:"
    
    keyboard = []
    for hour in range(8, 19):
        hora = dt_time(hour, 0)
        keyboard.append([
            InlineKeyboardButton(
                hora.strftime('%I:%M %p'),
                callback_data=f"preorder_time_{hora.isoformat()}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return SELECTING_TIME


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja selección de hora"""
    query = update.callback_query
    await query.answer()
    
    time_str = query.data.split('_')[-1]
    hora = dt_time.fromisoformat(time_str)
    context.user_data['preorder_hora'] = hora
    
    return await show_preorder_summary(query, context)


async def show_preorder_summary(query, context: ContextTypes.DEFAULT_TYPE):
    """Muestra resumen final"""
    text = "✅ **RESUMEN DE PRE-ORDEN**\n\n"
    text += "Resumen listo. ¿Confirmar?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="preorder_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="view_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return CONFIRMING_PREORDER


async def confirm_preorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma la pre-orden"""
    query = update.callback_query
    await query.answer("✅ Pre-orden creada")
    
    text = "🎉 Pre-orden creada exitosamente!"
    
    keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ConversationHandler.END


async def cancel_preorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el flujo"""
    query = update.callback_query
    if query:
        await query.answer("Cancelado")
    
    return ConversationHandler.END

"""
Handlers para gestión de productos y carrito
"""
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.database import get_supabase
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def show_products_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra productos de una categoría específica
    """
    query = update.callback_query
    await query.answer()

    # Extraer category_id del callback_data (formato: cat_1, cat_2, etc.)
    category_id = int(query.data.split('_')[1])

    from config.database import db

    # Obtener información de la categoría
    category = db.get_category(category_id)
    
    if not category:
        await query.edit_message_text("❌ Error obteniendo categoría.")
        return

    # Obtener productos de la categoría
    products = db.get_products_by_category(category_id)

    emoji = category.get('icon_emoji', '📦')
    cat_name = category['name']

    text = f"{emoji} **{cat_name.upper()}**\n\n"

    if not products:
        text += "😕 No hay productos disponibles en esta categoría.\n\n"
    else:
        text += f"Encontrados {len(products)} producto{'s' if len(products) > 1 else ''}:\n\n"

    # Mostrar estado del carrito si hay items
    cart = context.user_data.get('cart', [])
    if cart:
        total_items = len(cart)
        total_price = sum(item['precio'] * item['cantidad'] for item in cart)
        text += f"🛒 Tu carrito: {total_items} producto{'s' if total_items > 1 else ''} | ${total_price:,.0f}\n\n"

    keyboard = []

    # Botones de productos
    for prod in products:
        nombre = prod['nombre']
        precio = prod['precio']
        prod_id = prod['product_id']
        keyboard.append([
            InlineKeyboardButton(
                f"{nombre} - ${precio:,.0f}",
                callback_data=f"prod_{prod_id}"
            )
        ])

    # Botón de ver carrito si hay items
    if cart:
        keyboard.append([
            InlineKeyboardButton(
                f"🛒 Ver Carrito ({len(cart)})",
                callback_data="view_cart"
            )
        ])

    # Botones de navegación
    keyboard.append([
        InlineKeyboardButton("📂 Otras Categorías", callback_data="menu_hacer_pedido")
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


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra detalles de un producto específico
    """
    query = update.callback_query
    await query.answer()

    # Extraer product_id del callback_data (formato: prod_123)
    product_id = int(query.data.split('_')[1])

    from config.database import db

    # Obtener producto con categoría
    product = db.get_product_by_id(product_id)
    
    if not product:
        await query.answer("❌ Producto no encontrado", show_alert=True)
        return

    # Construir mensaje
    nombre = product['nombre']
    precio = product['precio']
    descripcion = product.get('descripcion', 'Sin descripción')
    cat_info = product.get('product_categories', {})
    cat_emoji = cat_info.get('icon_emoji', '📦')
    cat_name = cat_info.get('name', 'Sin categoría')

    text = f"📦 **DETALLE DEL PRODUCTO**\n\n"
    text += f"**{nombre}**\n\n"
    text += f"{cat_emoji} Categoría: {cat_name}\n"
    text += f"💰 Precio: ${precio:,.0f}\n\n"
    text += f"📝 {descripcion}\n"

    # Mostrar estado del carrito
    cart = context.user_data.get('cart', [])
    if cart:
        total_items = len(cart)
        total_price = sum(item['precio'] * item['cantidad'] for item in cart)
        text += f"\n🛒 Tu carrito: {total_items} producto{'s' if total_items > 1 else ''} | ${total_price:,.0f}"

    # Botones mejorados (B2B + Standard)
    keyboard = [
        [
            InlineKeyboardButton("➕ Agregar 1", callback_data=f"smart_add_{product_id}_1"),
        ],
        [
            InlineKeyboardButton("📦 +6", callback_data=f"smart_add_{product_id}_6"),
            InlineKeyboardButton("📦 +12", callback_data=f"smart_add_{product_id}_12"),
             # Opción para pedir cantidad personalizada via chat
            InlineKeyboardButton("💬 Otra Cantidad", callback_data="chat_libre"),
        ]
    ]

    # Si hay items en el carrito, agregar botón de ver carrito
    if cart_len := len(cart):
        keyboard.append([
            InlineKeyboardButton(
                f"🛒 Ver Carrito ({cart_len})",
                callback_data="view_cart"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Volver a Productos",
            callback_data=f"cat_{product.get('category_id', 1)}"
        ),
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


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Agrega producto al carrito y muestra opciones claras
    """
    query = update.callback_query

    # Extraer product_id
    product_id = int(query.data.split('_')[1])

    # Inicializar carrito si no existe
    if 'cart' not in context.user_data:
        context.user_data['cart'] = []

    # Obtener info del producto
    from config.database import db
    product = db.get_product_by_id(product_id)
    
    if not product:
        await query.answer("❌ Error agregando producto", show_alert=True)
        return

    # Agregar al carrito
    context.user_data['cart'].append({
        'product_id': product_id,
        'nombre': product['nombre'],
        'precio': product['precio'],
        'cantidad': 1
    })

    logger.info(f"Producto {product_id} agregado al carrito")

    # Calcular total del carrito
    cart = context.user_data['cart']
    total_items = len(cart)
    total_price = sum(item['precio'] * item['cantidad'] for item in cart)

    # Obtener info de categoría para el botón de volver
    category_id = product.get('category_id', 1)
    cat_info = product.get('product_categories', {})
    cat_name = cat_info.get('name', 'Productos')
    cat_emoji = cat_info.get('icon_emoji', '📦')

    # Mensaje de confirmación mejorado
    await query.answer("✅ Producto agregado", show_alert=False)

    text = f"✅ **PRODUCTO AGREGADO AL CARRITO**\n\n"
    text += f"📦 {product['nombre']}\n"
    text += f"💰 ${product['precio']:,.0f}\n\n"
    text += f"─────────────────────\n\n"
    text += f"🛒 **Tu carrito:** {total_items} producto{'s' if total_items > 1 else ''}\n"
    text += f"💵 **Total:** ${total_price:,.0f}\n\n"
    text += "**¿Qué deseas hacer?**"

    # Botones con flujo claro
    keyboard = [
        [
            InlineKeyboardButton(
                f"🛒 Ver Carrito ({total_items})",
                callback_data="view_cart"
            )
        ],
        [
            InlineKeyboardButton(
                f"➕ Agregar Más de {cat_emoji} {cat_name}",
                callback_data=f"cat_{category_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📂 Ver Otras Categorías",
                callback_data="menu_hacer_pedido"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Confirmar Pedido Ahora",
                callback_data="confirm_order"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Menú Principal",
                callback_data="menu_volver"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el carrito de compras
    """
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get('cart', [])

    if not cart:
        text = "🛒 **TU CARRITO**\n\n"
        text += "Tu carrito está vacío.\n\n"
        text += "¡Agrega productos para continuar!"

        keyboard = [
            [InlineKeyboardButton("🛍️ Ver Productos", callback_data="menu_hacer_pedido")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
        ]
    else:
        text = "🛒 **TU CARRITO**\n\n"
        total = 0

        for idx, item in enumerate(cart, 1):
            nombre = item['nombre']
            precio = item['precio']
            cantidad = item['cantidad']
            subtotal = precio * cantidad

            text += f"**{idx}.** {nombre}\n"
            text += f"   ${precio:,.0f} x {cantidad} = **${subtotal:,.0f}**\n\n"
            total += subtotal

        text += f"─────────────────────\n"
        text += f"💰 **TOTAL: ${total:,.0f}**\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar Pedido",
                    callback_data="confirm_order"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Agregar Más Productos",
                    callback_data="menu_hacer_pedido"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Vaciar Carrito",
                    callback_data="clear_cart"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Menú Principal",
                    callback_data="menu_volver"
                )
            ]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vacía el carrito
    """
    query = update.callback_query
    await query.answer("🗑️ Carrito vaciado")

    context.user_data['cart'] = []
    await view_cart(update, context)


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Confirma y procesa el pedido guardándolo en Supabase
    """
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
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return

    user = update.effective_user
    supabase = get_supabase()

    try:
        # ============================================
        # 1. VERIFICAR/CREAR USUARIO
        # ============================================
        user_response = supabase.table("users")\
            .select("*")\
            .eq("telegram_id", user.id)\
            .execute()

        if user_response.data:
            # Usuario existe
            db_user = user_response.data[0]
            user_id = db_user['user_id']
            logger.info(f"✅ Usuario existente: {user_id}")
        else:
            # Crear nuevo usuario
            new_user = {
                'telegram_id': user.id,
                'nombre': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Usuario'
            }
            user_create = supabase.table("users").insert(new_user).execute()
            user_id = user_create.data[0]['user_id']
            logger.info(f"✅ Nuevo usuario creado: {user_id}")

        # ============================================
        # 2. CALCULAR TOTALES
        # ============================================
        subtotal = sum(item['precio'] * item['cantidad'] for item in cart)
        tax = subtotal * 0.0  # 0% de impuesto
        delivery_fee = 0  # Sin cargo de envío
        total = subtotal + tax + delivery_fee

        # ============================================
        # 3. CREAR ORDEN
        # ============================================
        order_data = {
            'user_id': user_id,
            'estado': 'pending',
            'subtotal': float(subtotal),
            'tax': float(tax),
            'delivery_fee': float(delivery_fee),
            'total': float(total),
            'is_paid': False,
            'notas': context.user_data.get('order_notes', None)
        }

        order_response = supabase.table("orders").insert(order_data).execute()
        order = order_response.data[0]
        order_id = order['order_id']
        logger.info(f"✅ Orden creada: {order_id} para user {user_id}")

        # ============================================
        # 4. CREAR ITEMS DE LA ORDEN
        # ============================================
        order_items = []
        for item in cart:
            order_item = {
                'order_id': order_id,
                'product_id': item['product_id'],
                'cantidad': item['cantidad'],
                'precio_unitario': float(item['precio']),
                'subtotal': float(item['precio'] * item['cantidad'])
            }
            order_items.append(order_item)

        # Insertar todos los items
        items_response = supabase.table("order_items")\
            .insert(order_items, default_to_null=False)\
            .execute()

        logger.info(f"✅ {len(order_items)} items agregados a orden {order_id}")

               # ============================================
        # 5. GENERAR PDF Y ENVIAR EMAIL AL ADMIN
        # ============================================
        try:
            # Preparar datos para el email con detalles de productos
            items_with_names = []
            for item in cart:
                items_with_names.append({
                    'product_name': item['nombre'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio'],
                    'subtotal': item['precio'] * item['cantidad']
                })
            
            email_data = {
                'order_id': order_id,
                'nombre_cliente': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Usuario',
                'total': total,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'items': items_with_names
            }
            
            # Generar PDF
            logger.info(f"📄 Generando PDF para orden #{order_id}...")
            pdf_path = PDFService.generate_order_pdf(email_data, items_with_names)
            
            if pdf_path:
                logger.info(f"✅ PDF generado: {pdf_path}")
            else:
                logger.warning(f"⚠️ No se pudo generar PDF para orden #{order_id}")
            
            # Enviar email con PDF adjunto
            email_result = EmailService.send_order_confirmation_to_admin(email_data)
            
            if email_result:
                logger.info(f"✅ Email enviado al admin para orden #{order_id}")
            else:
                logger.warning(f"⚠️ No se pudo enviar email para orden #{order_id}")
                
        except Exception as email_error:
            logger.error(f"⚠️ Error enviando email/PDF al admin: {email_error}")
            import traceback
            traceback.print_exc()
            # No detenemos el proceso si falla el email


        # ============================================
        # 6. MENSAJE DE CONFIRMACIÓN CON INFO COMPLETA
        # ============================================
        
        # Calcular anticipo (50%)
        anticipo = total * 0.5
        
        text = "✅ **PEDIDO CONFIRMADO**\n\n"
        text += f"📋 Orden #{order_id}\n"
        text += f"👤 {user.first_name}\n\n"
        text += "📦 **Resumen de tu pedido:**\n\n"

        for idx, item in enumerate(cart, 1):
            nombre = item['nombre']
            cantidad = item['cantidad']
            precio = item['precio']
            subtotal_item = precio * cantidad

            text += f"**{idx}.** {nombre} x{cantidad}\n"
            text += f"   ${precio:,.0f} → **${subtotal_item:,.0f}**\n\n"

        text += f"─────────────────────\n\n"
        text += f"💰 Subtotal: ${subtotal:,.0f}\n"
        
        if tax > 0:
            text += f"📊 Impuesto: ${tax:,.0f}\n"
        if delivery_fee > 0:
            text += f"🚚 Envío: ${delivery_fee:,.0f}\n"
            
        text += f"💵 **TOTAL: ${total:,.0f}**\n"
        text += f"💰 **Anticipo requerido (50%):** ${anticipo:,.0f}\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📍 **PUNTOS DE RECOGIDA:**\n"
        text += "Elige uno al contactarnos:\n"
        text += "• Calle 96b #20d–70\n"
        text += "• Cra 81b #19b–80\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "💳 **PAGO DEL ANTICIPO:**\n"
        text += "Métodos: Nequi / Daviplata\n"
        text += "📱 Número: 3014170313\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "⚠️ **IMPORTANTE:**\n"
        text += "1️⃣ Envía comprobante del anticipo (50%)\n"
        text += "2️⃣ Indica fecha y hora de recogida\n"
        text += "3️⃣ Confirma punto de recogida\n"
        text += "4️⃣ NO hacemos domicilios directos\n"
        text += "5️⃣ Pedidos grandes: 2 días de anticipación\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📞 Contacto: 3014170313\n"
        text += "Para seguimiento, cambios o consultas\n\n"
        
        text += f"🔢 **Número de orden:** {order_id}"

        # Limpiar carrito
        context.user_data['cart'] = []

        keyboard = [
            [
                InlineKeyboardButton(
                    "📦 Ver Mis Pedidos",
                    callback_data="menu_mis_pedidos"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛒 Hacer Otro Pedido",
                    callback_data="menu_hacer_pedido"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Menú Principal",
                    callback_data="menu_volver"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        logger.info(f"✅ Pedido {order_id} completado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error creando pedido: {e}")
        import traceback
        traceback.print_exc()

        keyboard = [
            [InlineKeyboardButton("🔄 Intentar de nuevo", callback_data="view_cart")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def smart_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Agrega producto al carrito con cantidad específica desde el chat inteligente
    Callback: smart_add_<product_id>_<quantity>
    """
    query = update.callback_query
    
    # Extraer datos: smart_add_123_5
    parts = query.data.split('_')
    product_id = int(parts[2])
    quantity = int(parts[3])

    # Inicializar carrito si no existe
    if 'cart' not in context.user_data:
        context.user_data['cart'] = []

    # Obtener info del producto
    from config.database import db
    product = db.get_product_by_id(product_id)
    
    if not product:
        await query.answer("❌ Error: Producto no encontrado", show_alert=True)
        return

    # Agregar al carrito
    context.user_data['cart'].append({
        'product_id': product_id,
        'nombre': product['nombre'],
        'precio': product['precio'],
        'cantidad': quantity
    })

    logger.info(f"Smart add: {quantity}x {product['nombre']} al carrito")

    # Calcular total del carrito
    cart = context.user_data['cart']
    total_items = len(cart)
    total_price = sum(item['precio'] * item['cantidad'] for item in cart)

    # Mensaje de confirmación
    await query.answer(f"✅ Agregado: {quantity}x {product['nombre']}", show_alert=False)

    text = f"✅ **PRODUCTO AGREGADO DESDE EL CHAT**\n\n"
    text += f"📦 {quantity}x {product['nombre']}\n"
    text += f"💰 ${product['precio'] * quantity:,.0f}\n\n"
    text += f"─────────────────────\n"
    text += f"🛒 **Tu carrito:** {total_items} items | ${total_price:,.0f}\n\n"
    text += "¿Qué deseas hacer?"

    # Botones de acción con cantidades B2B
    keyboard = [
        [
            InlineKeyboardButton("🛒 +1", callback_data=f"smart_add_{product_id}_1"),
            InlineKeyboardButton("🛒 +6", callback_data=f"smart_add_{product_id}_6"),
            InlineKeyboardButton("🛒 +12", callback_data=f"smart_add_{product_id}_12"),
        ],
        [InlineKeyboardButton("🛒 Ver Carrito", callback_data="view_cart")],
        [InlineKeyboardButton("🔙 Volver a Productos", callback_data=f"cat_{product['category_id']}")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_volver")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if query.message.content_type == 'photo':
             await query.message.delete()
             await query.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
             await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error editando mensaje producto: {e}")
        # Fallback por si acaso
        await query.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
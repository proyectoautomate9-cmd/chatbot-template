"""
Chat libre con IA + guía al catálogo (categorías y productos)

Requisitos:
- start_chat_libre debe setear: context.user_data["chat_mode"] = "free"  [file:55]
- show_main_menu debería poner chat_mode = None (recomendado)            [file:55]
- Productos/categorías usan callbacks: cat_{id} y prod_{id}             [file:56]
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.database import get_supabase
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

# Instancia única
ai_service = AIService()


# =========================
# Handler principal
# =========================
async def handle_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = (update.message.text or "").strip()

    logger.info(f"💬 Mensaje de {user.first_name} ({user.id}): {user_message}")

    await update.message.chat.send_action("typing")

    # No interferir si no está en modo chat libre
    if context.user_data.get("chat_mode") != "free":
        return

    intent = detect_intent(user_message)

    if intent == "horarios":
        await handle_horarios(update)
        return

    if intent == "contacto":
        await handle_contacto(update)
        return

    if intent == "pedidos":
        await handle_pedidos(update, user.id)
        return

    if intent == "compra":
        await handle_compra(update, context, user_message)
        return

    await handle_general_query(update, context, user.id, user_message)


# =========================
# Intent detection
# =========================
def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(w in msg for w in ["horario", "horarios", "hora", "abierto", "abren", "cierran", "cierra", "atienden"]):
        return "horarios"

    if any(w in msg for w in ["whatsapp", "contacto", "telefono", "teléfono", "llamar", "correo", "email", "3014170313"]):
        return "contacto"

    if any(w in msg for w in ["pedido", "pedidos", "orden", "órden", "estado", "seguimiento", "cuantos", "cuántos", "mis pedidos"]):
        return "pedidos"

    # Todo lo relacionado con catálogo/compra
    if any(w in msg for w in [
        "menu", "menú", "catalogo", "catálogo",
        "quiero", "comprar", "pedir", "precio", "cuesta", "vale",
        "recomienda", "recomiendas", "sugiere", "opciones",
        # keywords de categorías/productos (según tu lista)
        "torta", "tortas", "cheese", "cheesecake", "brownie", "ponqué", "ponques",
        "postre", "postres", "liberal", "repollas",
        "hojaldre", "hojaldres", "pastel", "pasabocas", "corazones", "milhoja", "milhojas",
        "galleta", "galletas", "galleteria", "galletería", "coco", "chocolate",
        "masato", "almojabana", "almojábana", "arepa", "arepas", "merengue", "merengues",
        "yoyos",
    ]):
        return "compra"

    return "general"


# =========================
# Respuestas rápidas
# =========================
async def handle_horarios(update: Update):
    text = (
        "⏰ **HORARIOS MILHOJA DRES**\n\n"
        "🕐 **Lunes a Viernes:** 8:00 AM - 6:00 PM\n"
        "🕐 **Sábados:** 9:00 AM - 5:00 PM\n"
        "🕐 **Domingos:** Cerrado\n\n"
        "📍 **Puntos de recogida:**\n"
        "• Calle 96b #20d–70\n"
        "• Cra 81b #19b–80"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
    ]
    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_contacto(update: Update):
    text = (
        "📞 **CONTACTO - MILHOJA DRES**\n\n"
        "💬 **WhatsApp:** 3014170313\n"
        "📧 **Email:** info@milhojaldres.com\n"
        "📍 **Instagram:** @milhojaldres\n\n"
        "Escríbenos y te ayudamos 😊"
    )
    keyboard = [
        [InlineKeyboardButton("ℹ️ Información", callback_data="menu_informacion")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
    ]
    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_pedidos(update: Update, telegram_id: int):
    try:
        supabase = get_supabase()

        user_resp = supabase.table("users").select("user_id").eq("telegram_id", telegram_id).execute()
        if not user_resp.data:
            text = "No te encuentro registrado aún. Usa /start y prueba de nuevo."
            keyboard = [[InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")]]
            await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        user_id = user_resp.data[0]["user_id"]

        orders_resp = (
            supabase.table("orders")
            .select("order_id, estado")
            .eq("user_id", user_id)
            .in_("estado", ["pending", "confirmed", "preparing", "ready"])
            .execute()
        )
        active_count = len(orders_resp.data) if orders_resp.data else 0

        if active_count == 0:
            text = "📦 No tienes pedidos en proceso.\n\n¿Quieres hacer uno?"
        else:
            text = f"📦 Tienes **{active_count}** pedido(s) en proceso.\n\nToca **Mis Pedidos** para verlos."

        keyboard = [
            [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
            [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
            [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
        ]
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error consultando pedidos: {e}")
        text = "No pude consultar tus pedidos ahora. Toca **Mis Pedidos** para verlos."
        keyboard = [
            [InlineKeyboardButton("📦 Mis Pedidos", callback_data="menu_mis_pedidos")],
            [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
        ]
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# =========================
# Compra / Catálogo
# =========================
def category_keyword_map():
    """
    Mapa de keywords -> patrón para buscar en product_categories.name.
    Ajusta los valores (needle) según cómo se llamen tus categorías en Supabase.
    """
    return {
        # Categorías principales del menú (según tu lista)
        "torta": "torta",
        "tortas": "torta",
        "ponque": "ponqu",         # cubre ponqué/ponques
        "ponqué": "ponqu",
        "ponques": "ponqu",
        "ponqués": "ponqu",
        "postre": "postre",
        "postres": "postre",
        "hojaldre": "hojaldre",
        "hojaldres": "hojaldre",
        "galleteria": "gallet",
        "galletería": "gallet",
        "galleta": "gallet",
        "galletas": "gallet",
        "otros": "otros",

        # Productos que suelen vivir dentro de categorías
        "milhoja": "milhoja",
        "milhojas": "milhoja",
        "pastel": "pastel",
        "pasabocas": "pasaboca",
        "corazones": "corazon",
        "brownie": "brownie",
        "cheesecake": "cheese",
        "cheese": "cheese",
        "masato": "masato",
        "almojabana": "almojab",
        "almojábana": "almojab",
        "arepa": "arepa",
        "arepas": "arepa",
        "merengue": "mereng",
        "merengues": "mereng",
        "yoyos": "yoyos",
        "repollas": "repoll",
        "liberal": "liberal",
    }


def find_best_category_id(supabase, user_message: str):
    """
    Busca la mejor categoría:
    1) Intenta matchear por keyword->needle con ilike sobre product_categories.name.
    2) Si no encuentra, retorna None.
    """
    msg = user_message.lower()
    mapping = category_keyword_map()

    matched_needle = None
    for k, needle in mapping.items():
        if k in msg:
            matched_needle = needle
            break

    if not matched_needle:
        return None

    try:
        resp = (
            supabase.table("product_categories")
            .select("category_id, name, icon_emoji")
            .eq("is_active", True)
            .ilike("name", f"%{matched_needle}%")
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
        return None
    except Exception:
        # Si ilike no existe en tu SDK, fallback: traer categorías y filtrar en python
        cats = (
            supabase.table("product_categories")
            .select("category_id, name, icon_emoji")
            .eq("is_active", True)
            .order("display_order")
            .execute()
        )
        for c in (cats.data or []):
            if matched_needle in (c.get("name", "").lower()):
                return c
        return None


async def handle_compra(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    supabase = get_supabase()

    # 1) Si menciona algo que se asocia a una categoría -> ir directo
    cat = find_best_category_id(supabase, user_message)
    if cat:
        cat_id = cat["category_id"]
        emoji = cat.get("icon_emoji", "📦")
        cat_name = cat.get("name", "Productos")

        text = (
            f"{emoji} **¡Listo! Te llevo al catálogo de {cat_name}.**\n\n"
            "Toca el botón para ver opciones 👇"
        )
        keyboard = [
            [InlineKeyboardButton(f"{emoji} Ver {cat_name}", callback_data=f"cat_{cat_id}")],
            [InlineKeyboardButton("🛒 Ver categorías", callback_data="menu_hacer_pedido")],
            [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
        ]
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # 2) Si no detecta categoría: mostrar categorías top + IA
    categories_response = (
        supabase.table("product_categories")
        .select("category_id, name, icon_emoji")
        .eq("is_active", True)
        .order("display_order")
        .limit(5)
        .execute()
    )
    categories = categories_response.data if categories_response.data else []

    keyboard = []
    if categories:
        for c in categories[:5]:
            emoji = c.get("icon_emoji", "📦")
            keyboard.append([InlineKeyboardButton(f"{emoji} {c['name']}", callback_data=f"cat_{c['category_id']}")])

    ai_response = ai_service.get_response(
        query=user_message,
        user_id=update.effective_user.id,
        chat_history=context.user_data.get("chat_history", []),
    )
    ai_text = ai_response.get("respuesta", "")

    text = (
        f"{ai_text}\n\n"
        "Si quieres, también puedo llevarte directo a una categoría:\n"
        "Ej: *tortas*, *hojaldres*, *galletas*, *ponqués y postres*, *masato*."
    )

    keyboard.append([InlineKeyboardButton("🛒 Ver categorías", callback_data="menu_hacer_pedido")])
    keyboard.append([InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")])

    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # Guardar historial
    if "chat_history" not in context.user_data:
        context.user_data["chat_history"] = []
    context.user_data["chat_history"].append({"role": "user", "content": user_message})
    context.user_data["chat_history"].append({"role": "assistant", "content": ai_text})
    if len(context.user_data["chat_history"]) > 10:
        context.user_data["chat_history"] = context.user_data["chat_history"][-10:]


# =========================
# General query (IA)
# =========================
async def handle_general_query(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, user_message: str):
    ai_response = ai_service.get_response(
        query=user_message,
        user_id=telegram_id,
        chat_history=context.user_data.get("chat_history", []),
    )

    response_text = ai_response.get("respuesta", "")
    confianza = ai_response.get("confianza", 0.5)

    if confianza < 0.5:
        response_text += "\n\n💬 Si quieres, escríbenos a WhatsApp **3014170313**."

    keyboard = [
        [InlineKeyboardButton("🛒 Hacer un Pedido", callback_data="menu_hacer_pedido")],
        [InlineKeyboardButton("📞 Contacto", callback_data="menu_contacto")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu_volver")],
    ]
    await update.message.reply_text(text=response_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # Historial
    if "chat_history" not in context.user_data:
        context.user_data["chat_history"] = []
    context.user_data["chat_history"].append({"role": "user", "content": user_message})
    context.user_data["chat_history"].append({"role": "assistant", "content": response_text})
    if len(context.user_data["chat_history"]) > 10:
        context.user_data["chat_history"] = context.user_data["chat_history"][-10:]

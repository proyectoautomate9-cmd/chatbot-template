"""
Script para importar categorías y productos a Supabase.
SIN columna 'presentacion' (solo nombre + precio)
"""

from config.database import get_supabase
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =========================
# DATOS: Categorías
# =========================
CATEGORIES = [
    {"name": "Tortas", "emoji": "🎂", "order": 1},
    {"name": "Ponqués y Postres", "emoji": "🍰", "order": 2},
    {"name": "Hojaldres", "emoji": "🥐", "order": 3},
    {"name": "Galletería", "emoji": "🍪", "order": 4},
    {"name": "Otros", "emoji": "🥤", "order": 5},
]

# =========================
# DATOS: Productos (SIN presentacion)
# =========================
PRODUCTS = [
    # ===== TORTAS =====
    {"categoria": "Tortas", "nombre": "Cheese Cake", "precio": 22000},
    {"categoria": "Tortas", "nombre": "Cheese Cake Empaque Individual", "precio": 22000},
    {"categoria": "Tortas", "nombre": "Cheese Cake Decorado", "precio": 27000},
    {"categoria": "Tortas", "nombre": "Torta de Vainilla y Chocolate (Grande)", "precio": 20000},
    {"categoria": "Tortas", "nombre": "Torta de Vainilla y Chocolate (Pequeña)", "precio": 16000},
    {"categoria": "Tortas", "nombre": "Torta de Queso", "precio": 16000},
    {"categoria": "Tortas", "nombre": "Mantecada (Grande)", "precio": 23000},
    {"categoria": "Tortas", "nombre": "Mantecada (Pequeña)", "precio": 16000},
    {"categoria": "Tortas", "nombre": "Mantecada Empacada", "precio": 19000},
    {"categoria": "Tortas", "nombre": "Lonchero", "precio": 21000},
    {"categoria": "Tortas", "nombre": "Torta Decorada", "precio": 26000},
    {"categoria": "Tortas", "nombre": "Torta Brownie", "precio": 26000},

    # ===== PONQUÉS Y POSTRES =====
    {"categoria": "Ponqués y Postres", "nombre": "Brownie Cuadrado (Grande)", "precio": 28000},
    {"categoria": "Ponqués y Postres", "nombre": "Brownie Cuadrado (Pequeña)", "precio": 16000},
    {"categoria": "Ponqués y Postres", "nombre": "Liberal (Grande)", "precio": 23500},
    {"categoria": "Ponqués y Postres", "nombre": "Liberal (Pequeño)", "precio": 20000},
    {"categoria": "Ponqués y Postres", "nombre": "Repollas (Grande)", "precio": 18000},
    {"categoria": "Ponqués y Postres", "nombre": "Repollas (Domo)", "precio": 15000},
    {"categoria": "Ponqués y Postres", "nombre": "Repollas (Pequeña)", "precio": 12000},

    # ===== HOJALDRES =====
    {"categoria": "Hojaldres", "nombre": "Pastel de Pollo", "precio": 22000},
    {"categoria": "Hojaldres", "nombre": "Pastel de Carne", "precio": 22000},
    {"categoria": "Hojaldres", "nombre": "Pastel Hawaiano", "precio": 22000},
    {"categoria": "Hojaldres", "nombre": "Pastel Gloria", "precio": 22000},
    {"categoria": "Hojaldres", "nombre": "Pasabocas (Grande x25)", "precio": 15000},
    {"categoria": "Hojaldres", "nombre": "Pasabocas (Grande x13)", "precio": 9000},
    {"categoria": "Hojaldres", "nombre": "Pasabocas (Mini)", "precio": 15000},
    {"categoria": "Hojaldres", "nombre": "Corazones (Grande x30)", "precio": 15000},
    {"categoria": "Hojaldres", "nombre": "Corazones (Grande x15)", "precio": 9000},
    {"categoria": "Hojaldres", "nombre": "Corazones (Mini)", "precio": 15000},
    {"categoria": "Hojaldres", "nombre": "Choco Corazones", "precio": 15000},
    {"categoria": "Hojaldres", "nombre": "Milhoja", "precio": 15000},

    # ===== GALLETERÍA =====
    {"categoria": "Galletería", "nombre": "Galleta", "precio": 16000},
    {"categoria": "Galletería", "nombre": "Galleta con Chocolate", "precio": 11000},
    {"categoria": "Galletería", "nombre": "Galleta de Coco", "precio": 16000},

    # ===== OTROS =====
    {"categoria": "Otros", "nombre": "Masato", "precio": 24000},
    {"categoria": "Otros", "nombre": "Almojábanas o Arepas", "precio": 19000},
    {"categoria": "Otros", "nombre": "Merengues", "precio": 18000},
    {"categoria": "Otros", "nombre": "Yoyos (Bolsa)", "precio": 14000},
    {"categoria": "Otros", "nombre": "Yoyos (Domo)", "precio": 20000},
]


def import_categories():
    """Inserta/actualiza categorías."""
    supabase = get_supabase()
    logger.info("\n🔄 Procesando categorías...")
    cat_map = {}

    for cat in CATEGORIES:
        cat_name = cat["name"]
        emoji = cat["emoji"]
        order = cat["order"]

        existing = (
            supabase.table("product_categories")
            .select("category_id")
            .eq("name", cat_name)
            .execute()
        )

        if existing.data:
            cat_id = existing.data[0]["category_id"]
            supabase.table("product_categories").update(
                {"icon_emoji": emoji, "display_order": order, "is_active": True}
            ).eq("category_id", cat_id).execute()
            logger.info(f"  ✏️  '{cat_name}' (id={cat_id}) - Actualizado")
        else:
            resp = supabase.table("product_categories").insert(
                {"name": cat_name, "icon_emoji": emoji, "display_order": order, "is_active": True}
            ).execute()
            cat_id = resp.data[0]["category_id"]
            logger.info(f"  ✅ '{cat_name}' (id={cat_id}) - Creado")

        cat_map[cat_name] = cat_id

    return cat_map


def import_products(cat_map: dict):
    """Inserta/actualiza productos SIN presentacion."""
    supabase = get_supabase()
    logger.info("\n🔄 Procesando productos...")
    created_count = 0
    updated_count = 0

    for prod in PRODUCTS:
        categoria = prod["categoria"]
        nombre = prod["nombre"]
        precio = prod["precio"]

        category_id = cat_map.get(categoria)
        if not category_id:
            logger.warning(f"  ⚠️  '{nombre}' - Categoría '{categoria}' no encontrada")
            continue

        existing = (
            supabase.table("products")
            .select("product_id")
            .eq("nombre", nombre)
            .eq("category_id", category_id)
            .execute()
        )

        if existing.data:
            prod_id = existing.data[0]["product_id"]
            supabase.table("products").update({
                "precio": precio,
                "activo": True,
            }).eq("product_id", prod_id).execute()
            logger.info(f"  ✏️  '{nombre}' (id={prod_id}) - ${precio:,.0f}")
            updated_count += 1
        else:
            resp = supabase.table("products").insert({
                "nombre": nombre,
                "category_id": category_id,
                "precio": precio,
                "activo": True,
            }).execute()
            prod_id = resp.data[0]["product_id"]
            logger.info(f"  ✅ '{nombre}' (id={prod_id}) - ${precio:,.0f}")
            created_count += 1

    logger.info(f"\n📊 Resumen productos:")
    logger.info(f"   ✅ Creados: {created_count}")
    logger.info(f"   ✏️  Actualizados: {updated_count}")


def main():
    logger.info("=" * 60)
    logger.info("🍰 IMPORTACIÓN MILHOJA DRES - Categorías y Productos")
    logger.info("=" * 60)

    try:
        cat_map = import_categories()
        import_products(cat_map)
        logger.info("\n" + "=" * 60)
        logger.info("✅ ¡Importación completada exitosamente!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

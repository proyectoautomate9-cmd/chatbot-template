"""
Servicio de base de datos para Supabase
"""
import os
from supabase import create_client, Client
from typing import Optional, Dict, List
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================
# CLIENTE SINGLETON (para uso directo)
# ============================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Preferir Service Key para backend/admin (bypasses RLS)
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ SUPABASE_URL y SUPABASE_KEY (o SUPABASE_SERVICE_KEY) deben estar en .env"
    )

# Cliente global
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase() -> Client:
    """
    Retorna instancia del cliente de Supabase
    
    Returns:
        Client: Cliente de Supabase configurado
    """
    return supabase


# ============================================
# CLASE DatabaseService (tu código original)
# ============================================

class DatabaseService:
    """Maneja todas las operaciones con Supabase"""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar en .env")

        self.client: Client = create_client(url, key)
        logger.info("✅ DatabaseService inicializado")

    # === USUARIOS ===

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Obtiene usuario por telegram_id"""
        try:
            response = self.client.table("users").select("*").eq("telegram_id", telegram_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None

    def create_user(self, telegram_id: int, nombre: str, telefono: str = None, direccion: str = None) -> Dict:
        """Crea nuevo usuario"""
        try:
            data = {
                "telegram_id": telegram_id,
                "nombre": nombre,
                "telefono": telefono,
                "direccion": direccion
            }
            response = self.client.table("users").insert(data).execute()
            logger.info(f"✅ Usuario creado: {nombre}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return None

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Actualiza datos del usuario"""
        try:
            self.client.table("users").update(kwargs).eq("user_id", user_id).execute()
            logger.info(f"✅ Usuario {user_id} actualizado")
            return True
        except Exception as e:
            logger.error(f"Error actualizando usuario: {e}")
            return False

    # === ÓRDENES ===

    def create_order(self, user_id: int, productos: List[Dict], total: float, notas: str = None) -> Dict:
        """Crea nueva orden"""
        try:
            data = {
                "user_id": user_id,
                "productos": productos,
                "total": total,
                "notas": notas
            }
            response = self.client.table("orders").insert(data).execute()
            logger.info(f"✅ Orden creada para user_id {user_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creando orden: {e}")
            return None

    def get_user_orders(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Obtiene últimas órdenes del usuario"""
        try:
            response = (
                self.client.table("orders")
                .select("*")
                .eq("user_id", user_id)
                .order("fecha_orden", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo órdenes: {e}")
            return []

    # === PREFERENCIAS ===

    def get_preferences(self, user_id: int) -> Optional[Dict]:
        """Obtiene preferencias del usuario"""
        try:
            response = self.client.table("preferences").select("*").eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error obteniendo preferencias: {e}")
            return None

    def update_preferences(self, user_id: int, **kwargs) -> bool:
        """Actualiza preferencias del usuario"""
        try:
            # Intentar actualizar primero
            result = self.client.table("preferences").update(kwargs).eq("user_id", user_id).execute()

            # Si no existe, crear
            if not result.data:
                kwargs["user_id"] = user_id
                self.client.table("preferences").insert(kwargs).execute()

            logger.info(f"✅ Preferencias actualizadas para user_id {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando preferencias: {e}")
            return False




    # === PRODUCTOS ===

    def get_all_products(self) -> List[Dict]:
        """Obtiene todos los productos activos de la base de datos"""
        try:
            # Mapeamos las columnas nuevas a las que espera el bot
            # Nota: 'activo' es la columna correcta no 'is_active'
            response = (
                self.client.table("products")
                .select("*, category_id") # Select * es más seguro para traer todo
                .eq("is_available", True) # User script added this
                .order("categoria")
                .execute()
            )
            
            # Post-procesamiento para compatibilidad
            products = []
            for p in response.data:
                p['disponible'] = p.get('is_available', True)
                p['activo'] = p.get('activo', True) # La columna se llama activo
                products.append(p)
                
            logger.info(f"✅ {len(products)} productos recuperados de DB")
            return products
        except Exception as e:
            logger.error(f"Error obteniendo productos: {e}")
            return self._get_mock_products()
            
    def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Obtiene productos por categoría con fallback"""
        try:
            response = self.client.table("products")\
                .select("*")\
                .eq("category_id", category_id)\
                .eq("activo", True)\
                .order("nombre")\
                .execute()
                
            # Compatibilidad
            products = []
            for p in response.data:
                p['disponible'] = p.get('is_available', True)
                p['activo'] = p.get('activo', True)
                products.append(p)
                
            return products
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            # Mock fallback logic
            mocks = self._get_mock_products()
            return [p for p in mocks if p.get('category_id', 1) == category_id]
            
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Obtiene detalle de producto por ID con fallback"""
        try:
            response = self.client.table("products")\
                .select("*, product_categories(name, icon_emoji)")\
                .eq("product_id", product_id)\
                .single()\
                .execute()
                
            p = response.data
            if p:
                p['disponible'] = p.get('is_available', True)
                p['activo'] = p.get('activo', True)
            return p
            
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            mocks = self._get_mock_products()
            filtered = [p for p in mocks if p['product_id'] == product_id]
            return filtered[0] if filtered else None

    def get_category(self, category_id: int) -> Optional[Dict]:
        """Obtiene categoría por ID con fallback"""
        try:
            response = self.client.table("product_categories")\
                .select("*")\
                .eq("category_id", category_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting category {category_id}: {e}")
            # Mock categories
            if category_id == 1:
                return {'category_id': 1, 'name': 'Milhojas', 'icon_emoji': '🍰'}
            elif category_id == 2:
                return {'category_id': 2, 'name': 'Bebidas', 'icon_emoji': '☕'}
            return {'category_id': category_id, 'name': 'General', 'icon_emoji': '📦'}

    def _get_mock_products(self) -> List[Dict]:
        """Retorna productos fake para pruebas cuando falla la BD"""
        logger.warning("⚠️ Usando productos MOCK (Base de datos falló)")
        return [
            {
                "product_id": 1, 
                "nombre": "Milhoja Tradicional (Demo)", 
                "precio": 5000, 
                "descripcion": "Deliciosa milhoja con arequipe casero (Datos de prueba).",
                "categoria": "Milhojas", 
                "category_id": 1,
                "activo": True,
                "disponible": True,
                "product_categories": {'name': 'Milhojas', 'icon_emoji': '🍰'}
            },
            {
                "product_id": 2, 
                "nombre": "Milhoja Chantilly (Demo)", 
                "precio": 6000, 
                "descripcion": "Milhoja con suave crema chantilly (Datos de prueba).",
                "categoria": "Milhojas", 
                "category_id": 1,
                "activo": True,
                "disponible": True,
                "product_categories": {'name': 'Milhojas', 'icon_emoji': '🍰'}
            },
            {
                "product_id": 3, 
                "nombre": "Café Americano (Demo)", 
                "precio": 3500, 
                "descripcion": "Café recién molido (Datos de prueba).",
                "categoria": "Bebidas", 
                "category_id": 2,
                "activo": True,
                "disponible": True,
                "product_categories": {'name': 'Bebidas', 'icon_emoji': '☕'}
            }
        ]

# ============================================
# INSTANCIA GLOBAL (opcional)
# ============================================
db = DatabaseService()


# ============================================
# TEST AL EJECUTAR DIRECTAMENTE
# ============================================
if __name__ == "__main__":
    try:
        print("🧪 Probando conexión a Supabase...")
        print()
        
        # Test con cliente directo
        response = supabase.table("product_categories").select("*").execute()
        
        if response.data:
            print("✅ Conexión exitosa con get_supabase()")
            print(f"✅ {len(response.data)} categorías encontradas:")
            for cat in response.data:
                emoji = cat.get('icon_emoji', '📦')
                name = cat.get('name', 'Sin nombre')
                print(f"   {emoji} {name}")
        else:
            print("⚠️ Conexión OK pero no hay categorías")
        
        print()
        
        # Test con DatabaseService
        print("✅ DatabaseService inicializado correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

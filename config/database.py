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
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ SUPABASE_URL y SUPABASE_KEY deben estar en .env"
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

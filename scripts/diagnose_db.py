import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_supabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose():
    db = get_supabase()
    print(" Diagnosticando conexion a Supabase...")
    
    # Intenta listar todas las tablas visibles (truco usando una tabla que sabemos que existe)
    # O simplemente probando acceso
    
    tables_to_check = ["products", "users", "orders", "product_categories"]
    
    for table in tables_to_check:
        print(f"\n Verificando tabla: '{table}'...")
        try:
            # Try to fetch just 1 row
            response = db.table(table).select("*").limit(1).execute()
            print(f"    Acceso OK. Registros encontrados: {len(response.data)}")
            if response.data:
                item = response.data[0]
                print(f"    Schema (Columnas): {list(item.keys())}")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    diagnose()

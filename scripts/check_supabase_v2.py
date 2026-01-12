
import os
import time
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables desde .env directamente
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

def check_tables():
    if not url or not key:
        print("❌ No se encontraron SUPABASE_URL o SUPABASE_KEY en el .env")
        return

    supabase = create_client(url, key)
    tables = ['users', 'products', 'orders', 'discounts', 'admin_users']
    
    print("--- Diagnóstico de Conexión y Tablas ---")
    for table in tables:
        start = time.time()
        try:
            # Intentar una consulta mínima
            res = supabase.table(table).select("*", count="exact").limit(1).execute()
            end = time.time()
            print(f"✅ '{table}': Existe. ({res.count} filas) - Latencia: {end-start:.2f}s")
        except Exception as e:
            end = time.time()
            if "PGRST204" in str(e) or "PGRST205" in str(e):
                print(f"❌ '{table}': NO EXISTE. - Latencia: {end-start:.2f}s")
            else:
                print(f"⚠️ '{table}': Error inesperado ({type(e).__name__}). - Latencia: {end-start:.2f}s")
                # print(f"   Detalle: {str(e)}")

if __name__ == "__main__":
    check_tables()

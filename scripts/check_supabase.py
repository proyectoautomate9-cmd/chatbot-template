
from config.database import get_supabase
import time

def check_tables():
    supabase = get_supabase()
    tables = ['users', 'products', 'orders', 'discounts', 'admin_users']
    
    print("--- Diagnóstico de Tablas ---")
    for table in tables:
        start = time.time()
        try:
            res = supabase.table(table).select("*", count="exact").limit(1).execute()
            end = time.time()
            print(f"✅ Tabla '{table}': Existe. ({res.count} filas) - Latencia: {end-start:.2f}s")
        except Exception as e:
            end = time.time()
            print(f"❌ Tabla '{table}': ERROR/No existe. - Latencia: {end-start:.2f}s")
            # print(f"   Detalle: {str(e)}")

if __name__ == "__main__":
    check_tables()

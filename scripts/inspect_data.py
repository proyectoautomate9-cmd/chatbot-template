import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_supabase
import json

def inspect():
    db = get_supabase()
    
    print("🔍 INSPECCIÓN DE DATOS")
    print("=======================")
    
    # 1. Inspect Categories
    print("\n📦 CATEGORÍAS (product_categories):")
    try:
        cats = db.table("product_categories").select("*").execute()
        print(json.dumps(cats.data, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. Inspect Products
    print("\n🍔 PRODUCTOS (products):")
    try:
        prods = db.table("products").select("*").execute()
        print(json.dumps(prods.data, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect()

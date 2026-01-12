import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock database before importing handlers
import config.database
config.database.db = MagicMock()
config.database.db.get_product_by_id = MagicMock(return_value={
    'product_id': 62,
    'nombre': 'Milhoja',
    'precio': 15000,
    'activo': True
})

from app.handlers.products import smart_add_to_cart

async def test_smart_add():
    print("🧪 PROBANDO SMART ADD")
    
    # Mock Update and Context
    update = MagicMock()
    update.callback_query.data = "smart_add_62_17"
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {} # Simula sesión vacía
    
    # Ejecutar handler
    try:
        await smart_add_to_cart(update, context)
        
        # Verificar resultados
        print("\n📊 RESULTADOS:")
        
        # 1. Verificar Carrito
        cart = context.user_data.get('cart', [])
        print(f"   Carrito items: {len(cart)}")
        if len(cart) == 1:
            item = cart[0]
            print(f"   Item: {item['nombre']} x{item['cantidad']}")
            if item['cantidad'] == 17 and item['product_id'] == 62:
                print("   ✅ DATOS CORRECTOS")
            else:
                print("   ❌ DATOS ERRONEOS")
        else:
            print("   ❌ CARRITO VACIO")
            
        # 2. Verificar Respuesta Visual
        if update.callback_query.message.reply_text.called:
            print("   ✅ Mensaje de confirmación enviado")
        else:
            print("   ❌ Mensaje de confirmación NO enviado")
            
    except Exception as e:
        print(f"   ❌ EXCEPCION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_smart_add())

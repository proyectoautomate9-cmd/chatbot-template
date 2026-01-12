import os
import sys
from dotenv import load_dotenv

def check_environment():
    """
    Verifica que las variables de entorno críticas estén configuradas.
    """
    load_dotenv()
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    missing = []
    
    print("🔍 Verificando configuración del entorno...")
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing.append(var)
        else:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"✅ {var} configurado ({masked})")
            
    if missing:
        print("\n❌ ERRORES DE CONFIGURACIÓN DETECTADOS:")
        print("Faltan las siguientes variables en tu archivo .env:")
        for var in missing:
            print(f"   - {var}")
        print("\nPor favor edita el archivo .env y agrega los valores correspondientes.")
        return False
        
    print("\n✅ Todo parece correcto. Iniciando el sistema...")
    return True

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)
    sys.exit(0)

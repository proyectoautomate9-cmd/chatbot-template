"""
Aplicación FastAPI principal con bot de Telegram corriendo en background
Para desarrollo local con polling, usa: python -m app.polling_bot
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Milhojaldres Bot",
    description="Chatbot multicanal con Telegram, Supabase y OpenAI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# RUTAS DE SALUD
# ============================================================================

@app.get("/health")
async def health_check():
    """Verificar que la API está activa"""
    logger.info("Health check solicitado")
    return {
        "status": "healthy",
        "service": "milhojaldres-bot",
        "mode": "web_service_with_background_bot"
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Milhojaldres Bot API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "telegram_webhook": "/telegram/webhook"
        }
    }

# ============================================================================
# RUTAS DE TELEGRAM (WEBHOOK)
# ============================================================================

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook para recibir actualizaciones de Telegram (uso futuro)
    Por ahora el bot usa polling en background
    """
    try:
        json_data = await request.json()
        logger.info(f"📨 Webhook recibido: {json_data}")
        return {"ok": True, "message": "Webhook procesado"}
    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}")
        return {"ok": False, "error": str(e)}

# ============================================================================
# EVENTOS DE CICLO DE VIDA
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicia FastAPI y el bot en background"""
    logger.info("✅ FastAPI iniciando...")
    
    # Iniciar bot en background thread
    try:
        from app.background_bot import start_bot_background
        start_bot_background()
        logger.info("✅ Bot de Telegram iniciado en background")
    except Exception as e:
        logger.error(f"❌ Error iniciando bot: {e}")
    
    logger.info("🌐 Milhojaldres Bot listo para recibir tráfico")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Milhojaldres Bot detenido")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

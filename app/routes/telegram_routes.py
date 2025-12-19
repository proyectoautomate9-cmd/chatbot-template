from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import json
from datetime import datetime
import httpx
from openai import AsyncOpenAI


router = APIRouter(prefix="/webhook", tags=["telegram"])

# Cliente de OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_token():
    return os.getenv("TELEGRAM_TOKEN")


async def get_ai_response(user_message: str, user_name: str) -> str:
    """Obtiene respuesta inteligente de OpenAI"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": f"Eres un asistente de ventas amigable de Milhojaldres, una pastelería. Responde de forma breve y útil. El usuario se llama {user_name}."
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error con OpenAI: {e}")
        return f"¡Hola {user_name}! 👋 Estoy teniendo problemas técnicos, pero estoy aquí para ayudarte con Milhojaldres 🍰"


async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje a Telegram usando sendMessage"""
    token = get_token()
    if not token:
        print("❌ No hay token configurado")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text
            })
            
            if response.status_code == 200:
                print(f"✅ Mensaje enviado a chat {chat_id}")
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Excepción enviando mensaje: {e}")
        return False


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Webhook para recibir updates de Telegram"""
    try:
        update = await request.json()

        timestamp = datetime.now().isoformat()
        print(f"\n[{timestamp}] 📨 Update recibido desde Telegram:")
        print(json.dumps(update, indent=2, ensure_ascii=False))

        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            user_first_name = message["from"].get("first_name", "Usuario")
            text = message.get("text", "")

            print(f"\n✅ Mensaje procesado:")
            print(f"   Chat ID: {chat_id}")
            print(f"   User ID: {user_id}")
            print(f"   Nombre: {user_first_name}")
            print(f"   Texto: {text}")

            # Obtener respuesta de IA
            print(f"🤖 Consultando OpenAI...")
            ai_response = await get_ai_response(text, user_first_name)
            print(f"💡 Respuesta IA: {ai_response}")
            
            # Enviar respuesta
            await send_telegram_message(chat_id, ai_response)

            return JSONResponse({"ok": True, "received": True})

        if "update_id" in update:
            print(f"✅ Update ID {update['update_id']} procesado sin mensaje")
            return JSONResponse({"ok": True})

        return JSONResponse({"ok": True})

    except Exception as e:
        timestamp = datetime.now().isoformat()
        print(f"\n[{timestamp}] ❌ Error en webhook: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"ok": False, "error": str(e)},
            status_code=400
        )


@router.get("/telegram/info")
async def telegram_info():
    """Info del bot para verificar configuración"""
    
    token = get_token()
    token_masked = f"{token[:10]}...{token[-4:]}" if token else "NO CONFIGURADO"
    
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_configured = bool(openai_key and not openai_key.startswith("sk-proj-placeholder"))
    
    return {
        "bot_name": "Milhojaldres Bot",
        "token": token_masked,
        "telegram_status": "✅ Configurado" if token else "❌ No configurado",
        "openai_status": "✅ Configurado" if openai_configured else "❌ No configurado",
        "webhook_url": "/webhook/telegram"
    }


@router.get("/telegram/status")
async def telegram_status():
    """Estado general del webhook"""
    return {
        "webhook": "active",
        "timestamp": datetime.now().isoformat(),
        "bot_token_configured": bool(get_token()),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "company": os.getenv("EMPRESA_NAME", "milhojaldres")
    }

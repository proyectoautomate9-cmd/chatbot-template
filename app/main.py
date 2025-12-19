from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

# PRIMERO cargar .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# DESPUÉS importar routes (que usa os.getenv)
from app.routes import telegram_routes

app = FastAPI(
    title="Chatbot Milhojaldres",
    description="Bot de ventas IA para Milhojaldres",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_routes.router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "Chatbot Milhojaldres running",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/")
async def root():
    return {
        "message": "Chatbot Milhojaldres API",
        "version": "0.1.0",
        "docs": "/docs",
        "webhook": "/webhook/telegram",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

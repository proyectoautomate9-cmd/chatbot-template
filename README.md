# 🍰 Milhoja Dres Bot

Bot de Telegram para gestión de órdenes de milhojas y bebidas, integrado con Supabase.

## Características

- ✅ Menú interactivo de productos
- ✅ Carrito de compras
- ✅ Procesamiento de órdenes
- ✅ Notificaciones
- ✅ Historial de compras

## Requisitos

- Python 3.10+
- Supabase
- Telegram Bot Token

## Instalación

\\\ash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
\\\

## Configuración

1. Obtén tu token en @BotFather
2. Crea un proyecto en Supabase
3. Completa .env con tus credenciales

## Uso

\\\ash
python main.py
\\\

## Estructura

- app/ - Código principal
- config/ - Configuración
- tests/ - Tests
- scripts/ - Scripts SQL

## Base de Datos

Tablas: users, products, orders, order_items, preferences, notifications, audit_logs

## License

MIT

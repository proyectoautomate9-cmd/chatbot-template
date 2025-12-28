"""
Templates HTML para emails.
"""


def get_new_order_email_html(
    order_id: int, 
    user_name: str, 
    total: float,
    items_count: int = 0
) -> str:
    """Template para notificación de nuevo pedido al admin."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
                text-align: center;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .order-details {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }}
            .total {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 Nuevo Pedido Recibido</h1>
            <p>Pedido #{order_id}</p>
        </div>
        
        <div class="content">
            <p>¡Hola Admin! 👋</p>
            <p>Se ha recibido un nuevo pedido en <strong>Milhojaldres Bot</strong>.</p>
            
            <div class="order-details">
                <div class="detail-row">
                    <span>📋 Número de Pedido:</span>
                    <span>#{order_id}</span>
                </div>
                <div class="detail-row">
                    <span>👤 Cliente:</span>
                    <span>{user_name}</span>
                </div>
                <div class="detail-row">
                    <span>📦 Cantidad de Items:</span>
                    <span>{items_count if items_count > 0 else 'N/A'}</span>
                </div>
            </div>
            
            <div class="total">
                💰 Total: ${total:,.0f}
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                <strong>Próximos pasos:</strong><br>
                1. Revisa los detalles del pedido<br>
                2. Confirma el pedido para notificar al cliente<br>
                3. Prepara el pedido y actualiza el estado
            </p>
        </div>
    </body>
    </html>
    """


def get_order_confirmation_email_html(
    order_id: int,
    user_name: str,
    total: float
) -> str:
    """Template para confirmación de pedido al cliente."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
                text-align: center;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .success-icon {{
                font-size: 60px;
                text-align: center;
                margin: 20px 0;
            }}
            .total {{
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
                text-align: center;
                margin: 20px 0;
            }}
            .info-box {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #4CAF50;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Pedido Confirmado</h1>
            <p>#{order_id}</p>
        </div>
        
        <div class="content">
            <div class="success-icon">🎉</div>
            
            <p>¡Hola {user_name}! 👋</p>
            <p>Tu pedido ha sido <strong>confirmado exitosamente</strong> y está siendo preparado con mucho cariño.</p>
            
            <div class="total">
                💰 Total: ${total:,.0f}
            </div>
            
            <div class="info-box">
                <p><strong>📋 Número de pedido:</strong> #{order_id}</p>
                <p><strong>⏱️ Tiempo estimado:</strong> 30-45 minutos</p>
                <p><strong>📞 Contacto:</strong> +57 300 123 4567</p>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                Te notificaremos por Telegram cuando tu pedido esté listo. 🚚
            </p>
            
            <p style="margin-top: 30px;">
                ¡Gracias por tu preferencia! 🙏<br>
                <strong>Milhojaldres</strong>
            </p>
        </div>
    </body>
    </html>
    """

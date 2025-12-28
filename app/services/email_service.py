"""
Servicio para envío de emails con Gmail SMTP
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Maneja envío de emails con Gmail SMTP"""
    
    # Configuración desde .env
    SMTP_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('EMAIL_PORT', '587'))
    SMTP_USER = os.getenv('EMAIL_USER')
    SMTP_PASSWORD = os.getenv('EMAIL_PASSWORD')
    FROM_EMAIL = os.getenv('EMAIL_USER')  # Mismo que SMTP_USER
    FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Milhojaldres Bot')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    
    @classmethod
    def _send_email(
        cls,
        to_email: str,
        subject: str,
        body_html: str,
        attachment_path: Optional[str] = None
    ) -> bool:
        """
        Envía email con Gmail SMTP
        
        Args:
            to_email: Destinatario
            subject: Asunto
            body_html: Cuerpo en HTML
            attachment_path: Ruta del archivo adjunto (opcional)
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Validar configuración
            if not cls.SMTP_USER or not cls.SMTP_PASSWORD:
                logger.error("❌ EMAIL_USER y EMAIL_PASSWORD no configurados en .env")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{cls.FROM_NAME} <{cls.FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar cuerpo HTML
            html_part = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Agregar adjunto si existe
            if attachment_path and Path(attachment_path).exists():
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = Path(attachment_path).name
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
                    logger.info(f"📎 Adjunto agregado: {filename}")
            
            # Enviar email
            with smtplib.SMTP(cls.SMTP_HOST, cls.SMTP_PORT) as server:
                server.starttls()
                server.login(cls.SMTP_USER, cls.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado exitosamente a: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación SMTP: {e}")
            logger.error("Verifica EMAIL_USER y EMAIL_PASSWORD en .env")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def send_pre_order_email(
        cls,
        to_email: str,
        pre_order_data: Dict,
        pdf_path: Optional[str] = None
    ) -> bool:
        """
        Envía email con cotización/pre-orden al cliente
        
        Args:
            to_email: Email del cliente
            pre_order_data: Datos de la pre-orden
            pdf_path: Ruta del PDF adjunto
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            numero_cot = pre_order_data.get('numero_cotizacion', 'N/A')
            total = pre_order_data.get('total', 0)
            nombre = pre_order_data.get('nombre_cliente', 'Cliente')
            
            subject = f"📋 Tu Cotización #{numero_cot} - ${total:,.0f} | Milhojaldres"
            
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; border-radius: 4px; }}
        .total {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .highlight {{ background-color: #fffde7; padding: 15px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍪 Milhojaldres</h1>
            <p>Tu Cotización está Lista</p>
        </div>
        
        <div class="content">
            <h2>¡Hola {nombre}! 👋</h2>
            
            <p>Tu pre-orden ha sido creada exitosamente.</p>
            
            <div class="info">
                <p><strong>📋 Número de Cotización:</strong> {numero_cot}</p>
                <p><strong>💵 Total a Pagar:</strong> <span class="total">${total:,.0f}</span></p>
                <p><strong>📄 PDF Adjunto:</strong> Revisa el archivo adjunto para ver los detalles completos</p>
            </div>
            
            <h3>💳 ¿Cómo pagar?</h3>
            <ol>
                <li>Abre el PDF adjunto con los detalles de tu cotización</li>
                <li>Elige tu método de pago (Nequi, Daviplata o Transferencia)</li>
                <li>Realiza el pago por el monto total indicado</li>
                <li>Envía el comprobante al WhatsApp: <strong>301 417 0313</strong></li>
            </ol>
            
            <div class="highlight">
                <p><strong>⏰ Confirmación:</strong></p>
                <p>Verificaremos tu pago en 1-2 horas máximo y te enviaremos la confirmación.</p>
            </div>
            
            <h3>📱 ¿Tienes dudas?</h3>
            <p>Contáctanos directamente:</p>
            <ul>
                <li><strong>WhatsApp:</strong> 301 417 0313</li>
                <li><strong>Email:</strong> {cls.FROM_EMAIL}</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Esta cotización es válida por 7 días</p>
            <p>Milhojaldres | Bogotá, Colombia</p>
            <p>¡Gracias por tu confianza! 🍪</p>
        </div>
    </div>
</body>
</html>
            """
            
            return cls._send_email(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                attachment_path=pdf_path
            )
            
        except Exception as e:
            logger.error(f"❌ Error en send_pre_order_email: {e}")
            return False
    
    @classmethod
    def send_order_confirmation_to_admin(
        cls,
        order_data: Dict
    ) -> bool:
        """
        Envía notificación de pedido normal al admin
        
        Args:
            order_data: Datos del pedido
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            if not cls.ADMIN_EMAIL:
                logger.warning("⚠️ ADMIN_EMAIL no configurado en .env")
                return False
            
            order_id = order_data.get('order_id', 'N/A')
            total = order_data.get('total', 0)
            nombre = order_data.get('nombre_cliente', 'Cliente')
            items = order_data.get('items', [])
            
            # Construir tabla de productos
            items_html = ""
            for item in items:
                items_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{item.get('product_name', 'N/A')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item.get('cantidad', 0)}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${item.get('precio_unitario', 0):,.0f}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${item.get('subtotal', 0):,.0f}</td>
                </tr>
                """
            
            subject = f"🔔 Nuevo Pedido #{order_id} - ${total:,.0f}"
            
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background-color: white; }}
        th {{ background-color: #2196F3; color: white; padding: 10px; text-align: left; }}
        .total-row {{ background-color: #e3f2fd; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Nuevo Pedido Recibido</h1>
            <p>Pedido #{order_id}</p>
        </div>
        
        <div class="content">
            <div class="info">
                <p><strong>👤 Cliente:</strong> {nombre}</p>
                <p><strong>📦 Orden:</strong> #{order_id}</p>
                <p><strong>💰 Total:</strong> ${total:,.0f}</p>
                <p><strong>📅 Fecha:</strong> {order_data.get('fecha', 'N/A')}</p>
            </div>
            
            <h3>📋 Productos:</h3>
            <table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th style="text-align: center;">Cantidad</th>
                        <th style="text-align: right;">Precio Unit.</th>
                        <th style="text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                    <tr class="total-row">
                        <td colspan="3" style="padding: 10px; text-align: right;">TOTAL:</td>
                        <td style="padding: 10px; text-align: right;">${total:,.0f}</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="info">
                <p><strong>⚠️ Acción requerida:</strong></p>
                <p>Revisa tu panel de administración para gestionar este pedido.</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            result = cls._send_email(
                to_email=cls.ADMIN_EMAIL,
                subject=subject,
                body_html=body_html
            )
            
            if result:
                logger.info(f"✅ Notificación de orden #{order_id} enviada al admin")
            else:
                logger.error(f"❌ No se pudo enviar notificación de orden #{order_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en send_order_confirmation_to_admin: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def send_new_order_notification_to_admin(cls, order_data: Dict) -> bool:
        """Alias para mantener compatibilidad con código anterior"""
        return cls.send_order_confirmation_to_admin(order_data)


# Instancia singleton para compatibilidad
email_service = EmailService()

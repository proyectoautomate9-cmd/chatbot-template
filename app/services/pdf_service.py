"""
Servicio para generar PDFs de pedidos y cotizaciones
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger(__name__)


class PDFService:
    """Genera PDFs para pedidos y cotizaciones"""
    
    # Directorio donde se guardan los PDFs
    PDF_DIR = Path("pdfs")
    
    @classmethod
    def _ensure_pdf_dir(cls):
        """Asegura que existe el directorio de PDFs"""
        cls.PDF_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def generate_order_pdf(
        cls,
        order_data: Dict,
        items: List[Dict]
    ) -> str:
        """
        Genera PDF de pedido/orden
        
        Args:
            order_data: Datos de la orden
            items: Lista de productos
        
        Returns:
            str: Ruta del PDF generado
        """
        try:
            cls._ensure_pdf_dir()
            
            # Nombre del archivo
            order_id = order_data.get('order_id', 'N/A')
            filename = f"Pedido_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = cls.PDF_DIR / filename
            
            # Crear documento
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Contenedor de elementos
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilo personalizado para título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2196F3'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Estilo para subtítulos
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2196F3'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # ============================================
            # ENCABEZADO
            # ============================================
            elements.append(Paragraph("🍪 MILHOJALDRES", title_style))
            elements.append(Paragraph(f"Pedido #{order_id}", styles['Heading2']))
            elements.append(Spacer(1, 0.3*inch))
            
            # ============================================
            # INFORMACIÓN DEL CLIENTE
            # ============================================
            elements.append(Paragraph("📋 Información del Pedido", subtitle_style))
            
            cliente = order_data.get('nombre_cliente', 'N/A')
            fecha = order_data.get('fecha', datetime.now().strftime('%Y-%m-%d %H:%M'))
            
            info_data = [
                ['👤 Cliente:', cliente],
                ['📅 Fecha:', fecha],
                ['🔢 Orden:', f"#{order_id}"],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # ============================================
            # TABLA DE PRODUCTOS
            # ============================================
            elements.append(Paragraph("📦 Productos", subtitle_style))
            
            # Encabezados de tabla
            products_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
            
            # Agregar productos
            for item in items:
                nombre = item.get('product_name', 'N/A')
                cantidad = item.get('cantidad', 0)
                precio = item.get('precio_unitario', 0)
                subtotal = item.get('subtotal', 0)
                
                products_data.append([
                    nombre,
                    str(cantidad),
                    f"${precio:,.0f}",
                    f"${subtotal:,.0f}"
                ])
            
            # Crear tabla
            products_table = Table(products_data, colWidths=[3*inch, 1*inch, 1.2*inch, 1.2*inch])
            products_table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                
                # Cuerpo
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2196F3')),
                ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#2196F3')),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(products_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # ============================================
            # TOTALES
            # ============================================
            total = order_data.get('total', 0)
            anticipo = total * 0.5
            
            totals_data = [
                ['Subtotal:', f"${total:,.0f}"],
                ['TOTAL:', f"${total:,.0f}"],
                ['Anticipo (50%):', f"${anticipo:,.0f}"],
            ]
            
            totals_table = Table(totals_data, colWidths=[4.5*inch, 2*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('FONTSIZE', (0, 1), (-1, 1), 14),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#4CAF50')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEABOVE', (0, 1), (-1, 1), 2, colors.HexColor('#2196F3')),
            ]))
            
            elements.append(totals_table)
            elements.append(Spacer(1, 0.4*inch))
            
            # ============================================
            # INFORMACIÓN DE PAGO
            # ============================================
            elements.append(Paragraph("💳 Información de Pago", subtitle_style))
            
            payment_text = """
            <b>Métodos de pago:</b> Nequi / Daviplata<br/>
            <b>Número:</b> 3014170313<br/><br/>
            
            <b>⚠️ Envía el comprobante del anticipo (50%) al WhatsApp</b>
            """
            
            elements.append(Paragraph(payment_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # ============================================
            # PUNTOS DE RECOGIDA
            # ============================================
            elements.append(Paragraph("📍 Puntos de Recogida", subtitle_style))
            
            pickup_text = """
            Elige uno al contactarnos:<br/>
            • <b>Calle 96b #20d–70</b><br/>
            • <b>Cra 81b #19b–80</b><br/><br/>
            
            <b>📞 Contacto:</b> 3014170313
            """
            
            elements.append(Paragraph(pickup_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # ============================================
            # INSTRUCCIONES
            # ============================================
            elements.append(Paragraph("⚠️ Importante", subtitle_style))
            
            instructions_text = """
            1️⃣ Envía comprobante del anticipo (50%)<br/>
            2️⃣ Indica fecha y hora de recogida<br/>
            3️⃣ Confirma punto de recogida<br/>
            4️⃣ NO hacemos domicilios directos<br/>
            5️⃣ Pedidos grandes: 2 días de anticipación
            """
            
            elements.append(Paragraph(instructions_text, styles['Normal']))
            
            # ============================================
            # PIE DE PÁGINA
            # ============================================
            elements.append(Spacer(1, 0.4*inch))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            
            footer_text = f"""
            Milhojaldres | Bogotá, Colombia<br/>
            Gracias por tu compra 🍪<br/>
            Documento generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            elements.append(Paragraph(footer_text, footer_style))
            
            # ============================================
            # GENERAR PDF
            # ============================================
            doc.build(elements)
            
            logger.info(f"✅ PDF generado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Error generando PDF: {e}")
            import traceback
            traceback.print_exc()
            return None


# Test
if __name__ == "__main__":
    # Prueba de generación
    test_order = {
        'order_id': 999,
        'nombre_cliente': 'Juan Pérez (TEST)',
        'total': 50000,
        'fecha': '2025-12-28 11:45',
    }
    
    test_items = [
        {
            'product_name': 'Milhoja Tradicional',
            'cantidad': 10,
            'precio_unitario': 3500,
            'subtotal': 35000
        },
        {
            'product_name': 'Milhoja Premium',
            'cantidad': 5,
            'precio_unitario': 3000,
            'subtotal': 15000
        }
    ]
    
    pdf_path = PDFService.generate_order_pdf(test_order, test_items)
    
    if pdf_path:
        print(f"✅ PDF generado exitosamente: {pdf_path}")
    else:
        print("❌ Error al generar PDF")

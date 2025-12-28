"""
Servicio para generar PDFs de cotización (versión simple)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Genera PDFs de cotización profesionales"""
    
    # Directorio donde se guardan los PDFs
    PDF_DIR = Path("pdfs")
    
    @classmethod
    def ensure_pdf_directory(cls):
        """Crea directorio de PDFs si no existe"""
        cls.PDF_DIR.mkdir(exist_ok=True)
        logger.info(f"✅ Directorio PDF: {cls.PDF_DIR.absolute()}")
    
    @classmethod
    def generate_cotizacion_number(cls) -> str:
        """
        Genera número único de cotización
        
        Returns:
            str: Número de cotización (ej: COT-2025-001)
        """
        now = datetime.now()
        year = now.year
        
        # Usar timestamp para garantizar unicidad
        numero = f"COT-{year}-{now.strftime('%m%d%H%M%S')}"
        
        return numero
    
    @classmethod
    def generate_pdf(
        cls,
        pre_order_data: Dict,
        items: List[Dict],
        location: Dict
    ) -> Optional[str]:
        """
        Genera PDF de cotización (versión placeholder)
        
        Args:
            pre_order_data: Datos de la pre-orden
            items: Lista de productos
            location: Información de ubicación de recogida
        
        Returns:
            str: Ruta del PDF generado o None si falla
        """
        try:
            cls.ensure_pdf_directory()
            
            # Nombre del archivo
            numero_cot = pre_order_data['numero_cotizacion']
            pdf_filename = f"{numero_cot}.pdf"
            pdf_path = cls.PDF_DIR / pdf_filename
            
            # Por ahora solo creamos un archivo vacío como placeholder
            # En producción aquí iría WeasyPrint para generar el PDF real
            
            # Crear archivo placeholder
            with open(pdf_path, 'w') as f:
                f.write(f"Cotización: {numero_cot}\n")
                f.write(f"Cliente: {pre_order_data.get('nombre_cliente')}\n")
                f.write(f"Total: ${pre_order_data.get('total'):,.0f}\n")
            
            logger.info(f"✅ PDF placeholder generado: {pdf_path}")
            
            # Retornar ruta relativa para guardar en BD
            return f"/pdfs/{pdf_filename}"
            
        except Exception as e:
            logger.error(f"❌ Error generando PDF: {e}")
            import traceback
            traceback.print_exc()
            return None


# Test
if __name__ == "__main__":
    from datetime import date, time
    
    # Datos de ejemplo
    pre_order = {
        'numero_cotizacion': 'COT-2025-001',
        'fecha_creacion': datetime.now(),
        'nombre_cliente': 'Juan García',
        'email_cliente': 'juan@email.com',
        'total': 45000,
    }
    
    items = [
        {'nombre': 'Milhojas', 'cantidad': 50, 'precio': 800},
    ]
    
    location = {
        'nombre': '📍 Local Calle 96b',
        'direccion': 'Calle 96b #20d–70',
    }
    
    pdf_path = PDFGenerator.generate_pdf(pre_order, items, location)
    print(f"PDF generado: {pdf_path}")

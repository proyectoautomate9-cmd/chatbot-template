"""
Validadores de datos.
"""

import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True si el formato es válido
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_html(text: str) -> str:
    """
    Sanitiza texto para prevenir inyección HTML.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Reemplazar caracteres peligrosos
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def validate_order_id(order_id: int) -> bool:
    """
    Valida que el order_id sea válido.
    
    Args:
        order_id: ID del pedido
        
    Returns:
        True si es válido
    """
    return isinstance(order_id, int) and order_id > 0

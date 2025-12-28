"""
Servicio para calcular descuentos por volumen
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DiscountService:
    """Maneja cálculo de descuentos por volumen"""
    
    # Configuración de descuentos por cantidad total
    DISCOUNT_TIERS = [
        {"min_quantity": 100, "discount_percent": 15},
        {"min_quantity": 50, "discount_percent": 10},
        {"min_quantity": 20, "discount_percent": 5},
    ]
    
    @classmethod
    def calculate_discount(cls, cart_items: List[Dict]) -> Tuple[float, int, float, float]:
        """
        Calcula descuento basado en cantidad total de productos
        
        Args:
            cart_items: Lista de items del carrito con estructura:
                [
                    {'product_id': 1, 'nombre': 'X', 'precio': 1000, 'cantidad': 50},
                    ...
                ]
        
        Returns:
            Tuple[float, int, float, float]: (subtotal, descuento_porcentaje, descuento_monto, total)
        """
        try:
            # Calcular subtotal y cantidad total
            subtotal = 0.0
            total_quantity = 0
            
            for item in cart_items:
                precio = float(item.get('precio', 0))
                cantidad = int(item.get('cantidad', 0))
                subtotal += precio * cantidad
                total_quantity += cantidad
            
            # Determinar descuento aplicable
            descuento_porcentaje = 0
            
            for tier in cls.DISCOUNT_TIERS:
                if total_quantity >= tier['min_quantity']:
                    descuento_porcentaje = tier['discount_percent']
                    break
            
            # Calcular monto de descuento
            descuento_monto = subtotal * (descuento_porcentaje / 100)
            
            # Calcular total
            total = subtotal - descuento_monto
            
            logger.info(
                f"Descuento calculado: {total_quantity} unidades → "
                f"{descuento_porcentaje}% = ${descuento_monto:,.0f}"
            )
            
            return (subtotal, descuento_porcentaje, descuento_monto, total)
            
        except Exception as e:
            logger.error(f"Error calculando descuento: {e}")
            # En caso de error, retornar sin descuento
            return (subtotal, 0, 0.0, subtotal)
    
    @classmethod
    def get_discount_info_text(cls, total_quantity: int) -> str:
        """
        Genera texto informativo sobre descuentos disponibles
        
        Args:
            total_quantity: Cantidad total de productos en el carrito
        
        Returns:
            str: Texto con información de descuentos
        """
        text = "💰 **DESCUENTOS POR VOLUMEN**\n\n"
        
        for tier in reversed(cls.DISCOUNT_TIERS):
            min_qty = tier['min_quantity']
            discount = tier['discount_percent']
            
            if total_quantity >= min_qty:
                text += f"✅ {min_qty}+ unidades: **{discount}% OFF** (¡Aplicado!)\n"
            else:
                remaining = min_qty - total_quantity
                text += f"⭕ {min_qty}+ unidades: {discount}% OFF (Te faltan {remaining})\n"
        
        return text
    
    @classmethod
    def apply_discount_to_items(cls, cart_items: List[Dict], descuento_porcentaje: int) -> List[Dict]:
        """
        Aplica descuento proporcional a cada item del carrito
        
        Args:
            cart_items: Lista de items del carrito
            descuento_porcentaje: Porcentaje de descuento a aplicar
        
        Returns:
            List[Dict]: Items con descuentos aplicados individualmente
        """
        items_with_discount = []
        
        for item in cart_items:
            precio = float(item.get('precio', 0))
            cantidad = int(item.get('cantidad', 0))
            precio_total = precio * cantidad
            
            # Calcular descuento del item
            descuento_item = precio_total * (descuento_porcentaje / 100)
            
            items_with_discount.append({
                'product_id': item['product_id'],
                'nombre': item['nombre'],
                'precio': precio,
                'cantidad': cantidad,
                'precio_total': precio_total,
                'descuento_aplicado': descuento_item
            })
        
        return items_with_discount


# Test
if __name__ == "__main__":
    # Ejemplo de uso
    cart = [
        {'product_id': 1, 'nombre': 'Milhojas', 'precio': 5000, 'cantidad': 30},
        {'product_id': 2, 'nombre': 'Palmitas', 'precio': 3000, 'cantidad': 25},
    ]
    
    subtotal, desc_pct, desc_monto, total = DiscountService.calculate_discount(cart)
    
    print(f"Subtotal: ${subtotal:,.0f}")
    print(f"Descuento: {desc_pct}% = ${desc_monto:,.0f}")
    print(f"Total: ${total:,.0f}")
    print()
    print(DiscountService.get_discount_info_text(55))

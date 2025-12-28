"""
Gestión de pedidos con cambio de estados.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config.database import get_supabase


def show_orders_management():
    """Página de gestión de pedidos."""
    
    st.title("📦 Gestión de Pedidos")
    st.markdown("---")
    
    supabase = get_supabase()
    
    # ============================================
    # FILTROS
    # ============================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "📊 Estado",
            ["Todos", "pending", "confirmed", "preparing", "ready", "delivered", "cancelled"]
        )
    
    with col2:
        filter_date = st.date_input(
            "📅 Desde fecha",
            value=None,
            help="Mostrar pedidos desde esta fecha"
        )
    
    with col3:
        limit = st.number_input(
            "🔢 Mostrar últimos",
            min_value=10,
            max_value=100,
            value=20,
            step=10
        )
    
    st.markdown("---")
    
    # ============================================
    # OBTENER PEDIDOS
    # ============================================
    try:
        query = supabase.table("orders").select("*")
        
        # Aplicar filtros
        if filter_status != "Todos":
            query = query.eq("estado", filter_status)
        
        if filter_date:
            query = query.gte("fecha_orden", f"{filter_date}T00:00:00")
        
        query = query.order("fecha_orden", desc=True).limit(limit)
        
        response = query.execute()
        orders = response.data
        
        if not orders:
            st.info("📭 No se encontraron pedidos con los filtros seleccionados")
            return
        
        st.success(f"✅ {len(orders)} pedidos encontrados")
        
        # ============================================
        # MOSTRAR PEDIDOS
        # ============================================
        for order in orders:
            # Estado emoji
            estado_emoji = {
                'pending': '🕐',
                'confirmed': '✅',
                'preparing': '👨‍🍳',
                'ready': '📦',
                'delivered': '✅',
                'cancelled': '❌'
            }
            emoji = estado_emoji.get(order['estado'], '❓')
            
            # Color según estado
            if order['estado'] == 'pending':
                expanded = True
            else:
                expanded = False
            
            with st.expander(
                f"{emoji} Pedido #{order['order_id']} - {order['estado'].upper()} - ${order['total']:,.0f}",
                expanded=expanded
            ):
                col_info, col_actions = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**User ID:** {order['user_id']}")
                    st.write(f"**Subtotal:** ${order.get('subtotal', 0):,.0f}")
                    st.write(f"**Total:** ${order['total']:,.0f}")
                    st.write(f"**Fecha:** {order['fecha_orden'][:19]}")
                    
                    if order.get('notas'):
                        st.info(f"📝 Notas: {order['notas']}")
                    
                    # Items del pedido
                    items_response = supabase.table("order_items")\
                        .select("*, products(nombre, precio)")\
                        .eq("order_id", order['order_id'])\
                        .execute()
                    
                    if items_response.data:
                        st.markdown("**📦 Items del pedido:**")
                        for item in items_response.data:
                            product = item.get('products', {})
                            product_name = product.get('nombre', 'N/A')
                            st.write(f"- {product_name} x{item['cantidad']} = ${item['subtotal']:,.0f}")
                
                with col_actions:
                    st.markdown("**🔄 Cambiar Estado:**")
                    
                    estados = ["pending", "confirmed", "preparing", "ready", "delivered", "cancelled"]
                    current_index = estados.index(order['estado']) if order['estado'] in estados else 0
                    
                    new_status = st.selectbox(
                        "Nuevo estado",
                        estados,
                        index=current_index,
                        key=f"status_{order['order_id']}"
                    )
                    
                    if st.button(f"💾 Actualizar", key=f"update_{order['order_id']}"):
                        try:
                            # Actualizar estado
                            supabase.table("orders")\
                                .update({"estado": new_status})\
                                .eq("order_id", order['order_id'])\
                                .execute()
                            
                            st.success(f"✅ Estado actualizado a: **{new_status}**")
                            st.info("🔔 El cliente recibirá notificación automática (Feature 1)")
                            
                            # Recargar
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
    
    except Exception as e:
        st.error(f"❌ Error cargando pedidos: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

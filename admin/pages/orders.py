"""
Gestión de pedidos con cambio de estados.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config.database import get_supabase


def show_orders_management():
    """Página de gestión de pedidos."""
    
    supabase = get_supabase()
    
    # Get pending count for header
    pending = supabase.table("orders").select("order_id").eq("estado", "pending").execute()
    pending_count = len(pending.data) if pending.data else 0
    
    # Header with pending badge
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.markdown("### 📦 Gestión de Pedidos")
    with col_badge:
        if pending_count > 0:
            st.markdown(f"""
                <div style="background: rgba(243, 156, 18, 0.2); color: #F39C12; padding: 0.5rem 1rem; border-radius: 12px; text-align: center; font-weight: 600; border: 1px solid rgba(243, 156, 18, 0.3);">
                    ⏳ {pending_count} pendientes
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # FILTROS
    # ============================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_map_filter = {
            "Todos": "Todos",
            "Pendiente": "pending",
            "Confirmado": "confirmed",
            "En Preparación": "preparing",
            "Listo para Entrega": "ready",
            "Entregado": "delivered",
            "Cancelado": "cancelled"
        }
        
        filter_status_label = st.selectbox(
            "📊 Estado",
            list(status_map_filter.keys())
        )
        filter_status = status_map_filter[filter_status_label]
    
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
            
            status_translation = {
                'pending': 'PENDIENTE',
                'confirmed': 'CONFIRMADO',
                'preparing': 'EN PREPARACIÓN',
                'ready': 'LISTO',
                'delivered': 'ENTREGADO',
                'cancelled': 'CANCELADO'
            }
            estado_es = status_translation.get(order['estado'], order['estado'].upper())
            
            with st.expander(
                f"{emoji} Pedido #{order['order_id']} - {estado_es} - ${order['total']:,.0f}",
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
                    
                    status_options = {
                        "pending": "🕐 Pendiente",
                        "confirmed": "✅ Confirmado",
                        "preparing": "👨‍🍳 Preparando",
                        "ready": "📦 Listo para Entrega",
                        "delivered": "🚚 Entregado",
                        "cancelled": "❌ Cancelado"
                    }
                    
                    current_status = order['estado']
                    
                    new_status_key = st.selectbox(
                        "Nuevo estado",
                        options=list(status_options.keys()),
                        format_func=lambda x: status_options[x],
                        index=list(status_options.keys()).index(current_status) if current_status in status_options else 0,
                        key=f"status_{order['order_id']}"
                    )
                    
                    if st.button(f"💾 Actualizar", key=f"update_{order['order_id']}"):
                        try:
                            # Actualizar estado
                            supabase.table("orders")\
                                .update({"estado": new_status_key})\
                                .eq("order_id", order['order_id'])\
                                .execute()
                            
                            st.success(f"✅ Estado actualizado a: **{status_options.get(new_status_key, new_status_key)}**")
                            st.info("🔔 El cliente recibirá notificación automática")
                            
                            # Recargar
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
    
    except Exception as e:
        st.error(f"❌ Error cargando pedidos: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

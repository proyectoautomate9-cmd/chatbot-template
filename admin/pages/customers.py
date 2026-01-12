"""
Gestión de Clientes con información de contacto, historial y descuentos.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config.database import get_supabase


def show_customers():
    """Página de gestión de clientes."""
    
    st.markdown("### 👥 Gestión de Clientes")
    
    supabase = get_supabase()
    
    # Check if viewing a specific customer
    if 'viewing_customer' in st.session_state and st.session_state['viewing_customer']:
        show_customer_detail(st.session_state['viewing_customer'])
        return
    
    try:
        # ============================================
        # CUSTOMER STATS
        # ============================================
        users = supabase.table("users").select("*").execute()
        
        if not users.data:
            st.info("📭 No hay clientes registrados aún")
            return
        
        # Calculate stats
        total_customers = len(users.data)
        
        # New this month
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        new_this_month = len([u for u in users.data if u.get('created_at') and datetime.fromisoformat(u['created_at'].replace('Z', '+00:00')) >= first_day_month.replace(tzinfo=None)])
        
        # Get order data for active customers
        orders = supabase.table("orders").select("user_id, total, estado").execute()
        customer_orders = {}
        for order in orders.data:
            uid = order.get('user_id')
            if uid not in customer_orders:
                customer_orders[uid] = {'count': 0, 'total': 0}
            customer_orders[uid]['count'] += 1
            customer_orders[uid]['total'] += order.get('total', 0)
        
        active_customers = len(customer_orders)
        
        # Stats row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Clientes Totales", total_customers)
        with col2:
            st.metric("🆕 Nuevos (Este Mes)", new_this_month)
        with col3:
            st.metric("🛒 Con compras", active_customers)
        
        st.markdown("---")
        
        # ============================================
        # SEARCH & FILTERS
        # ============================================
        col_search, col_filter = st.columns([2, 1])
        
        with col_search:
            search = st.text_input("🔍 Buscar cliente", placeholder="Nombre o teléfono...")
        
        with col_filter:
            filter_type = st.selectbox(
                "Ordenar por",
                ["Más recientes", "Mayor valor", "Más pedidos"]
            )
        
        # Filter users
        filtered_users = users.data
        if search:
            search_lower = search.lower()
            filtered_users = [
                u for u in filtered_users 
                if search_lower in (u.get('nombre') or '').lower() 
                or search_lower in (u.get('telefono') or '')
            ]
        
        # Sort
        if filter_type == "Más recientes":
            filtered_users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif filter_type == "Mayor valor":
            filtered_users.sort(key=lambda x: customer_orders.get(x['user_id'], {}).get('total', 0), reverse=True)
        elif filter_type == "Más pedidos":
            filtered_users.sort(key=lambda x: customer_orders.get(x['user_id'], {}).get('count', 0), reverse=True)
        
        st.markdown(f"📦 Mostrando **{len(filtered_users)}** clientes")
        
        # ============================================
        # CUSTOMER LIST
        # ============================================
        for user in filtered_users:
            user_id = user.get('user_id')
            name = user.get('nombre') or 'Sin nombre'
            phone = user.get('telefono') or 'Sin teléfono'
            
            # Get customer stats
            stats = customer_orders.get(user_id, {'count': 0, 'total': 0})
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                    <div class="customer-card" style="padding: 1.25rem; margin-bottom: 0.75rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div style="display: flex; align-items: center; gap: 1.25rem;">
                            <div class="customer-avatar" style="width: 48px; height: 48px; background: rgba(0, 180, 216, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #00B4D8; border: 1px solid rgba(0, 180, 216, 0.3);">
                                {name[0].upper() if name else '?'}
                            </div>
                            <div style="flex: 1;">
                                <p style="margin: 0; font-weight: 600; color: #F8FAFC; font-size: 1.1rem;">{name}</p>
                                <p style="margin: 0.25rem 0 0 0; color: #94A3B8; font-size: 0.875rem;">📱 {phone}</p>
                            </div>
                            <div style="text-align: right;">
                                <p style="margin: 0; font-weight: 700; color: #00B4D8; font-size: 1.1rem;">${stats['total']:,.0f}</p>
                                <p style="margin: 0.25rem 0 0 0; color: #94A3B8; font-size: 0.875rem;">{stats['count']} pedidos</p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("👁️ Ver", key=f"view_{user_id}"):
                    st.session_state['viewing_customer'] = user
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error cargando clientes: {e}")


def show_customer_detail(customer):
    """Muestra el detalle de un cliente específico."""
    
    supabase = get_supabase()
    user_id = customer.get('user_id')
    
    # Back button
    if st.button("← Volver a la lista"):
        st.session_state['viewing_customer'] = None
        st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # CUSTOMER INFO HEADER
    # ============================================
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1.5rem; background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
                <div style="width: 72px; height: 72px; background: rgba(0, 180, 216, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.75rem; font-weight: 700; color: #00B4D8; border: 1px solid rgba(0, 180, 216, 0.3);">
                    {(customer.get('nombre') or '?')[0].upper()}
                </div>
                <div>
                    <h2 style="margin: 0; color: #F8FAFC;">{customer.get('nombre') or 'Sin nombre'}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: #94A3B8;">Cliente desde {customer.get('created_at', '')[:10]}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Quick actions
        st.markdown("**Acciones rápidas**")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Información",
        "📦 Historial de Pedidos",
        "🎟️ Descuentos",
        "📝 Notas"
    ])
    
    # ============================================
    # TAB 1: CONTACT INFO
    # ============================================
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Información de Contacto")
            st.markdown(f"**Nombre:** {customer.get('nombre') or 'No registrado'}")
            st.markdown(f"**Teléfono:** {customer.get('telefono') or 'No registrado'}")
            st.markdown(f"**Dirección:** {customer.get('direccion') or 'No registrada'}")
            st.markdown(f"**Telegram ID:** `{customer.get('telegram_id')}`")
        
        with col2:
            # Customer stats
            st.markdown("#### Estadísticas")
            
            orders = supabase.table("orders")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if orders.data:
                total_spent = sum(o.get('total', 0) for o in orders.data)
                order_count = len(orders.data)
                avg_order = total_spent / order_count if order_count > 0 else 0
                
                st.metric("💰 Total Gastado", f"${total_spent:,.0f}")
                st.metric("📦 Total Pedidos", order_count)
                st.metric("💵 Ticket Promedio", f"${avg_order:,.0f}")
            else:
                st.info("Sin pedidos aún")
    
    # ============================================
    # TAB 2: ORDER HISTORY
    # ============================================
    with tab2:
        st.markdown("#### Historial de Pedidos")
        
        orders = supabase.table("orders")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("fecha_orden", desc=True)\
            .execute()
        
        if orders.data:
            for order in orders.data:
                estado = order.get('estado', 'unknown')
                emoji = {
                    'pending': '🕐',
                    'confirmed': '✅',
                    'preparing': '👨‍🍳',
                    'ready': '📦',
                    'delivered': '✅',
                    'cancelled': '❌'
                }.get(estado, '❓')
                
                with st.expander(f"{emoji} Pedido #{order['order_id']} - ${order['total']:,.0f} - {order['fecha_orden'][:10]}"):
                    st.markdown(f"**Estado:** {estado}")
                    st.markdown(f"**Total:** ${order['total']:,.0f}")
                    st.markdown(f"**Fecha:** {order['fecha_orden'][:19]}")
                    
                    if order.get('notas'):
                        st.info(f"📝 {order['notas']}")
                    
                    # Items
                    items = supabase.table("order_items")\
                        .select("*, products(nombre)")\
                        .eq("order_id", order['order_id'])\
                        .execute()
                    
                    if items.data:
                        st.markdown("**Productos:**")
                        for item in items.data:
                            prod = item.get('products', {})
                            st.write(f"- {prod.get('nombre', 'N/A')} x{item['cantidad']} = ${item['subtotal']:,.0f}")
        else:
            st.info("📭 Este cliente no tiene pedidos")
    
    # ============================================
    # TAB 3: DISCOUNTS
    # ============================================
    with tab3:
        st.markdown("#### Descuentos Asignados")
        
        try:
            # Get discounts for this customer
            discounts = supabase.table("discounts")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if discounts.data:
                for d in discounts.data:
                    status = "🟢 Activo" if d.get('active') else "⚫ Inactivo"
                    st.markdown(f"""
                        - **{d.get('name')}**: {d.get('value')}{'%' if d.get('discount_type') == 'percentage' else ' COP'} {status}
                    """)
            else:
                st.info("No tiene descuentos asignados")
            
            st.markdown("---")
            st.markdown("#### Asignar Nuevo Descuento")
            
            with st.form("assign_discount"):
                name = st.text_input("Nombre del descuento")
                col1, col2 = st.columns(2)
                with col1:
                    value_type = st.selectbox("Tipo", ["percentage", "fixed"], format_func=lambda x: "Porcentaje" if x == "percentage" else "Monto fijo")
                with col2:
                    value = st.number_input("Valor", min_value=0.0)
                
                if st.form_submit_button("✅ Asignar Descuento"):
                    if name and value > 0:
                        try:
                            supabase.table("discounts").insert({
                                "name": name,
                                "type": "individual",
                                "discount_type": value_type,
                                "value": value,
                                "user_id": user_id,
                                "active": True
                            }).execute()
                            st.success("✅ Descuento asignado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Completa todos los campos")
        
        except Exception as e:
            st.warning("No se pudieron cargar los descuentos. Verifica que la tabla existe.")
    
    # ============================================
    # TAB 4: NOTES
    # ============================================
    with tab4:
        st.markdown("#### Notas del Administrador")
        
        current_notes = customer.get('admin_notes') or ''
        
        new_notes = st.text_area("Notas sobre este cliente", value=current_notes, height=150)
        
        if st.button("💾 Guardar Notas"):
            try:
                supabase.table("users")\
                    .update({"admin_notes": new_notes})\
                    .eq("user_id", user_id)\
                    .execute()
                st.success("✅ Notas guardadas!")
            except Exception as e:
                st.error(f"Error: {e}")

"""
Dashboard con métricas del negocio.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config.database import get_supabase


def show_dashboard():
    """Muestra el dashboard principal con métricas."""
    
    st.title("📊 Dashboard - Milhojaldres")
    st.markdown("---")
    
    supabase = get_supabase()
    
    try:
        # Fecha de hoy
        today = datetime.now().date()
        
        # ============================================
        # MÉTRICAS DEL DÍA
        # ============================================
        
        # Pedidos de hoy
        orders_today = supabase.table("orders")\
            .select("*")\
            .gte("fecha_orden", f"{today}T00:00:00")\
            .execute()
        
        total_orders_today = len(orders_today.data)
        total_revenue_today = sum(o.get('total', 0) for o in orders_today.data)
        
        # Pedidos pendientes
        pending_orders = supabase.table("orders")\
            .select("*")\
            .eq("estado", "pending")\
            .execute()
        
        total_pending = len(pending_orders.data)
        
        # Total de clientes
        users_response = supabase.table("users")\
            .select("user_id", count="exact")\
            .execute()
        
        total_users = len(users_response.data)
        
        # ============================================
        # MOSTRAR MÉTRICAS EN COLUMNAS
        # ============================================
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Pedidos Hoy",
                value=total_orders_today
            )
        
        with col2:
            st.metric(
                label="💰 Ingresos Hoy",
                value=f"${total_revenue_today:,.0f}"
            )
        
        with col3:
            st.metric(
                label="⏳ Pendientes",
                value=total_pending
            )
        
        with col4:
            st.metric(
                label="👥 Clientes",
                value=total_users
            )
        
        st.markdown("---")
        
        # ============================================
        # ÚLTIMOS PEDIDOS
        # ============================================
        st.subheader("📋 Últimos 10 Pedidos")
        
        recent_orders = supabase.table("orders")\
            .select("order_id, user_id, estado, total, fecha_orden")\
            .order("fecha_orden", desc=True)\
            .limit(10)\
            .execute()
        
        if recent_orders.data:
            df = pd.DataFrame(recent_orders.data)
            
            # Formatear fecha
            df['fecha_orden'] = pd.to_datetime(df['fecha_orden']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Formatear total
            df['total'] = df['total'].apply(lambda x: f"${x:,.0f}")
            
            # Emoji por estado
            estado_emoji = {
                'pending': '🕐',
                'confirmed': '✅',
                'preparing': '👨‍🍳',
                'ready': '📦',
                'delivered': '✅',
                'cancelled': '❌'
            }
            df['estado'] = df['estado'].apply(lambda x: f"{estado_emoji.get(x, '❓')} {x}")
            
            # Renombrar columnas
            df = df.rename(columns={
                'order_id': 'ID',
                'user_id': 'Usuario',
                'estado': 'Estado',
                'total': 'Total',
                'fecha_orden': 'Fecha'
            })
            
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("📭 No hay pedidos registrados")
        
        # ============================================
        # GRÁFICA DE PEDIDOS (últimos 7 días)
        # ============================================
        st.markdown("---")
        st.subheader("📈 Pedidos de los últimos 7 días")
        
        last_week = datetime.now() - timedelta(days=7)
        orders_week = supabase.table("orders")\
            .select("fecha_orden")\
            .gte("fecha_orden", last_week.isoformat())\
            .execute()
        
        if orders_week.data and len(orders_week.data) > 0:
            df_week = pd.DataFrame(orders_week.data)
            df_week['fecha'] = pd.to_datetime(df_week['fecha_orden']).dt.date
            orders_per_day = df_week.groupby('fecha').size().reset_index(name='Pedidos')
            
            st.line_chart(orders_per_day.set_index('fecha'), width='stretch')
        else:
            st.info("📊 No hay suficientes datos para la gráfica")
        
    except Exception as e:
        st.error(f"❌ Error cargando dashboard: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

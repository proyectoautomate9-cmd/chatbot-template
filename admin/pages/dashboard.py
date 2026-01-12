"""
Dashboard con métricas del negocio - Rediseño moderno.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config.database import get_supabase


# ============================================
# CACHED DATA FUNCTIONS (para mejor rendimiento)
# ============================================

@st.cache_data(ttl=60)  # Cache por 60 segundos
def get_orders_data(date_filter: str = None):
    """Obtiene órdenes con cache."""
    supabase = get_supabase()
    query = supabase.table("orders").select("*")
    if date_filter:
        query = query.gte("fecha_orden", date_filter)
    return query.execute().data


@st.cache_data(ttl=60)
def get_users_data(date_filter: str = None):
    """Obtiene usuarios con cache con manejo de errores de esquema."""
    supabase = get_supabase()
    try:
        query = supabase.table("users").select("*")
        if date_filter:
            # Intentar filtrar por created_at, si falla capturamos el error
            query = query.gte("created_at", date_filter)
        return query.execute().data
    except Exception as e:
        # Si falla (ej: columna no existe), traer todo y filtrar en memoria si es posible
        try:
            response = supabase.table("users").select("*").execute()
            data = response.data
            if date_filter and data:
                # Filtrar en Python si existe alguna columna de fecha similar o ignorar
                # Buscamos si existe alguna columna que parezca fecha
                return data
            return data
        except:
            return []


@st.cache_data(ttl=60)
def get_order_items_data():
    """Obtiene items de órdenes con cache."""
    supabase = get_supabase()
    return supabase.table("order_items").select("product_id, cantidad, subtotal, products(nombre)").execute().data


@st.cache_data(ttl=120)
def get_pending_orders_count():
    """Obtiene conteo de órdenes pendientes."""
    supabase = get_supabase()
    return len(supabase.table("orders").select("order_id").eq("estado", "pending").execute().data)


def create_kpi_card(label: str, value: str, change: str = None, change_positive: bool = True, color: str = "primary"):
    """Crea una tarjeta KPI con estilo moderno."""
    change_html = ""
    if change:
        change_class = "positive" if change_positive else "negative"
        arrow = "↑" if change_positive else "↓"
        change_html = f'<p class="kpi-change {change_class}">{arrow} {change}</p>'
    
    return f"""
        <div class="kpi-card {color}">
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
            {change_html}
        </div>
    """


def show_dashboard():
    """Muestra el dashboard principal con métricas."""
    
    supabase = get_supabase()
    
    try:
        # ============================================
        # FETCH DATA
        # ============================================
        today = datetime.now().date()
        first_day_month = today.replace(day=1)
        last_month_start = (first_day_month - timedelta(days=1)).replace(day=1)
        last_month_end = first_day_month - timedelta(days=1)
        
        # Orders this month
        orders_month = supabase.table("orders")\
            .select("*")\
            .gte("fecha_orden", f"{first_day_month}T00:00:00")\
            .execute()
        
        # Orders last month (for comparison)
        orders_last_month = supabase.table("orders")\
            .select("*")\
            .gte("fecha_orden", f"{last_month_start}T00:00:00")\
            .lte("fecha_orden", f"{last_month_end}T23:59:59")\
            .execute()
        
        # Pending orders
        pending_orders = supabase.table("orders")\
            .select("*")\
            .eq("estado", "pending")\
            .execute()
        
        # All users
        all_users = get_users_data()
        
        # User filtering (safe approach)
        def filter_users_by_date(users, start_date):
            if not users: return []
            # Intentar encontrar una columna de fecha (created_at es la estándar)
            date_col = 'created_at' if users and 'created_at' in users[0] else None
            if not date_col:
                # Si no hay columna de fecha, retornamos todo o lista vacía según lógica
                return users
            
            filtered = []
            for u in users:
                u_date = u.get(date_col)
                if u_date and u_date[:10] >= str(start_date):
                    filtered.append(u)
            return filtered

        users_this_month_list = filter_users_by_date(all_users, first_day_month)
        users_last_month_list = filter_users_by_date(all_users, last_month_start)
        # Excluir los de este mes para tener solo los del mes pasado
        users_last_month_list = [u for u in users_last_month_list if u not in users_this_month_list]
        
        # ============================================
        # CALCULATE METRICS
        # ============================================
        
        # Revenue
        revenue_month = sum(o.get('total', 0) for o in orders_month.data)
        revenue_last_month = sum(o.get('total', 0) for o in orders_last_month.data)
        revenue_change = ((revenue_month - revenue_last_month) / revenue_last_month * 100) if revenue_last_month > 0 else 0
        
        # Orders
        total_orders_month = len(orders_month.data)
        total_orders_last_month = len(orders_last_month.data)
        orders_change = ((total_orders_month - total_orders_last_month) / total_orders_last_month * 100) if total_orders_last_month > 0 else 0
        
        # Customers
        new_customers = len(users_this_month_list)
        new_customers_last = len(users_last_month_list)
        customers_change = ((new_customers - new_customers_last) / new_customers_last * 100) if new_customers_last > 0 else 0
        
        # Average order value
        avg_order = revenue_month / total_orders_month if total_orders_month > 0 else 0
        avg_order_last = revenue_last_month / total_orders_last_month if total_orders_last_month > 0 else 0
        avg_change = ((avg_order - avg_order_last) / avg_order_last * 100) if avg_order_last > 0 else 0
        
        # Pending
        total_pending = len(pending_orders.data)
        
        # Total customers
        total_customers = len(all_users)
        
        # ============================================
        # KPI CARDS - ROW 1
        # ============================================
        st.markdown('<h2 class="greeting-header">📊 Resumen del Mes</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Ingresos Mensuales",
                value=f"${revenue_month:,.0f}",
                delta=f"{revenue_change:+.1f}% vs mes ant."
            )
        
        with col2:
            st.metric(
                label="📦 Pedidos Totales",
                value=total_orders_month,
                delta=f"{orders_change:+.1f}% vs mes ant."
            )
        
        with col3:
            st.metric(
                label="👥 Nuevos Clientes",
                value=new_customers,
                delta=f"{customers_change:+.1f}% vs mes ant."
            )
        
        with col4:
            st.metric(
                label="💵 Ticket Promedio",
                value=f"${avg_order:,.0f}",
                delta=f"{avg_change:+.1f}% vs mes ant."
            )
        
        # ============================================
        # KPI CARDS - ROW 2
        # ============================================
        st.markdown("<br>", unsafe_allow_html=True)
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Pending with urgency color
            if total_pending > 5:
                st.error(f"⏳ **{total_pending}** Pendientes")
            elif total_pending > 0:
                st.warning(f"⏳ **{total_pending}** Pendientes")
            else:
                st.success("✅ Sin pendientes")
        
        with col6:
            st.metric(
                label="👤 Clientes Totales",
                value=total_customers
            )
        
        with col7:
            # Top product
            order_items = supabase.table("order_items")\
                .select("product_id, cantidad, products(nombre)")\
                .execute()
            
            if order_items.data:
                product_sales = {}
                for item in order_items.data:
                    prod_name = item.get('products', {}).get('nombre', 'N/A')
                    product_sales[prod_name] = product_sales.get(prod_name, 0) + item.get('cantidad', 0)
                
                if product_sales:
                    top_product = max(product_sales, key=product_sales.get)
                    st.metric(label="🏆 Más Vendido", value=top_product[:20])
                else:
                    st.metric(label="🏆 Más Vendido", value="Sin datos")
            else:
                st.metric(label="🏆 Más Vendido", value="Sin datos")
        
        with col8:
            # Conversion rate (delivered / total)
            delivered = len([o for o in orders_month.data if o.get('estado') == 'delivered'])
            conversion = (delivered / total_orders_month * 100) if total_orders_month > 0 else 0
            st.metric(
                label="✅ Tasa de Entrega",
                value=f"{conversion:.0f}%"
            )
        
        st.markdown("---")
        
        # ============================================
        # CHARTS ROW
        # ============================================
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("### 📈 Ingresos - Últimos 30 días")
            
            # Revenue trend
            last_30_days = datetime.now() - timedelta(days=30)
            orders_30 = supabase.table("orders")\
                .select("total, fecha_orden")\
                .gte("fecha_orden", last_30_days.isoformat())\
                .execute()
            
            if orders_30.data:
                df_revenue = pd.DataFrame(orders_30.data)
                df_revenue['fecha'] = pd.to_datetime(df_revenue['fecha_orden']).dt.date
                daily_revenue = df_revenue.groupby('fecha')['total'].sum().reset_index()
                
                fig = px.area(
                    daily_revenue,
                    x='fecha',
                    y='total',
                    color_discrete_sequence=['#00B4D8']
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_title="",
                    yaxis_title="",
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#F8FAFC", size=14)  # Increased font size
                )
                fig.update_xaxes(showgrid=False, tickfont=dict(color="#CBD5E1", size=12))
                fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color="#CBD5E1", size=12))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No hay datos suficientes para la gráfica")
        
        with chart_col2:
            st.markdown("### 📊 Pedidos por Estado")
            
            # Orders by status
            all_orders = supabase.table("orders")\
                .select("estado")\
                .execute()
            
            if all_orders.data:
                status_counts = {}
                for order in all_orders.data:
                    status = order.get('estado', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                df_status = pd.DataFrame([
                    {"Estado": k, "Cantidad": v} for k, v in status_counts.items()
                ])
                
                colors = {
                    'pending': '#F39C12',
                    'confirmed': '#3498DB',
                    'preparing': '#9B59B6',
                    'ready': '#2ECC71',
                    'delivered': '#27AE60',
                    'cancelled': '#E74C3C'
                }
                
                # Translate status names for the chart
                status_map_es = {
                    'pending': 'Pendiente',
                    'confirmed': 'Confirmado',
                    'preparing': 'Preparando',
                    'ready': 'Listo',
                    'delivered': 'Entregado',
                    'cancelled': 'Cancelado'
                }
                df_status['Estado_ES'] = df_status['Estado'].map(lambda x: status_map_es.get(x, x))

                fig = px.pie(
                    df_status,
                    values='Cantidad',
                    names='Estado_ES',
                    hole=0.5,
                    color='Estado',
                    color_discrete_map=colors
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color="#F8FAFC", size=13)),
                    font=dict(color="#F8FAFC", size=14)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No hay datos suficientes para la gráfica")
        
        st.markdown("---")
        
        # ============================================
        # TOP PRODUCTS & RECENT ORDERS
        # ============================================
        bottom_col1, bottom_col2 = st.columns(2)
        
        with bottom_col1:
            st.markdown("### 🏆 Top 5 Productos")
            
            if order_items.data:
                product_sales = {}
                for item in order_items.data:
                    prod_name = item.get('products', {}).get('nombre', 'N/A')
                    product_sales[prod_name] = product_sales.get(prod_name, 0) + item.get('cantidad', 0)
                
                top_5 = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
                
                if top_5:
                    df_top = pd.DataFrame(top_5, columns=['Producto', 'Vendidos'])
                    df_top = df_top.iloc[::-1]  # Reverse to show top item at the top of chart
                    
                    fig = px.bar(
                        df_top,
                        x='Vendidos',
                        y='Producto',
                        orientation='h',
                        color_discrete_sequence=['#00B4D8']
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=250,
                        xaxis_title="",
                        yaxis_title="",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#F8FAFC", size=14)
                    )
                    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color="#CBD5E1", size=12))
                    fig.update_yaxes(showgrid=False, tickfont=dict(color="#CBD5E1", size=12))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📦 No hay datos de productos")
            else:
                st.info("📦 No hay datos de productos")
        
        with bottom_col2:
            st.markdown("### 📋 Últimos Pedidos")
            
            recent_orders = supabase.table("orders")\
                .select("order_id, estado, total, fecha_orden")\
                .order("fecha_orden", desc=True)\
                .limit(5)\
                .execute()
            
            if recent_orders.data:
                for order in recent_orders.data:
                    # Explicitly define variables from order dict to avoid NameError
                    estado = order.get('estado', 'unknown')
                    fecha = order.get('fecha_orden', '')[:10]
                    total = order.get('total', 0)
                    
                    emoji_dict = {
                        'pending': '🕐',
                        'confirmed': '✅',
                        'preparing': '👨‍🍳',
                        'ready': '📦',
                        'delivered': '✅',
                        'cancelled': '❌'
                    }
                    emoji = emoji_dict.get(estado, '❓')

                    estado_dict_es = {
                        'pending': 'Pendiente',
                        'confirmed': 'Confirmado',
                        'preparing': 'Preparando',
                        'ready': 'Listo',
                        'delivered': 'Entregado',
                        'cancelled': 'Cancelado'
                    }
                    estado_es = estado_dict_es.get(estado, estado)

                    st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 0.75rem 1rem; border-radius: 12px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                            <span style="color: #F8FAFC; font-size: 1.1rem;"><strong>#{order['order_id']}</strong> • {fecha}</span>
                            <span style="color: #CBD5E1; font-size: 1rem;">{emoji} {estado_es} • <strong style="color: #00B4D8; font-size: 1.1rem;">${total:,.0f}</strong></span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📭 No hay pedidos registrados")
        
    except Exception as e:
        st.error(f"❌ Error cargando dashboard: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

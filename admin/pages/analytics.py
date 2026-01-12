"""
Analytics page con métricas avanzadas y exportación.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config.database import get_supabase


def show_analytics():
    """Página de analytics avanzados con diseño mejorado."""
    
    st.markdown('<h1 class="greeting-header">📈 Análisis de Negocio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="greeting-subtitle">Consulta el rendimiento detallado de Milhojaldres</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    supabase = get_supabase()
    
    # ============================================
    # DATE RANGE SELECTOR
    # ============================================
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("##### 📅 Rango de Fechas")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            start_date = st.date_input("Desde", value=datetime.now().date() - timedelta(days=30))
        
        with col2:
            end_date = st.date_input("Hasta", value=datetime.now().date())
        
        with col3:
            quick_range = st.selectbox(
                "Rango rápido",
                ["Personalizado", "Últimos 7 días", "Últimos 30 días", "Este mes", "Mes anterior", "Este año"],
                index=2
            )
            
            if quick_range == "Últimos 7 días":
                start_date = datetime.now().date() - timedelta(days=7)
                end_date = datetime.now().date()
            elif quick_range == "Últimos 30 días":
                start_date = datetime.now().date() - timedelta(days=30)
                end_date = datetime.now().date()
            elif quick_range == "Este mes":
                start_date = datetime.now().date().replace(day=1)
                end_date = datetime.now().date()
            elif quick_range == "Mes anterior":
                first_this_month = datetime.now().date().replace(day=1)
                end_date = first_this_month - timedelta(days=1)
                start_date = end_date.replace(day=1)
            elif quick_range == "Este año":
                start_date = datetime.now().date().replace(month=1, day=1)
                end_date = datetime.now().date()
        st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        # ============================================
        # FETCH DATA FOR RANGE
        # ============================================
        orders = supabase.table("orders")\
            .select("*")\
            .gte("fecha_orden", f"{start_date}T00:00:00")\
            .lte("fecha_orden", f"{end_date}T23:59:59")\
            .execute()
        
        if not orders.data:
            st.warning(f"📊 No hay datos para el rango seleccionado ({start_date} - {end_date})")
            return
        
        df_orders = pd.DataFrame(orders.data)
        df_orders['fecha'] = pd.to_datetime(df_orders['fecha_orden']).dt.date
        df_orders['hora'] = pd.to_datetime(df_orders['fecha_orden']).dt.hour
        df_orders['dia_semana'] = pd.to_datetime(df_orders['fecha_orden']).dt.day_name()
        
        # ============================================
        # SUMMARY METRICS - Use custom cards or improved metrics
        # ============================================
        total_revenue = df_orders['total'].sum()
        total_orders = len(df_orders)
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        delivered = len(df_orders[df_orders['estado'] == 'delivered'])
        conversion_rate = (delivered / total_orders * 100) if total_orders > 0 else 0

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("💰 Ingresos", f"${total_revenue:,.0f}")
        with metric_col2:
            st.metric("📦 Pedidos", total_orders)
        with metric_col3:
            st.metric("💵 Ticket Promedio", f"${avg_order:,.0f}")
        with metric_col4:
            st.metric("✅ Tasa Entrega", f"{conversion_rate:.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================
        # CHARTS ROW 1
        # ============================================
        chart_row1_col1, chart_row1_col2 = st.columns(2)
        
        with chart_row1_col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="chart-title">📈 Ingresos por Día</p>', unsafe_allow_html=True)
            daily = df_orders.groupby('fecha')['total'].sum().reset_index()
            fig = px.line(daily, x='fecha', y='total', markers=True, color_discrete_sequence=['#00B4D8'])
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=300,
                xaxis_title="", yaxis_title="",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#F8FAFC", size=14)
            )
            fig.update_xaxes(showgrid=False, tickfont=dict(color="#CBD5E1", size=12))
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color="#CBD5E1", size=12))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with chart_row1_col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="chart-title">📊 Distribución de Estados</p>', unsafe_allow_html=True)
            status_counts = df_orders['estado'].value_counts().reset_index()
            status_counts.columns = ['estado', 'count']
            colors = {'pending': '#F39C12', 'confirmed': '#3498DB', 'preparing': '#9B59B6', 
                      'ready': '#2ECC71', 'delivered': '#27AE60', 'cancelled': '#E74C3C'}
            status_map_es = {
                'pending': 'Pendiente',
                'confirmed': 'Confirmado',
                'preparing': 'Preparando',
                'ready': 'Listo',
                'delivered': 'Entregado',
                'cancelled': 'Cancelado'
            }
            status_counts['estado_es'] = status_counts['estado'].map(lambda x: status_map_es.get(x, x))
            
            fig = px.pie(status_counts, values='count', names='estado_es', hole=0.4, color='estado', color_discrete_map=colors)
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=300,
                paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#F8FAFC", size=14),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color="#F8FAFC", size=13))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ============================================
        # CHARTS ROW 2
        # ============================================
        chart_row2_col1, chart_row2_col2 = st.columns(2)
        
        with chart_row2_col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="chart-title">📅 Pedidos por Día de la Semana</p>', unsafe_allow_html=True)
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_names_es = {'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mie', 
                          'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sab', 'Sunday': 'Dom'}
            by_day = df_orders['dia_semana'].value_counts().reindex(day_order).reset_index()
            by_day.columns = ['dia', 'count']
            by_day['dia_es'] = by_day['dia'].map(day_names_es)
            fig = px.bar(by_day, x='dia_es', y='count', color_discrete_sequence=['#00B4D8'])
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=250,
                xaxis_title="", yaxis_title="",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#F8FAFC", size=14)
            )
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color="#CBD5E1", size=12))
            fig.update_xaxes(tickfont=dict(color="#CBD5E1", size=12))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with chart_row2_col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="chart-title">⏰ Pedidos por Hora del Día</p>', unsafe_allow_html=True)
            by_hour = df_orders.groupby('hora').size().reset_index(name='count')
            fig = px.area(by_hour, x='hora', y='count', color_discrete_sequence=['#9B59B6'])
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=250,
                xaxis_title="", yaxis_title="",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#F8FAFC", size=14)
            )
            fig.update_xaxes(tickmode='linear', tick0=0, dtick=2, tickfont=dict(color="#CBD5E1", size=12))
            fig.update_yaxes(tickfont=dict(color="#CBD5E1", size=12))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ============================================
        # TOP PRODUCTS & EXPORT
        # ============================================
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<p class="chart-title">🏆 Top Productos y Exportación</p>', unsafe_allow_html=True)
        
        order_ids = [o['order_id'] for o in orders.data]
        if order_ids:
            items = supabase.table("order_items")\
                .select("cantidad, subtotal, products(nombre, categoria)")\
                .in_("order_id", order_ids)\
                .execute()
            
            if items.data:
                product_stats = {}
                for item in items.data:
                    prod = item.get('products', {})
                    name = prod.get('nombre', 'N/A')
                    if name not in product_stats:
                        product_stats[name] = {'cantidad': 0, 'revenue': 0, 'categoria': prod.get('categoria', 'N/A')}
                    product_stats[name]['cantidad'] += item.get('cantidad', 0)
                    product_stats[name]['revenue'] += item.get('subtotal', 0)
                
                df_products = pd.DataFrame([
                    {'Producto': k, 'Unidades': v['cantidad'], 'Ingresos': v['revenue'], 'Categoría': v['categoria']}
                    for k, v in product_stats.items()
                ]).sort_values('Ingresos', ascending=False)
                
                col_p1, col_p2 = st.columns([2, 1])
                with col_p1:
                    st.dataframe(df_products.head(10), hide_index=True, use_container_width=True)
                with col_p2:
                    st.markdown("###### 📥 Descargar Datos")
                    csv_orders = df_orders.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Pedidos (CSV)", csv_orders, f"pedidos_{start_date}.csv", "text/csv", use_container_width=True)
                    
                    df_items_export = pd.DataFrame(items.data)
                    csv_items = df_items_export.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Productos (CSV)", csv_items, f"productos_{start_date}.csv", "text/csv", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error cargando analytics: {e}")
        with st.expander("Ver detalles"):
            import traceback
            st.code(traceback.format_exc())


"""
Sistema de Gestión de Descuentos.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config.database import get_supabase


def show_discounts():
    """Página de gestión de descuentos."""
    
    st.markdown("### 🎟️ Gestión de Descuentos")
    
    supabase = get_supabase()
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Descuentos", 
        "➕ Crear Nuevo", 
        "📈 Estadísticas", 
        "⚙️ Reglas Automáticas"
    ])
    
    # ============================================
    # TAB 1: LISTA DE DESCUENTOS
    # ============================================
    with tab1:
        try:
            discounts = supabase.table("discounts")\
                .select("*")\
                .order("created_at", desc=True)\
                .execute()
            
            if discounts.data:
                # Filtros
                col_filter1, col_filter2 = st.columns(2)
                with col_filter1:
                    filter_type = st.selectbox(
                        "Filtrar por tipo",
                        ["Todos", "massive", "individual", "rule", "seasonal"]
                    )
                with col_filter2:
                    filter_active = st.selectbox(
                        "Estado",
                        ["Todos", "Activos", "Inactivos"]
                    )
                
                filtered = discounts.data
                if filter_type != "Todos":
                    filtered = [d for d in filtered if d.get('type') == filter_type]
                if filter_active == "Activos":
                    filtered = [d for d in filtered if d.get('active')]
                elif filter_active == "Inactivos":
                    filtered = [d for d in filtered if not d.get('active')]
                
                st.markdown(f"**{len(filtered)}** descuentos encontrados")
                st.markdown("---")
                
                for discount in filtered:
                    active_class = "" if discount.get('active') else "inactive"
                    code_display = f"<span class='discount-code'>{discount.get('code', 'AUTO')}</span>" if discount.get('code') else "<span style='color:#6B7280;'>Automático</span>"
                    
                    # Type badge
                    type_colors = {
                        'massive': '#3498DB',
                        'individual': '#9B59B6',
                        'rule': '#2ECC71',
                        'seasonal': '#F39C12'
                    }
                    type_color = type_colors.get(discount.get('type'), '#6B7280')
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        type_labels = {
                            'massive': 'Masivo',
                            'individual': 'Individual',
                            'rule': 'Regla',
                            'seasonal': 'Temporada'
                        }
                        display_label = type_labels.get(discount.get('type'), discount.get('type', 'N/A'))
                        
                        st.markdown(f"""
                            <div class="discount-card {active_class}">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div>
                                        <p style="margin: 0; font-weight: 600; font-size: 1rem;">{discount.get('name', 'Sin nombre')}</p>
                                        <p style="margin: 0.25rem 0 0 0;">{code_display}</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="background: {type_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                                            {display_label}
                                        </span>
                                    </div>
                                </div>
                                <div style="margin-top: 0.75rem; display: flex; gap: 1rem; font-size: 0.875rem; color: #6B7280;">
                                    <span>💰 {discount.get('value', 0)}{'%' if discount.get('discount_type') == 'percentage' else ' COP'}</span>
                                    <span>📊 Usos: {discount.get('current_uses', 0)}/{discount.get('max_uses') or '∞'}</span>
                                    {'<span>🟢 Activo</span>' if discount.get('active') else '<span>⚫ Inactivo</span>'}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{discount['discount_id']}"):
                            st.session_state['editing_discount'] = discount
                            st.rerun()
                    
                    with col3:
                        new_state = not discount.get('active')
                        btn_label = "🔴 Desactivar" if discount.get('active') else "🟢 Activar"
                        if st.button(btn_label, key=f"toggle_{discount['discount_id']}"):
                            supabase.table("discounts")\
                                .update({"active": new_state})\
                                .eq("discount_id", discount['discount_id'])\
                                .execute()
                            st.rerun()
            else:
                st.info("📭 No hay descuentos creados. Usa la pestaña '➕ Crear Nuevo' para agregar uno.")
                
        except Exception as e:
            st.warning(f"⚠️ No se pudo cargar los descuentos. Asegúrate de haber ejecutado el script SQL para crear la tabla.")
            st.error(str(e))
    
    # ============================================
    # TAB 2: CREAR DESCUENTO
    # ============================================
    with tab2:
        st.markdown("#### Crear Nuevo Descuento")
        
        with st.form("create_discount_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nombre del descuento *", placeholder="Ej: Descuento de Navidad")
                discount_type_select = st.selectbox(
                    "Tipo de descuento *",
                    ["massive", "individual", "rule", "seasonal"],
                    format_func=lambda x: {
                        'massive': '🌐 Masivo (todos los clientes)',
                        'individual': '👤 Individual (cliente específico)',
                        'rule': '🔧 Regla automática',
                        'seasonal': '📅 Temporada'
                    }.get(x, x)
                )
                code = st.text_input("Código (opcional)", placeholder="Ej: NAVIDAD2026", help="Deja vacío para descuentos automáticos")
                
            with col2:
                value_type = st.selectbox("Tipo de valor", ["percentage", "fixed"], format_func=lambda x: "Porcentaje (%)" if x == "percentage" else "Monto fijo ($)")
                value = st.number_input("Valor del descuento *", min_value=0.0, help="Ej: 10 para 10% o 5000 para $5,000")
                max_uses = st.number_input("Máximo de usos (0 = ilimitado)", min_value=0, value=0)
            
            st.markdown("---")
            
            col3, col4 = st.columns(2)
            with col3:
                min_order = st.number_input("Monto mínimo de orden ($)", min_value=0, value=0, help="Para reglas automáticas")
            with col4:
                min_qty = st.number_input("Cantidad mínima de productos", min_value=0, value=0)
            
            col5, col6 = st.columns(2)
            with col5:
                start_date = st.date_input("Fecha inicio (opcional)", value=None)
            with col6:
                end_date = st.date_input("Fecha fin (opcional)", value=None)
            
            # Cliente específico para descuentos individuales
            if discount_type_select == "individual":
                try:
                    users = supabase.table("users").select("user_id, nombre, telefono").execute()
                    user_options = {f"{u.get('nombre', 'Sin nombre')} ({u.get('telefono', 'N/A')})": u['user_id'] for u in users.data}
                    selected_user = st.selectbox("Seleccionar cliente", list(user_options.keys()))
                    user_id = user_options.get(selected_user)
                except:
                    user_id = None
                    st.warning("No se pudieron cargar los clientes")
            else:
                user_id = None
            
            submitted = st.form_submit_button("✅ Crear Descuento", use_container_width=True)
            
            if submitted:
                if not name or value <= 0:
                    st.error("Por favor completa los campos requeridos")
                else:
                    try:
                        new_discount = {
                            "name": name,
                            "code": code.upper() if code else None,
                            "type": discount_type_select,
                            "discount_type": value_type,
                            "value": value,
                            "min_order_amount": min_order,
                            "min_quantity": min_qty,
                            "max_uses": max_uses if max_uses > 0 else None,
                            "start_date": start_date.isoformat() if start_date else None,
                            "end_date": end_date.isoformat() if end_date else None,
                            "user_id": user_id,
                            "active": True
                        }
                        
                        supabase.table("discounts").insert(new_discount).execute()
                        st.success("✅ Descuento creado exitosamente!")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error creando descuento: {e}")
    
    # ============================================
    # TAB 3: ESTADÍSTICAS
    # ============================================
    with tab3:
        st.markdown("#### 📊 Estadísticas de Descuentos")
        
        try:
            # Get discount usage stats
            discounts_data = supabase.table("discounts").select("*").execute()
            
            if discounts_data.data:
                total_discounts = len(discounts_data.data)
                active_discounts = len([d for d in discounts_data.data if d.get('active')])
                total_uses = sum(d.get('current_uses', 0) for d in discounts_data.data)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎟️ Total Descuentos", total_discounts)
                with col2:
                    st.metric("🟢 Activos", active_discounts)
                with col3:
                    st.metric("📊 Usos Totales", total_uses)
                st.markdown("---")
                
                # Breakdown by type
                st.markdown("##### Por Tipo")
                type_counts = {}
                for d in discounts_data.data:
                    t = d.get('type', 'unknown')
                    type_counts[t] = type_counts.get(t, 0) + 1
                
                for t, count in type_counts.items():
                    st.write(f"- **{t}**: {count} descuentos")
            else:
                st.info("No hay datos de descuentos para mostrar estadísticas")
                
        except Exception as e:
            st.warning("No se pudieron cargar las estadísticas. Verifica que la tabla existe.")
    
    # ============================================
    # TAB 4: REGLAS AUTOMÁTICAS
    # ============================================
    with tab4:
        st.markdown("#### 🔧 Reglas de Descuento Automático")
        st.info("Los descuentos de tipo 'rule' se aplican automáticamente cuando se cumplen las condiciones.")
        
        st.markdown("""
        **Ejemplos de reglas:**
        - 🛒 Compras mayores a $500,000 → 5% de descuento
        - 📦 Más de 10 productos → 10% de descuento
        - 🆕 Primera compra → 15% de bienvenida
        
        Para crear una regla, ve a la pestaña **'➕ Crear Descuento'** y selecciona tipo **'Regla automática'**.
        """)
        
        # Show existing rules
        try:
            rules = supabase.table("discounts")\
                .select("*")\
                .eq("type", "rule")\
                .execute()
            
            if rules.data:
                st.markdown("---")
                st.markdown("##### Reglas Activas")
                
                for rule in rules.data:
                    status = "🟢" if rule.get('active') else "⚫"
                    condition = []
                    if rule.get('min_order_amount', 0) > 0:
                        condition.append(f"Orden > ${rule['min_order_amount']:,.0f}")
                    if rule.get('min_quantity', 0) > 0:
                        condition.append(f"Cantidad > {rule['min_quantity']}")
                    
                    st.markdown(f"""
                        {status} **{rule['name']}**: {' y '.join(condition) if condition else 'Sin condición'} 
                        → **{rule['value']}{'%' if rule['discount_type'] == 'percentage' else ' COP'} de descuento**
                    """)
            else:
                st.info("No hay reglas automáticas creadas")
                
        except Exception as e:
            st.warning("No se pudieron cargar las reglas")

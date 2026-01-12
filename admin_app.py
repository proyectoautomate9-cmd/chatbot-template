"""
Panel de Administración Web - Milhojaldres Bot
Ejecutar con: streamlit run admin_app.py
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Admin - Milhojaldres",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Carga los estilos CSS personalizados."""
    css_path = os.path.join(os.path.dirname(__file__), "admin", "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_greeting():
    """Retorna un saludo según la hora del día."""
    hour = datetime.now().hour
    if hour < 12:
        return "Buenos días"
    elif hour < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def check_password():
    """Verifica la contraseña del admin - DESHABILITADO."""
    # Autenticación deshabilitada para desarrollo
    st.session_state["password_correct"] = True
    st.session_state["admin_name"] = "Administrador"
    return True


# Cargar estilos CSS
load_css()

if check_password():
    # ============================================
    # SIDEBAR
    # ============================================
    with st.sidebar:
        # Logo and branding
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <span style="font-size: 2.5rem;">🍰</span>
                <h2 style="color: white; margin: 0.5rem 0 0 0; font-weight: 700;">Milhojaldres</h2>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.875rem; margin: 0;">Panel de Administración</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navegación",
            [
                "📊 Dashboard",
                "📦 Pedidos",
                "👥 Clientes",
                "🎟️ Descuentos",
                "📈 Analytics",
                "🔐 Acceso"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Bot status
        st.markdown("""
            <div style="background: rgba(46, 204, 113, 0.1); border-radius: 8px; padding: 0.75rem; border-left: 3px solid #2ECC71;">
                <p style="color: #2ECC71; font-weight: 600; margin: 0; font-size: 0.875rem;">🟢 Bot Online</p>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; margin: 0.25rem 0 0 0;">@milhojaldres_bot</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Logout button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()
    
    # ============================================
    # MAIN CONTENT - GREETING
    # ============================================
    admin_name = st.session_state.get("admin_name", "Admin")
    greeting = get_greeting()
    
    st.markdown(f"""
        <div class="animate-in">
            <p class="greeting-header">{greeting}, {admin_name}! 👋</p>
            <p class="greeting-subtitle">Aquí tienes un resumen de tu negocio</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================
    # LOAD SELECTED PAGE
    # ============================================
    if page == "📊 Dashboard":
        from admin.pages.dashboard import show_dashboard
        show_dashboard()
    
    elif page == "📦 Pedidos":
        from admin.pages.orders import show_orders_management
        show_orders_management()
    
    elif page == "👥 Clientes":
        from admin.pages.customers import show_customers
        show_customers()
    
    elif page == "🎟️ Descuentos":
        from admin.pages.discounts import show_discounts
        show_discounts()
    
    elif page == "📈 Analytics":
        from admin.pages.analytics import show_analytics
        show_analytics()
    
    elif page == "🔐 Acceso":
        from admin.pages.access import show_access_management
        show_access_management()

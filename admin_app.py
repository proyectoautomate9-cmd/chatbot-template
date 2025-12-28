"""
Panel de Administración Web - Milhojaldres Bot
Ejecutar con: streamlit run admin_app.py
"""

import streamlit as st
import os
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


def check_password():
    """Verifica la contraseña del admin."""
    
    def password_entered():
        """Callback cuando se ingresa la contraseña."""
        if st.session_state["password"] == os.getenv("ADMIN_PANEL_PASSWORD", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Panel de Administración - Milhojaldres")
        st.markdown("---")
        st.text_input(
            "Contraseña",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.info("💡 La contraseña está en `.env` como `ADMIN_PANEL_PASSWORD`")
        return False
    
    elif not st.session_state["password_correct"]:
        st.title("🔐 Panel de Administración - Milhojaldres")
        st.markdown("---")
        st.text_input(
            "Contraseña",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("❌ Contraseña incorrecta")
        return False
    
    else:
        return True


if check_password():
    # Sidebar
    st.sidebar.title("🍰 Milhojaldres")
    st.sidebar.markdown("**Panel de Administración**")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "📍 Navegación",
        ["📊 Dashboard", "📦 Gestión de Pedidos"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Estado del Bot:**\n\n"
        "🟢 Online\n\n"
        "📱 Telegram: @milhojaldres_bot"
    )
    
    # Cargar página seleccionada
    if page == "📊 Dashboard":
        from admin.pages.dashboard import show_dashboard
        show_dashboard()
    
    elif page == "📦 Gestión de Pedidos":
        from admin.pages.orders import show_orders_management
        show_orders_management()

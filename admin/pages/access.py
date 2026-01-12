"""
Gestión de Acceso y Usuarios Administradores.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config.database import get_supabase

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        # Fallback - NOT SECURE, only for demo
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    if BCRYPT_AVAILABLE:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    else:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed


def show_access_management():
    """Página de gestión de acceso."""
    
    st.markdown("### 🔐 Gestión de Acceso")
    
    supabase = get_supabase()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "👤 Usuarios Admin",
        "➕ Crear Usuario",
        "📋 Log de Actividad"
    ])
    
    # ============================================
    # TAB 1: ADMIN USERS LIST
    # ============================================
    with tab1:
        st.markdown("#### Usuarios Administradores")
        
        try:
            admins = supabase.table("admin_users")\
                .select("admin_id, email, name, role, active, last_login, created_at")\
                .order("created_at", desc=True)\
                .execute()
            
            if admins.data:
                for admin in admins.data:
                    role = admin.get('role', 'viewer')
                    role_colors = {
                        'super_admin': ('linear-gradient(135deg, #667EEA 0%, #764BA2 100%)', 'white'),
                        'manager': ('#00B4D8', 'white'),
                        'viewer': ('#E5E7EB', '#374151')
                    }
                    bg, color = role_colors.get(role, ('#E5E7EB', '#374151'))
                    
                    status = "🟢" if admin.get('active') else "🔴"
                    last_login = admin.get('last_login', 'Nunca')[:16] if admin.get('last_login') else 'Nunca'
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <p style="margin: 0; font-weight: 600;">{status} {admin.get('name', 'Sin nombre')}</p>
                                        <p style="margin: 0; color: #6B7280; font-size: 0.875rem;">{admin.get('email')}</p>
                                    </div>
                                    <div>
                                        <span style="background: {bg}; color: {color}; padding: 0.25rem 0.75rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600;">{role.upper()}</span>
                                    </div>
                                </div>
                                <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #9CA3AF;">Último acceso: {last_login}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        new_role = st.selectbox(
                            "Rol",
                            ['super_admin', 'manager', 'viewer'],
                            index=['super_admin', 'manager', 'viewer'].index(role),
                            key=f"role_{admin['admin_id']}",
                            label_visibility="collapsed"
                        )
                        if new_role != role:
                            if st.button("💾", key=f"save_role_{admin['admin_id']}"):
                                supabase.table("admin_users")\
                                    .update({"role": new_role})\
                                    .eq("admin_id", admin['admin_id'])\
                                    .execute()
                                st.rerun()
                    
                    with col3:
                        toggle_label = "🔴 Desactivar" if admin.get('active') else "🟢 Activar"
                        if st.button(toggle_label, key=f"toggle_{admin['admin_id']}"):
                            supabase.table("admin_users")\
                                .update({"active": not admin.get('active')})\
                                .eq("admin_id", admin['admin_id'])\
                                .execute()
                            st.rerun()
            else:
                st.info("📭 No hay usuarios administradores. Crea uno en la pestaña '➕ Crear Usuario'.")
                
        except Exception as e:
            st.warning("⚠️ No se pudo cargar los usuarios. Asegúrate de haber ejecutado el script SQL.")
            st.error(str(e))
            
            # Show how to create the table
            with st.expander("📋 Ver SQL para crear la tabla"):
                st.code("""
CREATE TABLE IF NOT EXISTS public.admin_users (
    admin_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',
    active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
                """, language="sql")
    
    # ============================================
    # TAB 2: CREATE ADMIN USER
    # ============================================
    with tab2:
        st.markdown("#### Crear Nuevo Usuario Admin")
        
        if not BCRYPT_AVAILABLE:
            st.warning("⚠️ bcrypt no está instalado. Las contraseñas se guardarán con hash SHA-256 (menos seguro).")
        
        with st.form("create_admin_form"):
            name = st.text_input("Nombre completo *")
            email = st.text_input("Email *", placeholder="admin@ejemplo.com")
            password = st.text_input("Contraseña *", type="password")
            password_confirm = st.text_input("Confirmar contraseña *", type="password")
            
            role = st.selectbox(
                "Rol *",
                ['viewer', 'manager', 'super_admin'],
                format_func=lambda x: {
                    'viewer': '👁️ Viewer - Solo lectura',
                    'manager': '📋 Manager - Pedidos, clientes, descuentos',
                    'super_admin': '👑 Super Admin - Acceso total'
                }.get(x, x)
            )
            
            st.markdown("""
            **Permisos por rol:**
            - **Viewer**: Solo puede ver el dashboard y estadísticas
            - **Manager**: Puede gestionar pedidos, clientes y descuentos
            - **Super Admin**: Acceso total incluyendo gestión de usuarios
            """)
            
            submitted = st.form_submit_button("✅ Crear Usuario", use_container_width=True)
            
            if submitted:
                if not all([name, email, password, password_confirm]):
                    st.error("Por favor completa todos los campos")
                elif password != password_confirm:
                    st.error("Las contraseñas no coinciden")
                elif len(password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    try:
                        password_hash = hash_password(password)
                        
                        supabase.table("admin_users").insert({
                            "email": email,
                            "password_hash": password_hash,
                            "name": name,
                            "role": role,
                            "active": True
                        }).execute()
                        
                        st.success(f"✅ Usuario '{name}' creado exitosamente!")
                        st.balloons()
                        
                    except Exception as e:
                        if "duplicate" in str(e).lower():
                            st.error("Este email ya está registrado")
                        else:
                            st.error(f"Error: {e}")
    
    # ============================================
    # TAB 3: ACTIVITY LOG
    # ============================================
    with tab3:
        st.markdown("#### Log de Actividad")
        
        try:
            logs = supabase.table("admin_activity_log")\
                .select("*, admin_users(name, email)")\
                .order("created_at", desc=True)\
                .limit(50)\
                .execute()
            
            if logs.data:
                # Filter
                action_filter = st.selectbox(
                    "Filtrar por acción",
                    ["Todas"] + list(set(l.get('action', '') for l in logs.data))
                )
                
                filtered_logs = logs.data
                if action_filter != "Todas":
                    filtered_logs = [l for l in filtered_logs if l.get('action') == action_filter]
                
                for log in filtered_logs:
                    admin_info = log.get('admin_users', {})
                    admin_name = admin_info.get('name', 'Sistema')
                    
                    action_icons = {
                        'login': '🔑',
                        'logout': '🚪',
                        'create_discount': '🎟️',
                        'update_order': '📦',
                        'create_user': '👤'
                    }
                    icon = action_icons.get(log.get('action', ''), '📝')
                    
                    st.markdown(f"""
                        <div style="background: white; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.25rem;">{icon}</span>
                                <strong>{log.get('action', 'N/A')}</strong> - {admin_name}
                                {f"<br><small style='color: #6B7280;'>{log.get('details', {})}</small>" if log.get('details') else ''}
                            </div>
                            <small style="color: #9CA3AF;">{log.get('created_at', '')[:16]}</small>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📭 No hay actividad registrada aún")
                
        except Exception as e:
            st.info("📋 El log de actividad estará disponible después de ejecutar el script SQL.")

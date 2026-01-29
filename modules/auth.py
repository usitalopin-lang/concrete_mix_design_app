"""
Módulo de autenticación de usuarios.
Gestiona el inicio de sesión verificando credenciales contra Google Sheets.
Incluye persistencia de sesión mediante cookies para mantener login entre refrescos.
"""

import streamlit as st
import bcrypt
import time
import json
from modules import database
from streamlit_cookies_manager import EncryptedCookieManager

# Inicializar cookie manager (solo una vez)
@st.cache_resource
def get_cookie_manager():
    """Obtiene una instancia del gestor de cookies."""
    return EncryptedCookieManager(
        prefix="concrete_app_",
        password=st.secrets.get("COOKIE_PASSWORD", "default_secret_key_change_in_production")
    )

def restore_session_from_cookies():
    """Restaura la sesión desde cookies si existe."""
    cookies = get_cookie_manager()
    
    if not cookies.ready():
        st.stop()
    
    # Verificar si hay sesión guardada en cookies
    if 'authenticated' in cookies and cookies['authenticated'] == 'true':
        if 'authenticated' not in st.session_state or not st.session_state.get('authenticated'):
            # Restaurar datos de sesión
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = cookies.get('user_email', '')
            st.session_state['user_name'] = cookies.get('user_name', '')

def save_session_to_cookies(email: str, name: str):
    """Guarda la sesión en cookies."""
    cookies = get_cookie_manager()
    cookies['authenticated'] = 'true'
    cookies['user_email'] = email
    cookies['user_name'] = name
    cookies.save()

def clear_session_cookies():
    """Limpia las cookies de sesión."""
    cookies = get_cookie_manager()
    cookies['authenticated'] = 'false'
    cookies['user_email'] = ''
    cookies['user_name'] = ''
    cookies.save()

def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    try:
        # Convertir a bytes si son strings
        if isinstance(password_plano, str):
            password_plano = password_plano.encode('utf-8')
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
            
        return bcrypt.checkpw(password_plano, password_hash)
    except Exception as e:
        st.error(f"Error verificar hash: {e}")
        return False

def generar_hash(password: str) -> str:
    """Genera un hash bcrypt para una contraseña (útil para crear usuarios)."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def login_screen():
    """Muestra la pantalla de inicio de sesión."""
    st.markdown("""
        <style>
            .stApp {
                background-color: #f0f2f6;
            }
            .login-container {
                max-width: 400px;
                margin: 0 auto;
                padding: 40px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            /* Hacer visibles los bordes de los inputs */
            .stTextInput > div > div > input {
                border: 2px solid #d0d0d0 !important;
                border-radius: 5px !important;
                padding: 10px !important;
                background-color: white !important;
            }
            .stTextInput > div > div > input:focus {
                border-color: #1f77b4 !important;
                box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🏗️ Concrete Design</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Inicia sesión para continuar</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico", placeholder="usuario@ejemplo.com", key="login_email")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña", key="login_password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.warning("Ingresa correo y contraseña")
                else:
                    with st.spinner("Verificando..."):
                        usuario = database.obtener_usuario(email)
                        
                        if usuario:
                            # Asumimos que la columna en sheet se llama 'password_hash'
                            hash_almacenado = usuario.get('password_hash', '')
                            if verificar_password(password, hash_almacenado):
                                st.session_state['authenticated'] = True
                                st.session_state['user_email'] = email
                                st.session_state['user_name'] = usuario.get('nombre', email.split('@')[0])
                                
                                # Guardar sesión en cookies para persistencia
                                save_session_to_cookies(email, usuario.get('nombre', email.split('@')[0]))
                                
                                st.success("¡Bienvenido!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta")
                        else:
                            st.error("Usuario no encontrado")

def logout():
    """Cierra la sesión del usuario."""
    st.session_state['authenticated'] = False
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None
    
    # Limpiar cookies
    clear_session_cookies()
    
    st.rerun()

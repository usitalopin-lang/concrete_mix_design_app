"""
Módulo de autenticación de usuarios.
Gestiona el inicio de sesión verificando credenciales contra Google Sheets.
Incluye persistencia de sesión mediante cookies para mantener login entre refrescos.
"""

import streamlit as st
import bcrypt
import time
import json
import hmac
import hashlib
import base64
import datetime
from modules import database
import extra_streamlit_components as stx

# Nombre de la cookie única que guarda la sesión (JSON firmado con HMAC)
SESSION_COOKIE = "concrete_app_session"
SESSION_TIMEOUT = 3600  # 60 minutos de inactividad


def _cookie_secret() -> bytes:
    try:
        secret = st.secrets.get("COOKIE_PASSWORD", "default_secret_key_change_in_production")
    except Exception:
        secret = "default_secret_key_change_in_production"
    return str(secret).encode("utf-8")


def _encode_session(data: dict) -> str:
    """Serializa y firma los datos de sesión (evita que se falsifique la cookie)."""
    payload = base64.urlsafe_b64encode(json.dumps(data).encode("utf-8")).decode("ascii")
    sig = hmac.new(_cookie_secret(), payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _decode_session(value) -> dict | None:
    """Verifica la firma y devuelve los datos de sesión, o None si no es válida."""
    if not value or not isinstance(value, str) or "." not in value:
        return None
    payload, sig = value.rsplit(".", 1)
    expected = hmac.new(_cookie_secret(), payload.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except Exception:
        return None


def get_cookie_manager(refresh: bool = False):
    """
    Obtiene el CookieManager de extra-streamlit-components.
    El componente debe renderizarse una sola vez por ejecución del script
    (si no, Streamlit lanza DuplicateWidgetID). restore_session_from_cookies()
    lo crea con refresh=True al inicio de cada ejecución y el resto lo reutiliza.
    """
    if refresh or '_cookie_manager' not in st.session_state:
        st.session_state['_cookie_manager'] = stx.CookieManager(key="concrete_cookie_manager")
    return st.session_state['_cookie_manager']


def _write_session_cookie(cookies, data: dict, key: str):
    cookies.set(
        SESSION_COOKIE,
        _encode_session(data),
        key=key,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=SESSION_TIMEOUT),
    )


def restore_session_from_cookies():
    """Restaura la sesión desde cookies si existe."""
    try:
        cookies = get_cookie_manager(refresh=True)
    except Exception as e:
        print(f"Warning: CookieManager no disponible ({e})")
        return

    # Tras un logout explícito no restauramos aunque el navegador aún tenga la cookie
    if st.session_state.get('_logged_out'):
        return

    # En la primera ejecución el componente aún no devolvió las cookies (Fail-Open):
    # el usuario simplemente verá el login o se restaurará en el siguiente rerun.
    data = _decode_session(cookies.get(SESSION_COOKIE))
    if not data or not data.get('authenticated'):
        return

    try:
        current_time = time.time()
        session_age = current_time - float(data.get('last_activity', 0))

        # Si la sesión tiene más de 60 minutos, expirar
        if session_age > SESSION_TIMEOUT:
            clear_session_cookies(key="cookie_delete_expired")
            st.session_state['authenticated'] = False
            st.warning("⏱️ Tu sesión expiró por inactividad. Por favor inicia sesión nuevamente.")
            return

        # Sesión válida - restaurar
        if not st.session_state.get('authenticated'):
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = data.get('user_email', '')
            st.session_state['user_name'] = data.get('user_name', '')

        # Renovar timestamp de actividad (como máximo una vez por minuto)
        if session_age > 60:
            data['last_activity'] = current_time
            _write_session_cookie(cookies, data, key="cookie_set_renew")

    except (ValueError, TypeError):
        # Si hay error parseando el timestamp, limpiar sesión
        clear_session_cookies(key="cookie_delete_invalid")


def save_session_to_cookies(email: str, name: str):
    """Guarda la sesión en cookies."""
    # Intentamos guardar en cookies, pero si falla no bloqueamos el login
    try:
        st.session_state.pop('_logged_out', None)
        cookies = get_cookie_manager()
        _write_session_cookie(cookies, {
            'authenticated': True,
            'user_email': email,
            'user_name': name,
            'last_activity': time.time(),
        }, key="cookie_set_login")
    except Exception as e:
        print(f"Warning: Cookies not ready for saving session ({e})")


def clear_session_cookies(key: str = "cookie_delete"):
    """Limpia las cookies de sesión."""
    try:
        cookies = get_cookie_manager()
        if cookies.get(SESSION_COOKIE) is not None:
            cookies.delete(SESSION_COOKIE, key=key)
    except Exception:
        pass

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
    
    # Evitar que la sesión se restaure desde la cookie antes de que el navegador la borre
    st.session_state['_logged_out'] = True

    # Limpiar cookies
    clear_session_cookies(key="cookie_delete_logout")

    # Dar tiempo al componente para borrar la cookie en el navegador antes del rerun
    time.sleep(0.5)
    st.rerun()

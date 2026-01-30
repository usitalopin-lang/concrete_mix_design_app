import streamlit as st
from modules.utils_ui import inicializar_estado, sidebar_user_info
from modules.dashboard import render_dashboard

st.set_page_config(
    page_title="Dashboard | Inteligencia",
    page_icon="📊",
    layout="wide"
)

inicializar_estado()

# Gatekeeper
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes [iniciar sesión](/) en la página principal.")
    st.stop()

sidebar_user_info()

# --- GUÍA DE EXPERTO (Consultoría Técnica) ---
from modules.utils_ui import render_expert_guide
render_expert_guide()
st.markdown("---")

render_dashboard()

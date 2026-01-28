import streamlit as st
from modules.utils_ui import inicializar_estado
from modules.auth import login_screen, logout

st.set_page_config(
    page_title="Mix Design App",
    page_icon="🏠",
    layout="wide"
)

def main():
    inicializar_estado()
    
    st.markdown('<h1 style="text-align: center;">🏗️ Sistema de Diseño de Mezclas</h1>', unsafe_allow_html=True)
    
    # Gatekeeper: Login Check
    if not st.session_state.get('authenticated'):
        # Ocultar sidebar de navegación cuando no hay sesión
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    display: none;
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.info("Inicia sesión para acceder a las herramientas.")
        login_screen()
        return

    # Home Screen Authenticated
    st.success(f"Bienvenido, **{st.session_state.get('user_name', 'Usuario')}**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏗️ Diseño
        Calculadora avanzada Faury-Joisel con optimización granulométrica.
        """)
        st.page_link("pages/1_🏗️_Diseño.py", label="Ir a Diseñar", icon="🏗️")
        
    with col2:
        st.markdown("""
        ### 📊 Analítica
        Dashboard inteligente. Visualiza consumos, resistencias y eficiencia.
        """)
        st.page_link("pages/2_📊_Dashboard.py", label="Ver Dashboard", icon="📊")
        
    with col3:
        st.markdown("""
        ### 📚 Catálogos
        Revisa los materiales disponibles en la base de datos centralizada.
        """)
        st.page_link("pages/3_📚_Catálogos.py", label="Ver Catálogos", icon="📚")

    st.markdown("---")
    if st.button("Cerrar Sesión"):
        logout()

if __name__ == "__main__":
    main()

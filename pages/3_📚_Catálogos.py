import streamlit as st
from modules.utils_ui import inicializar_estado, sidebar_user_info
from modules import catalogs
import pandas as pd

st.set_page_config(
    page_title="Catálogos de Materiales",
    page_icon="📚",
    layout="wide"
)

inicializar_estado()

if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes [iniciar sesión](/) en la página principal.")
    st.stop()

sidebar_user_info()

st.markdown("## 📚 Catálogos de Materiales")
st.info("Estos datos se cargan directamente desde Google Sheets. Contacta al administrador para solicitar cambios.")

tab1, tab2, tab3 = st.tabs(["🏭 Cementos", "🪨 Áridos", "🧪 Aditivos"])

with tab1:
    st.markdown("### Cementos Disponibles")
    cem = catalogs.obtener_cementos()
    st.dataframe(pd.DataFrame(cem), use_container_width=True)

with tab2:
    st.markdown("### Áridos Disponibles")
    ari = catalogs.obtener_aridos()
    # Mostrar granulometrías es complejo en tabla simple, mostramos resumen
    df_ari = pd.DataFrame(ari)
    if not df_ari.empty and 'granulometria' in df_ari.columns:
        df_ari = df_ari.drop(columns=['granulometria']) # Ocultar array largo
    st.dataframe(df_ari, use_container_width=True)

with tab3:
    st.markdown("### Aditivos Disponibles")
    adi = catalogs.obtener_aditivos()
    st.dataframe(pd.DataFrame(adi), use_container_width=True)

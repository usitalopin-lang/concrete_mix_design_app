import streamlit as st
from config.config import DEFAULTS, TAMICES_MM, TAMICES_ASTM
from modules.data_loader import cargar_catalogo_aridos, obtener_arido_por_nombre
from modules.faury_joisel import disenar_mezcla_faury
from modules.shilstone import calcular_shilstone_completo
from modules.graphics import crear_grafico_shilstone_interactivo, crear_grafico_power45_interactivo
from modules.power45 import generar_curva_ideal_power45
from modules import gemini_integration as gemini

st.set_page_config(page_title="Diseño Hormigón", layout="wide")

if 'datos_completos' not in st.session_state: st.session_state.datos_completos = {}
if 'analisis_ia' not in st.session_state: st.session_state.analisis_ia = None

st.title("🏗️ Diseño de Mezclas - Conectado a BD")
df_aridos = cargar_catalogo_aridos()

tab1, tab2, tab3, tab4 = st.tabs(["📝 Entrada Datos", "📊 Resultados", "📈 Gráficos", "🤖 IA"])

with tab1:
    st.subheader("Selección de Materiales (Google Sheets)")
    aridos_seleccionados = []
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Árido 1 (Grueso)")
        nom_a1 = st.selectbox("Catálogo Grueso", df_aridos['Nombre del Árido'].unique(), key="sel_a1")
        if nom_a1: aridos_seleccionados.append(obtener_arido_por_nombre(nom_a1, df_aridos))
    with col2:
        st.markdown("#### Árido 2 (Fino)")
        opciones = df_aridos['Nombre del Árido'].unique()
        nom_a2 = st.selectbox("Catálogo Fino", opciones, key="sel_a2", index=1 if len(opciones)>1 else 0)
        if nom_a2: aridos_seleccionados.append(obtener_arido_por_nombre(nom_a2, df_aridos))

    st.markdown("---")
    if st.button("🔄 Calcular Diseño", type="primary"):
        res_faury = disenar_mezcla_faury(
            DEFAULTS['fc'], 40, 0.1, "Plástica", 19.0, 3100,
            aridos_seleccionados, 2.0, "Sin riesgo", []
        )
        # Shilstone con tamices dinámicos
        res_shil = calcular_shilstone_completo(
            res_faury['granulometria_mezcla'], TAMICES_MM, res_faury['cemento']['cantidad']
        )
        st.session_state.datos_completos = {'faury': res_faury, 'shilstone': res_shil, 'aridos': aridos_seleccionados}
        st.success("Cálculo OK")

with tab3:
    if 'shilstone' in st.session_state.datos_completos:
        res = st.session_state.datos_completos['shilstone']
        st.plotly_chart(crear_grafico_shilstone_interactivo(res['CF'], res['Wadj']), use_container_width=True)
        # Power 45
        mezcla = st.session_state.datos_completos['faury']['granulometria_mezcla']
        _, ideal = generar_curva_ideal_power45(19.0, TAMICES_MM)
        st.plotly_chart(crear_grafico_power45_interactivo(TAMICES_ASTM, TAMICES_MM, mezcla, ideal), use_container_width=True)

with tab4:
    if st.session_state.datos_completos:
        api_key = st.text_input("API Key Gemini", type="password")
        if api_key and st.button("Analizar con IA"):
            res = gemini.analizar_mezcla(st.session_state.datos_completos, api_key=api_key)
            st.session_state.analisis_ia = res['analisis'] if res['exito'] else res['error']
        if st.session_state.analisis_ia: st.markdown(st.session_state.analisis_ia)

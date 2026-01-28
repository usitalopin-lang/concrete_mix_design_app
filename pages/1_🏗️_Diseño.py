import streamlit as st
from modules.utils_ui import inicializar_estado, sidebar_inputs, input_aridos_ui, sidebar_user_info
from config.config import DEFAULTS, TAMICES_MM, TAMICES_ASTM
from modules.calculos import disenar_mezcla_faury, calcular_shilstone_completo
from modules.optimization import optimizar_agregados, generar_curva_ideal_power45, evaluar_gradacion
from modules.charts import (
    crear_grafico_shilstone_interactivo, mostrar_resultados_faury,
    crear_grafico_power45_interactivo, crear_grafico_tarantula_interactivo,
    crear_grafico_haystack_interactivo, crear_grafico_gradaciones_individuales, mostrar_resultados_optimizacion
)
from modules.pdf_generator import generar_descarga_pdf
from modules.gemini_client import seccion_gemini, verificar_conexion
import pandas as pd
import io
from datetime import datetime

st.set_page_config(
    page_title="Diseño de Mezclas",
    page_icon="🏗️",
    layout="wide"
)

# Inicialización
inicializar_estado()

# Gatekeeper simple (Si no hay login en Home, esta página podría redirigir mensaje)
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes iniciar sesión en la página principal.")
    st.stop()

st.markdown("## 🏗️ Diseño de Mezclas de Concreto")

# Sidebar
params = sidebar_inputs()
sidebar_user_info()

# Tabs de Diseño (Simplificado sin Dashboard)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Datos de Entrada",
    "📊 Faury-Joisel",
    "📈 Shilstone",
    "🎯 Optimización",
    "🤖 IA & Reportes"
])

with tab1:
    st.markdown("### Configuración de Materiales")
    aridos = input_aridos_ui()
    st.session_state.aridos_config = aridos
    
    st.markdown("---")
    if st.button("🔄 Calcular Diseño", type="primary", key="btn_calcular"):
        with st.spinner("Calculando diseño..."):
            try:
                # 1. Faury
                res_faury = disenar_mezcla_faury(
                    params['resistencia_fc'], params['desviacion_std'], params['fraccion_def'],
                    params['consistencia'], params['tmn'], params['densidad_cemento'],
                    aridos, params['aire_porcentaje'], params['condicion_exposicion'],
                    params['aditivos_config']
                )
                st.session_state.resultados_faury = res_faury
                
                # 2. Shilstone
                peso_aridos = sum(res_faury['cantidades_kg_m3'].values())
                dsss_arenas = aridos[-1]['DRSSS']
                res_shil = calcular_shilstone_completo(
                    res_faury['granulometria_mezcla'], res_faury['cemento']['cantidad'],
                    peso_aridos, dsss_arenas, res_faury['agua_cemento']['agua_amasado'],
                    params['densidad_cemento'], res_faury['aire']['volumen']
                )
                st.session_state.resultados_shilstone = res_shil
                
                # Guardar Global
                st.session_state.datos_completos = {
                    **params, 'fc': params['resistencia_fc'], 'fd': res_faury['resistencia']['fd_mpa'],
                    'aridos': aridos, 'faury_joisel': res_faury, 'shilstone': res_shil
                }
                st.success("✅ Cálculo completo!")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    if st.session_state.resultados_faury:
        mostrar_resultados_faury(st.session_state.resultados_faury)
    else:
        st.info("Calcula el diseño primero.")

with tab3:
    if st.session_state.resultados_shilstone:
        st.markdown("### Análisis Shilstone")
        res = st.session_state.resultados_shilstone
        c1, c2, c3 = st.columns(3)
        c1.metric("CF", f"{res['CF']:.1f}")
        c2.metric("W", f"{res['W']:.1f}")
        c3.metric("Wadj", f"{res['Wadj']:.1f}")
        
        fig = crear_grafico_shilstone_interactivo(res['CF'], res['Wadj'], res['evaluacion'])
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"**Zona:** {res['evaluacion']['zona']}")
    else:
        st.info("Calcula el diseño primero.")

with tab4:
    st.markdown("### Optimización Granulométrica")
    if st.session_state.aridos_config:
        c1, c2, c3 = st.columns(3)
        p_hay = c1.slider("Peso Haystack", 0.0, 1.0, 0.3)
        p_tar = c2.slider("Peso Tarantula", 0.0, 1.0, 0.3)
        p_shil = c3.slider("Peso Shilstone", 0.0, 1.0, 0.2)
        
        if st.button("🚀 Optimizar Propiedades"):
            try:
                grans = [a['granulometria'] for a in st.session_state.aridos_config]
                res_opt = optimizar_agregados(grans, params['tmn'], len(grans), p_hay, p_tar, p_shil)
                st.session_state.resultados_optimizacion = res_opt
                mostrar_resultados_optimizacion(res_opt, grans, params['tmn'])
            except Exception as e:
                st.error(f"Error optimización: {e}")
    else:
        st.info("Configura áridos primero.")

with tab5:
    if st.session_state.datos_completos:
        seccion_gemini(st.session_state.datos_completos)
        st.markdown("---")
        generar_descarga_pdf(st.session_state.datos_completos, st.session_state.resultados_shilstone)
    else:
        st.info("Calcula diseño primero.")

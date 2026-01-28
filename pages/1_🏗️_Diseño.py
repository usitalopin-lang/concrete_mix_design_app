import streamlit as st
from modules.utils_ui import inicializar_estado, sidebar_inputs, input_aridos_ui, sidebar_user_info
from config.config import DEFAULTS, TAMICES_MM, TAMICES_ASTM
from modules.faury_joisel import disenar_mezcla_faury
from modules.shilstone import calcular_shilstone_completo
from modules.optimization import optimizar_agregados
from modules import gemini_integration as gemini
from modules.power45 import generar_curva_ideal_power45, evaluar_gradacion
from modules.graphics import (
    crear_grafico_shilstone_interactivo, mostrar_resultados_faury,
    crear_grafico_power45_interactivo, crear_grafico_tarantula_interactivo,
    crear_grafico_haystack_interactivo, crear_grafico_gradaciones_individuales, mostrar_resultados_optimizacion
)
from modules.pdf_generator import generar_reporte_pdf
from modules.gemini_integration import verificar_conexion
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
    
    # --- NUEVO: Configuración Avanzada / Magallanes ---
    with st.expander("🛠️ Configuración Avanzada (Magallanes / Experto)", expanded=False):
        st.session_state.modo_avanzado_magallanes = st.checkbox("ACTIVAR Configuración Manual (A/C y Aire)", 
                                                               value=st.session_state.get('modo_avanzado_magallanes', False))
        
        # Calcular recomendados para mostrar como referencia
        # 1. A/C Recomendada
        from modules.faury_joisel import calcular_resistencia_media, obtener_razon_ac, obtener_aire_ocluido
        
        # Necesitamos Fd para saber la A/C teórica
        fd, fd_kg = calcular_resistencia_media(params['resistencia_fc'], params['desviacion_std'], params['fraccion_def'])
        ac_ref = obtener_razon_ac(fd_kg)
        
        # 2. Aire Recomendado
        aire_ref_lt = obtener_aire_ocluido(params['tmn'], params['aire_porcentaje'])
        
        if st.session_state.modo_avanzado_magallanes:
            st.info(f"💡 El Agua se calculará como: Cemento * A/C Manual.")
            
            col_man1, col_man2 = st.columns(2)
            with col_man1:
                st.session_state.input_manual_ac = st.number_input(
                    "Razón A/C Objetivo", 
                    min_value=0.2, max_value=1.0, 
                    value=st.session_state.get('input_manual_ac', 0.45), 
                    step=0.01,
                    help=f"Recomendado por Resistencia: {ac_ref:.2f}"
                )
                st.caption(f"ℹ️ Sugerido (Tablas): **{ac_ref:.2f}**")
                
            with col_man2:
                st.session_state.input_manual_aire = st.number_input(
                    "Aire Ocluido (Litros)", 
                    min_value=0.0, max_value=100.0, 
                    value=st.session_state.get('input_manual_aire', 20.0), 
                    step=1.0,
                    help=f"Recomendado por TMN: {aire_ref_lt:.1f} L"
                )
                st.caption(f"ℹ️ Sugerido (TMN): **{aire_ref_lt:.1f} L**")
    # ----------------------------------------------------

    aridos = input_aridos_ui()
    st.session_state.aridos_config = aridos
    
    st.markdown("---")
    
    # --- NUEVO: Input Proporciones Personalizadas ---
    usar_personalizado = st.toggle("🔧 Usar Proporciones Personalizadas / Optimizadas")
    proporciones_custom = None
    
    if usar_personalizado:
        # Verificar si hay optimización disponible
        opt_available = st.session_state.get('resultados_optimizacion') is not None
        
        col_opt1, col_opt2 = st.columns([1, 2])
        if opt_available:
             with col_opt1:
                if st.button("✨ Cargar desde Optimización"):
                    res_opt = st.session_state.resultados_optimizacion
                    st.session_state.custom_props_val = res_opt['proporciones']
                    st.toast("Proporciones cargadas desde optimizador!")

        # Inputs manuales (sliders)
        num_ar = len(aridos)
        props_init = st.session_state.get('custom_props_val', [100.0/num_ar]*num_ar)
        
        # Ajustar longitud si cambió número de áridos
        if len(props_init) != num_ar:
            props_init = [100.0/num_ar]*num_ar
            
        proporciones_custom = []
        st.caption("Ajusta los porcentajes (deben sumar 100% aprox)")
        
        cols_p = st.columns(num_ar)
        for i in range(num_ar):
            with cols_p[i]:
                 nombre = aridos[i].get('nombre', f'Árido {i+1}')
                 val = st.number_input(f"% {nombre}", 0.0, 100.0, float(props_init[i]), step=0.5, key=f"prop_man_{i}")
                 proporciones_custom.append(val)
        
        # Validar suma
        suma = sum(proporciones_custom)
        if abs(suma - 100.0) > 1.0:
            st.warning(f"⚠️ La suma de proporciones es {suma:.1f}%, debería ser 100%")
    
    # ---------------------------------------------

    if st.button("🔄 Calcular Diseño", type="primary", key="btn_calcular"):
        with st.spinner("Calculando diseño..."):
            try:
                # 1. Faury
                override_ac = None
                override_aire = None
                
                # --- NUEVO: Modo Magallanes / Manual ---
                # Si el usuario quiere forzar A/C o Aire
                # Podríamos poner esto en sidebar o arriba.
                # Lo ponemos en el objeto 'params' si decidimos agregarlo ahí,
                # o lo leemos aqui de inputs nuevos.
                # Para limpieza, usamos variable de session_state o leemos inputs si existen.
                # Aqui simplificamos leyendo de session_state si está configurado
                
                if st.session_state.get('modo_avanzado_magallanes'):
                    override_ac = st.session_state.get('input_manual_ac')
                    override_aire = st.session_state.get('input_manual_aire')
                
                res_faury = disenar_mezcla_faury(
                    params['resistencia_fc'], params['desviacion_std'], params['fraccion_def'],
                    params['consistencia'], params['tmn'], params['densidad_cemento'],
                    aridos, params['aire_porcentaje'], params['condicion_exposicion'],
                    params['aditivos_config'],
                    proporciones_personalizadas=proporciones_custom,
                    manual_ac=override_ac,
                    manual_aire_litros=override_aire
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
                # Validar que todos los áridos tengan granulometría como lista
                grans = []
                for a in st.session_state.aridos_config:
                    gran = a.get('granulometria', [])
                    if not isinstance(gran, list):
                        st.error(f"❌ Error: La granulometría del árido '{a.get('nombre', 'desconocido')}' no es válida. Debe ser una lista de valores.")
                        st.stop()
                    if len(gran) != 12:
                        st.error(f"❌ Error: La granulometría del árido '{a.get('nombre', 'desconocido')}' debe tener exactamente 12 valores (tiene {len(gran)}).")
                        st.stop()
                    grans.append(gran)
                
                res_opt = optimizar_agregados(
                    granulometrias=grans,
                    tmn=params['tmn'],
                    num_agregados=len(grans),
                    peso_haystack=p_hay,
                    peso_tarantula=p_tar,
                    peso_shilstone=p_shil
                )
                st.session_state.resultados_optimizacion = res_opt
                mostrar_resultados_optimizacion(res_opt, grans, params['tmn'])
            except Exception as e:
                st.error(f"Error optimización: {e}")
                import traceback
                st.code(traceback.format_exc())
    else:
        st.info("Configura áridos primero.")

with tab5:
    if st.session_state.datos_completos:
        st.markdown("### 🤖 Consultor IA (Gemini)")
        
        # Verificar API Key
        api_key = gemini.obtener_api_key()
        
        if not api_key:
            st.warning("⚠️ Configura tu API Key para activar el análisis.")
            st.markdown("Agrega `GOOGLE_API_KEY` en `secrets.toml` o ingrésala abajo:")
            user_key = st.text_input("API Key", type="password", label_visibility="collapsed")
            if user_key:
                api_key = user_key
        
        if api_key:
            col_ia_1, col_ia_2 = st.columns([1, 3])
            with col_ia_1:
                analizar_btn = st.button("🧠 Analizar Diseño", type="primary", use_container_width=True)
            
            if analizar_btn:
                with st.status("🤖 Gemini está analizando tu mezcla...", expanded=True) as status:
                    st.write("Interpretando curvas granulométricas...")
                    st.write("Evaluando parámetros de resistencia...")
                    resultado = gemini.analizar_mezcla(st.session_state.datos_completos, api_key=api_key)
                    
                    if resultado['exito']:
                        st.session_state.analisis_ia = resultado['analisis']
                        status.update(label="✅ Análisis Completado", state="complete", expanded=False)
                    else:
                        st.error(f"Error: {resultado['error']}")
                        status.update(label="❌ Error en el análisis", state="error", expanded=True)
            
            # Mostrar resultado con diseño profesional
            if 'analisis_ia' in st.session_state and st.session_state.analisis_ia:
                with st.container(border=True):
                    st.markdown("#### 💡 Reporte del Consultor Experto")
                    st.markdown(st.session_state.analisis_ia)
                    
                    st.markdown("---")
                    if st.button("🗑️ Limpiar Reporte"):
                        del st.session_state.analisis_ia
                        st.rerun()
                with st.spinner("Analizando mezcla con Gemini AI..."):
                    resultado = gemini.analizar_mezcla(st.session_state.datos_completos, api_key=api_key)
                    
                    if resultado['exito']:
                        st.session_state.analisis_ia = resultado['analisis']
                    else:
                        st.error(f"Error en análisis: {resultado['error']}")
            
            # Mostrar resultado si existe en sesión
            if 'analisis_ia' in st.session_state and st.session_state.analisis_ia:
                st.markdown("#### 💡 Análisis y Recomendaciones")
                st.markdown(st.session_state.analisis_ia)
                
                # Botón de limpiar análisis
                if st.button("Limpiar Análisis"):
                    del st.session_state.analisis_ia
                    st.rerun()
        else:
            st.info("ℹ️ Configura tu API Key para activar el análisis inteligente.")

        st.markdown("---")
        
        # Placeholder para vista datos
        with st.expander("📋 Vista Previa de Datos Técnicos (JSON)"):
            st.json(st.session_state.datos_completos)
        
        st.markdown("---")
        st.markdown("### 📄 Exportar Reporte")
        if st.button("📥 Generar PDF", type="primary"):
            try:
                pdf_bytes = generar_reporte_pdf(st.session_state.datos_completos)
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"reporte_diseno_{st.session_state.datos_completos.get('proyecto', {}).get('nombre', 'proyecto')}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF generado correctamente")
            except Exception as e:
                st.error(f"Error generando PDF: {e}")
    else:
        st.info("Calcula diseño primero.")

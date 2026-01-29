import streamlit as st
from config.config import TAMICES_MM, TAMICES_ASTM
from modules.utils_ui import inicializar_estado, sidebar_inputs, sidebar_user_info, input_aridos_ui
from modules.faury_joisel import disenar_mezcla_faury
from modules.shilstone import calcular_shilstone_completo
from modules.graphics import (
    crear_grafico_shilstone_interactivo, crear_grafico_power45_interactivo,
    crear_grafico_tarantula_interactivo, crear_grafico_haystack_interactivo
)
from modules.power45 import generar_curva_ideal_power45
from modules.optimization import optimizar_agregados
from modules import gemini_integration as gemini
from modules.pdf_generator import generar_reporte_pdf
import json
from datetime import datetime

st.set_page_config(page_title="Diseño Hormigón", layout="wide")

inicializar_estado()

# Gatekeeper de autenticación
if not st.session_state.get('authenticated'):
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    st.warning("⚠️ Debes iniciar sesión en la página principal.")
    st.stop()

# Sidebar con todos los inputs
inputs = sidebar_inputs()
sidebar_user_info()

st.title("🏗️ Diseño de Mezclas de Concreto")

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Entrada Datos", 
    "📊 Resultados", 
    "📈 Gráficos", 
    "✨ Optimización (Iowa)", 
    "🤖 IA"
])

with tab1:
    st.markdown("### 🪨 Configuración de Áridos")
    aridos = input_aridos_ui()
    
    st.markdown("---")
    
    if st.button("🔄 Calcular Diseño", type="primary", use_container_width=True):
        if len(aridos) < 2:
            st.error("❌ Debes configurar al menos 2 áridos")
        else:
            with st.spinner("Calculando diseño Faury-Joisel..."):
                # Diseño Faury-Joisel
                resultado_faury = disenar_mezcla_faury(
                    resistencia_fc=inputs['resistencia_fc'],
                    desviacion_std=inputs['desviacion_std'],
                    fraccion_def=inputs['fraccion_def'],
                    consistencia=inputs['consistencia'],
                    tmn=inputs['tmn'],
                    densidad_cemento=inputs['densidad_cemento'],
                    aridos=aridos,
                    aire_porcentaje=inputs['aire_porcentaje'],
                    condicion_exposicion=inputs['condicion_exposicion'],
                    aditivos_config=inputs['aditivos_config']
                )
                
                # Análisis Shilstone
                # Análisis Shilstone - Preparación de datos correctos
                
                # Calcular peso total de áridos y densidad SSS de arena representativa
                cantidades = resultado_faury['cantidades_kg_m3']
                peso_grava = cantidades.get('grava', 0)
                peso_arena = cantidades.get('arena', 0)
                peso_aridos_total = peso_grava + peso_arena
                
                # Densidad promedio ponderada si hay múltiples arenas, o tomar la primera
                dsss_arena = 2650 # Valor default seguro
                for a in aridos:
                    if a['tipo'] != 'Grueso':
                        dsss_arena = a['DRSSS']
                        break

                resultado_shilstone = calcular_shilstone_completo(
                    granulometria_mezcla=resultado_faury['granulometria_mezcla'],
                    cemento=resultado_faury['cemento']['cantidad'],
                    peso_aridos_total=peso_aridos_total,
                    dsss_arena=dsss_arena,
                    agua_neta=resultado_faury['agua_cemento']['agua_total'],
                    densidad_cemento=resultado_faury['cemento']['densidad'],
                    aditivos=resultado_faury.get('volumen_aditivos', 0),
                    aire=resultado_faury['aire']['volumen']
                )
                
                # Guardar en session_state
                st.session_state.datos_completos = {
                    **inputs,
                    'aridos': aridos,
                    'faury_joisel': resultado_faury,
                    'shilstone': resultado_shilstone
                }
                
                st.success("✅ Diseño calculado exitosamente!")
                st.balloons()

with tab2:
    if not st.session_state.datos_completos:
        st.info("👈 Configura los parámetros en la pestaña 'Entrada Datos' y presiona 'Calcular Diseño'")
    else:
        datos = st.session_state.datos_completos
        faury = datos['faury_joisel']
        shil = datos['shilstone']
        
        st.markdown("## 📋 Resumen del Diseño")
        
        # KPIs principales
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Cemento", f"{faury['cemento']['cantidad']:.1f} kg/m³")
        col2.metric("Agua Total", f"{faury['agua_cemento']['agua_total']:.1f} L/m³")
        col3.metric("Razón A/C", f"{faury['agua_cemento']['razon']:.3f}")
        col4.metric("Shilstone CF", f"{shil['CF']:.1f}")
        
        st.markdown("---")
        
        # Dosificación
        st.markdown("### 🧮 Dosificación por m³")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**Materiales Cementantes**")
            st.write(f"- Cemento: **{faury['cemento']['cantidad']:.2f} kg**")
            st.write(f"- Agua de amasado: **{faury['agua_cemento']['agua_amasado']:.2f} L**")
            st.write(f"- Agua total: **{faury['agua_cemento']['agua_total']:.2f} L**")
            
        with col_b:
            st.markdown("**Agregados**")
            # Filtrar áridos desde cantidades_kg_m3
            for material, cantidad in faury['cantidades_kg_m3'].items():
                if material not in ['cemento', 'agua', 'aire', 'aditivo']:
                     st.write(f"- {material.capitalize()}: **{cantidad:.2f} kg**")
        
        # Botón PDF
        st.markdown("---")
        if st.button("📄 Generar Informe PDF"):
            pdf_bytes = generar_reporte_pdf(datos)
            st.download_button(
                "⬇️ Descargar PDF",
                pdf_bytes,
                file_name=f"Informe_Diseño_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
        
        # Botón JSON
        json_data = json.dumps(datos, default=str, indent=2)
        st.download_button(
            "💾 Guardar JSON Local",
            json_data,
            file_name=f"{inputs['nombre_archivo_local']}.json",
            mime="application/json"
        )

with tab3:
    if not st.session_state.datos_completos:
        st.info("Calcula primero un diseño en la pestaña 'Entrada Datos'")
    else:
        datos = st.session_state.datos_completos
        shil = datos['shilstone']
        faury = datos['faury_joisel']
        
        st.markdown("### 📊 Análisis Granulométrico")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### Diagrama Shilstone")
            fig_shil = crear_grafico_shilstone_interactivo(shil['CF'], shil['Wadj'], shil['evaluacion'])
            st.plotly_chart(fig_shil, use_container_width=True)
            
            # Mostrar evaluación texto
            st.info(f"**Zona:** {shil['evaluacion']['zona']}\n\n{shil['evaluacion']['descripcion']}")
        
        with col_g2:
            st.markdown("#### Curva Power 0.45")
            
            # Preparar datos power45
            from modules.power45 import generar_curva_ideal_power45, calcular_error_power45, TAMICES_POWER45
            ideal_curve, _ = generar_curva_ideal_power45(tmn=inputs['tmn'])
            real_curve = faury['granulometria_mezcla']
            
            # Asegurar longitud igual
            min_len = min(len(ideal_curve), len(real_curve))
            rmse = calcular_error_power45(real_curve[:min_len], ideal_curve[:min_len])
            
            from config.config import TAMICES_ASTM 
            # TAMICES_ASTM puede tener longitud diferente, ajustar
            nombres = TAMICES_ASTM[:min_len]
            # Calcular valores X elevados a 0.45 como espera el gráfico
            x_vals = [t**0.45 for t in TAMICES_POWER45[:min_len]]
            
            fig_p45 = crear_grafico_power45_interactivo(
                tamices_nombres=nombres,
                tamices_power=x_vals,
                ideal_vals=ideal_curve[:min_len],
                real_vals=real_curve[:min_len],
                rmse=rmse
            )
            st.plotly_chart(fig_p45, use_container_width=True)

with tab4:
    st.markdown("### 🧬 Optimización Matemática (Iowa Method)")
    
    if not st.session_state.datos_completos or 'aridos' not in st.session_state.datos_completos:
        st.info("Calcula primero un diseño en la pestaña 'Entrada Datos'")
    else:
        # Usar datos VIVOS del sidebar (aridos) en lugar de los guardados en el último cálculo
        # Esto permite optimizar sin tener que calcular Faury primero si solo se quiere jugar con áridos
        grans = [a['granulometria'] for a in aridos]
        
        col_opt1, col_opt2 = st.columns([1, 2])
        
        with col_opt1:
            # Validación de datos antes de optimizar
            datos_validos = True
            for i, g in enumerate(grans):
                if sum(g) == 0:
                    st.warning(f"⚠️ El Árido {i+1} no tiene datos granulométricos (suma=0).")
                    datos_validos = False
            
            st.info(f"Optimizando {len(aridos)} áridos...")
            
            if st.button("🚀 Ejecutar Optimización Multi-objetivo", disabled=not datos_validos, help="Requiere datos de granulometría válidos en todos los áridos"):
                with st.spinner("Busca la mejor combinación matemática..."):
                    res_opt = optimizar_agregados(grans, tmn=st.session_state.datos_completos['tmn'])
                    if res_opt['exito']:
                        st.session_state.res_opt = res_opt
                        
                        # Interpretación Experta del Error (RSS/RMSE)
                        error_val = res_opt['error_total']
                        
                        if error_val < 500:
                            st.success(f"✅ **Ajuste Excelente** (Desviación: {error_val:.1f})")
                        elif error_val < 2000:
                            st.info(f"ℹ️ **Ajuste Aceptable** (Desviación: {error_val:.1f})")
                        else:
                            st.warning(f"⚠️ **Ajuste Pobre** (Desviación: {error_val:.1f})")
                            st.markdown("""
                                <small>La curva combinada está muy lejos de la ideal. 
                                Es posible que tus áridos sean "discontinuos" (falta tamaño intermedio).
                                **Sugerencia:** Prueba agregar un tercer árido de tamaño intermedio.</small>
                            """, unsafe_allow_html=True)
                            
                    else:
                        st.error("❌ No se pudo converger a una solución.")
        
        if st.session_state.res_opt:
            res = st.session_state.res_opt
            
            # Formatear proporciones bonito
            props_str = ", ".join([f"Árido {i+1}: **{p:.1f}%**" for i, p in enumerate(res['proporciones'])])
            st.markdown(f"**Proporciones Sugeridas:** {props_str}")
            
            # Gráficos Iowa Suite
            tab_p45, tab_tar, tab_hay, tab_shil = st.tabs(["Power 45", "Tarantula", "Haystack", "Shilstone"])
            
            with tab_p45:
                # Datos para P45 Optimizado
                from modules.power45 import TAMICES_POWER45, calcular_error_power45
                tamices_astm_nombres = TAMICES_ASTM[:len(res['curva_ideal'])]
                x_vals_opt = [t**0.45 for t in TAMICES_POWER45[:len(res['curva_ideal'])]]
                rmse_opt = calcular_error_power45(res['mezcla_granulometria'], res['curva_ideal'])

                fig = crear_grafico_power45_interactivo(
                    tamices_nombres=tamices_astm_nombres,
                    tamices_power=x_vals_opt,
                    ideal_vals=res['curva_ideal'],
                    real_vals=res['mezcla_granulometria'],
                    rmse=rmse_opt
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab_tar:
                tmn_val = st.session_state.datos_completos.get('tmn', 25.0)
                fig = crear_grafico_tarantula_interactivo(TAMICES_ASTM, res['mezcla_retenido'], tmn_val)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab_hay:
                fig = crear_grafico_haystack_interactivo(TAMICES_ASTM, res['mezcla_retenido'])
                st.plotly_chart(fig, use_container_width=True)
            
            with tab_shil:
                sf = res['shilstone_factors']
                # Crear evaluación 'dummy' mínima para que la función gráfica funcione
                eval_dummy = {'zona': 'N/A', 'descripcion': 'Optimización', 'calidad': 'N/A'}
                fig = crear_grafico_shilstone_interactivo(sf['cf'], sf['wf'], eval_dummy)
                st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.markdown("### 🤖 Análisis con IA (Gemini)")
    
    if not st.session_state.datos_completos:
        st.info("Calcula primero un diseño en la pestaña 'Entrada Datos'")
    else:
        api_key = st.text_input("API Key Gemini", type="password", help="Ingresa tu API key de Google Gemini")
        
        if api_key and st.button("✨ Analizar con IA"):
            with st.spinner("Analizando con Gemini..."):
                resultado = gemini.analizar_mezcla(st.session_state.datos_completos, api_key=api_key)
                if resultado['exito']:
                    st.session_state.analisis_ia = resultado['analisis']
                    st.success("✅ Análisis completado")
                else:
                    st.error(f"❌ Error: {resultado['error']}")
        
        if st.session_state.analisis_ia:
            st.markdown("#### 📝 Análisis del Diseño")
            st.markdown(st.session_state.analisis_ia)

import streamlit as st
from config.config import TAMICES_MM, TAMICES_ASTM
from modules.utils_ui import inicializar_estado, sidebar_inputs, sidebar_user_info, input_aridos_ui
from modules.faury_joisel import disenar_mezcla_faury
from modules.shilstone import calcular_shilstone_completo
from modules.graphics import (
    crear_grafico_shilstone_interactivo, crear_grafico_power45_interactivo,
    crear_grafico_tarantula_interactivo, crear_grafico_haystack_interactivo,
    crear_grafico_nsw, crear_grafico_illinois
)
from modules.power45 import generar_curva_ideal_power45
from modules.optimization import optimizar_agregados, PERFILES_ADN, calcular_pesos_desde_matriz
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
    st.warning("⚠️ Debes [iniciar sesión](/) en la página principal.")
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
                    aire_porcentaje=inputs.get('aire_porcentaje', 0), # Backward legacy
                    condicion_exposicion=inputs['condicion_exposicion'],
                    aditivos_config=inputs['aditivos_config'],
                    # NUEVOS ARGS MAGALLANES
                    manual_ac=inputs.get('razon_ac_manual'),
                    manual_aire_litros=inputs.get('aire_litros_manual')
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
            
            # Preparar densidades para corrección volumétrica
            densidades_opt = []
            for a in aridos:
                d = a.get('Densidad_Real', 0)
                if d <= 0: d = a.get('Densidad_SSS', 0)
                if d <= 0: d = 2.65
                densidades_opt.append(float(d))

            # --- CONFIGURACIÓN DE PESOS (ADN DE LA MEZCLA) ---
            st.markdown("#### 🧬 Carácter de la Mezcla (DNA)")
            
            opciones_adn = list(PERFILES_ADN.keys()) + ["🗺️ Mapa de Consistencia", "⚙️ Personalizado (Manual)"]
            estrategia = st.radio(
                "Selecciona la Estrategia de Optimización:",
                opciones_adn,
                index=0,
                horizontal=True,
                help="Define qué criterio matemático tendrá más peso en la búsqueda del diseño óptimo."
            )
            
            pesos_finales = {}
            
            if estrategia in PERFILES_ADN:
                config = PERFILES_ADN[estrategia]
                st.caption(f"{config['icon']} **{estrategia}**: {config['desc']}")
                pesos_finales = {
                    'peso_haystack': config['haystack'],
                    'peso_tarantula': config['tarantula'],
                    'peso_shilstone': config['shilstone']
                }
            
            elif estrategia == "🗺️ Mapa de Consistencia":
                st.caption("📍 Mueve los controles para posicionar el 'Punto de Diseño' en la matriz.")
                col_mat1, col_mat2 = st.columns([1, 1])
                with col_mat1:
                    x_trab = st.slider("Trabajabilidad (Shilstone)", 0.0, 1.0, 0.5, 0.1, help="Más a la derecha = Mejor para bombeo")
                    y_coh = st.slider("Cohesión (Tarantula)", 0.0, 1.0, 0.5, 0.1, help="Más arriba = Menos segregación")
                
                with col_mat2:
                    # Gráfico 2D visual del punto
                    import plotly.graph_objects as go
                    fig_mat = go.Figure()
                    # Dibujar cuadrantes
                    fig_mat.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="gray")
                    fig_mat.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="gray")
                    # El punto rojo (ADN)
                    fig_mat.add_trace(go.Scatter(
                        x=[x_trab], y=[y_coh], 
                        mode='markers+text',
                        marker=dict(size=25, color='red', symbol='cross', line=dict(width=2, color='darkred')),
                        name="ADN Elegido"
                    ))
                    fig_mat.update_layout(
                        xaxis=dict(title="Trabajabilidad →", range=[0, 1], showgrid=False),
                        yaxis=dict(title="Cohesión ↑", range=[0, 1], showgrid=False),
                        width=300, height=300, margin=dict(l=40, r=20, t=20, b=40),
                        showlegend=False,
                        plot_bgcolor='white'
                    )
                    st.plotly_chart(fig_mat, use_container_width=False, config={'displayModeBar': False})
                
                pesos_mat = calcular_pesos_desde_matriz(x_trab, y_coh)
                pesos_finales = {
                    'peso_haystack': pesos_mat['haystack'],
                    'peso_tarantula': pesos_mat['tarantula'],
                    'peso_shilstone': pesos_mat['shilstone']
                }

            elif estrategia == "⚙️ Personalizado (Manual)":
                st.caption("🛠️ Ajuste fino de pesos matemáticos (Modo Experto)")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    w_haystack = st.slider("Importancia Haystack", 0.0, 1.0, 0.25)
                    w_tarantula = st.slider("Importancia Tarantula", 0.0, 1.0, 0.25)
                with col_m2:
                    w_shilstone = st.slider("Importancia Shilstone", 0.0, 1.0, 0.25)
                    st.info("El peso de Power 45 se ajusta automáticamente.")
                
                pesos_finales = {
                    'peso_haystack': w_haystack,
                    'peso_tarantula': w_tarantula,
                    'peso_shilstone': w_shilstone
                }

            st.divider()

            if st.button("🚀 Ejecutar Optimización de ADN", disabled=not datos_validos):
                with st.spinner("Buscando la armonía perfecta entre áridos..."):
                    res_opt = optimizar_agregados(
                        grans, 
                        tmn=st.session_state.datos_completos['tmn'],
                        densidades=densidades_opt,
                        **pesos_finales
                    )
                    if res_opt['exito']:
                        st.session_state.res_opt = res_opt
                        # Interpretación Experta del Error
                        error_val = res_opt['error_total']
                        if error_val < 500:
                            st.success(f"✅ **Ajuste Excelente** (Desviación: {error_val:.1f})")
                        elif error_val < 2000:
                            st.info(f"ℹ️ **Ajuste Aceptable** (Desviación: {error_val:.1f})")
                        else:
                            st.warning(f"⚠️ **Ajuste Pobre** (Desviación: {error_val:.1f})")
                            st.markdown("<small>La curva combinada está muy lejos de la ideal. Prueba agregar un tercer árido.</small>", unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {res_opt.get('mensaje', 'No se pudo converger a una solución.')}")
        
        if st.session_state.res_opt:
            res = st.session_state.res_opt
            
            # Formatear proporciones bonito
            props_str = ", ".join([f"Árido {i+1}: **{p:.1f}%**" for i, p in enumerate(res['proporciones'])])
            st.markdown(f"**Proporciones Sugeridas:** {props_str}")
            
            # Gráficos Iowa Suite + Normativos
            tab_p45, tab_tar, tab_hay, tab_shil, tab_c33, tab_nsw, tab_il = st.tabs(["Power 45", "Tarantula", "Haystack", "Shilstone", "C33 & Individual", "NSW", "Illinois Tollway"])
            
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
                eval_dummy = {'zona': 'N/A', 'descripcion': 'Optimización', 'calidad': 'N/A'}
                fig = crear_grafico_shilstone_interactivo(sf['cf'], sf['wf'], eval_dummy)
                st.plotly_chart(fig, use_container_width=True)

            with tab_c33:
                # Datos individuales y C33 ...
                aridos_data_chart = []
                for i, a in enumerate(aridos):
                    nombre = a.get('Nombre', f'Árido {i+1}')
                    g = grans[i]
                    if len(g) < len(TAMICES_ASTM): g = g + [0]*(len(TAMICES_ASTM)-len(g))
                    aridos_data_chart.append({'nombre': nombre, 'granulometria': g[:len(TAMICES_ASTM)]})
                
                mezcla_comb = res['mezcla_granulometria']
                if len(mezcla_comb) < len(TAMICES_ASTM): mezcla_comb = mezcla_comb + [0]*(len(TAMICES_ASTM)-len(mezcla_comb))
                
                fig = crear_grafico_individual_combinado(TAMICES_ASTM, aridos_data_chart, mezcla_comb[:len(TAMICES_ASTM)])
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("ℹ️ ¿Qué es ASTM C33 (Sand)?"):
                    st.markdown("""
                    **ASTM C33 - Standard Specification for Concrete Aggregates**
                    ... (Ver descripción anterior)
                    """)

            with tab_nsw:
                # Datos para NSW
                if len(res['mezcla_granulometria']) < len(TAMICES_ASTM):
                    m = res['mezcla_granulometria'] + [0]*(len(TAMICES_ASTM)-len(res['mezcla_granulometria']))
                else: m = res['mezcla_granulometria']
                
                fig = crear_grafico_nsw(TAMICES_ASTM, m[:len(TAMICES_ASTM)])
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("ℹ️ ¿Qué es NSW?"):
                    st.markdown("""
                    **NSW (New South Wales) - RTA T306 Specification**
                    ... (Ver descripción anterior)
                    """)
                    
            with tab_il:
                # Datos para Illinois
                if len(res['mezcla_granulometria']) < len(TAMICES_ASTM):
                    m = res['mezcla_granulometria'] + [0]*(len(TAMICES_ASTM)-len(res['mezcla_granulometria']))
                else: m = res['mezcla_granulometria']
                
                fig = crear_grafico_illinois(TAMICES_ASTM, m[:len(TAMICES_ASTM)])
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("ℹ️ ¿Qué es Illinois Tollway?"):
                    st.markdown("""
                    **Illinois Tollway - Performance Based Specs**
                    
                    Es una especificación famosa por optimizar mezclas para **Pavimentos de Hormigón** (especialmente colocación con moldaje deslizante o "Slipform").
                    *   Busca una trabajabilidad perfecta y alta densidad para resistir el vibrado sin segregarse.
                    *   Si trabajas en pavimentos o pisos industriales, esta curva es una excelente referencia.
                    """)

with tab5:
    st.markdown("### 🤖 Análisis con IA (Gemini)")
    
    if not st.session_state.datos_completos:
        st.info("Calcula primero un diseño en la pestaña 'Entrada Datos'")
    else:
        # Intentar cargar desde secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        
        if not api_key:
             api_key = st.text_input("API Key Gemini", type="password", help="No detectada en secrets.toml")
        
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

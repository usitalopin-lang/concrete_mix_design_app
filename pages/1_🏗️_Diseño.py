import streamlit as st
from config import TAMICES_MM, TAMICES_ASTM
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
            
            from config import TAMICES_ASTM 
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
        
        grans = [a['granulometria'] for a in aridos]
        
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
        
        # Espaciador
        st.write("")

        if estrategia in PERFILES_ADN:
            config = PERFILES_ADN[estrategia]
            st.info(f"**Estrategia {estrategia}**: {config['desc']}")
            pesos_finales = {
                'peso_haystack': config['haystack'],
                'peso_tarantula': config['tarantula'],
                'peso_shilstone': config['shilstone']
            }
        
        elif estrategia == "🗺️ Mapa de Consistencia":
            col_mat1, col_mat2, col_mat3 = st.columns([1, 1.5, 1])
            with col_mat1:
                st.markdown("##### 📍 Ajustes de Mapa")
                st.caption("Mueve los controles para posicionar el 'Punto de Diseño' en la matriz.")
                x_trab = st.slider("Trabajabilidad (Shilstone) ➡️", 0.0, 1.0, 0.5, 0.1, help="Más a la derecha = Mejor para bombeo")
                y_coh = st.slider("Cohesión (Tarantula) ⬆️", 0.0, 1.0, 0.5, 0.1, help="Más arriba = Menos segregación")
            
            with col_mat2:
                # Gráfico 2D visual del punto
                import plotly.graph_objects as go
                fig_mat = go.Figure()
                fig_mat.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="gray")
                fig_mat.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="gray")
                fig_mat.add_trace(go.Scatter(
                    x=[x_trab], y=[y_coh], 
                    mode='markers+text',
                    marker=dict(size=25, color='red', symbol='cross', line=dict(width=2, color='darkred')),
                    name="ADN Elegido"
                ))
                fig_mat.update_layout(
                    xaxis=dict(title="Trabajabilidad →", range=[0, 1], showgrid=False),
                    yaxis=dict(title="Cohesión →", range=[0, 1], showgrid=False),
                    width=400, height=400, margin=dict(l=40, r=20, t=20, b=40),
                    showlegend=False,
                    plot_bgcolor='white'
                )
                st.plotly_chart(fig_mat, use_container_width=True, config={'displayModeBar': False})
            
            with col_mat3:
                pesos_mat = calcular_pesos_desde_matriz(x_trab, y_coh)
                st.markdown("##### ⚖️ Pesos Calculados")
                st.code(f"Haystack: {pesos_mat['haystack']:.3f}\nTarantula: {pesos_mat['tarantula']:.3f}\nShilstone: {pesos_mat['shilstone']:.3f}\nPower 45: {pesos_mat['power45']:.3f}")

            pesos_finales = {
                'peso_haystack': pesos_mat['haystack'],
                'peso_tarantula': pesos_mat['tarantula'],
                'peso_shilstone': pesos_mat['shilstone']
            }

        elif estrategia == "⚙️ Personalizado (Manual)":
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("##### 🛠️ Ajuste Manual de Pesos")
                w_haystack = st.slider("Importancia Haystack (Norma)", 0.0, 1.0, 0.25)
                w_tarantula = st.slider("Importancia Tarantula (Cohesión)", 0.0, 1.0, 0.25)
            with col_m2:
                w_shilstone = st.slider("Importancia Shilstone (Bombeabilidad)", 0.0, 1.0, 0.25)
                st.info("💡 **Nota:** El peso de Power 45 se calcula automáticamente para completar la unidad.")
            
            pesos_finales = {
                'peso_haystack': w_haystack,
                'peso_tarantula': w_tarantula,
                'peso_shilstone': w_shilstone
            }

        st.write("")
        
        # --- NUEVO: RESTRICCIONES DE USUARIO (Mínimos MOP/EETT) ---
        limites_minimos = [0.0] * len(grans)
        suma_minimos = 0.0
        
        with st.expander("🔓 Restricciones de Usuario (Mínimos %)", expanded=False):
            st.caption("Define el porcentaje mínimo obligatorio para cada árido (ej. MOP exige min 40% chancado).")
            cols_min = st.columns(len(grans))
            for i, a in enumerate(aridos):
                nombre = a.get('Nombre', f'Árido {i+1}')
                with cols_min[i]:
                    val_min = st.number_input(
                        f"Min % {nombre}",
                        min_value=0.0, max_value=100.0, value=0.0, step=5.0,
                        key=f"min_restriccion_{i}"
                    )
                    limites_minimos[i] = val_min
                    suma_minimos += val_min
            
            if suma_minimos > 100:
                st.error(f"❌ La suma de mínimos ({suma_minimos}%) excede el 100%. Ajusta tus restricciones.")
                datos_validos = False # Bloquear botón
            elif suma_minimos > 80:
                st.warning(f"⚠️ Restricciones muy altas ({suma_minimos}%). El optimizador tendrá poco margen de maniobra.")

        st.write("")
        if st.button("🚀 Ejecutar Optimización de ADN", disabled=not datos_validos, use_container_width=True):
            with st.spinner("Buscando la armonía perfecta entre áridos..."):
                res_opt = optimizar_agregados(
                    grans, 
                    tmn=st.session_state.datos_completos['tmn'],
                    densidades=densidades_opt,
                    limites_minimos=limites_minimos,
                    **pesos_finales
                )
                if res_opt['exito']:
                    st.session_state.res_opt = res_opt
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
            
            # --- BOTÓN APLICAR OPTIMIZACIÓN ---
            if st.button("✅ Aceptar y Aplicar Optimización al Diseño", type="primary", use_container_width=True):
                # 1. Obtener peso total de áridos del diseño original
                faury_orig = st.session_state.datos_completos['faury_joisel']
                cantidades = faury_orig['cantidades_kg_m3']
                
                peso_aridos_total = 0.0
                for k, v in cantidades.items():
                    if k not in ['cemento', 'agua', 'aire', 'aditivo']:
                        peso_aridos_total += v
                
                # 2. Calcular nuevas masas
                nuevas_cantidades = cantidades.copy()
                # Limpiar referencias viejas a árido 1, 2, etc si existen, o usar nombre
                # Asumimos que el orden en 'aridos' coincide con res['proporciones']
                
                for i, prop in enumerate(res['proporciones']):
                    arido_data = aridos[i]
                    # Nombre clave usado en faury (probablemente simplificado o nombre directo)
                    # En faury_joisel.py se usa el nombre del arido como key
                    nombre_arido = arido_data['nombre'] 
                    nuevas_masa = peso_aridos_total * (prop / 100.0)
                    nuevas_cantidades[nombre_arido] = nuevas_masa
                
                # 3. Actualizar Session State
                st.session_state.datos_completos['faury_joisel']['cantidades_kg_m3'] = nuevas_cantidades
                st.session_state.datos_completos['faury_joisel']['granulometria_mezcla'] = res['mezcla_granulometria']
                st.session_state.datos_completos['shilstone']['factors'] = res['shilstone_factors'] # Update shil data if structure allows
                
                # Recalcular Shilstone completo para consistencia
                from modules.shilstone import calcular_shilstone_completo
                # Necesitamos dsss_arena ponderada nueva
                dsss_arena = 2650 
                # (Simplificación: tomamos la primera arena o promedio)
                for a in aridos:
                    if a['tipo'] != 'Grueso':
                        dsss_arena = a.get('DRSSS', 2650)
                        break
                        
                nuevo_shil = calcular_shilstone_completo(
                    granulometria_mezcla=res['mezcla_granulometria'],
                    cemento=faury_orig['cemento']['cantidad'],
                    peso_aridos_total=peso_aridos_total,
                    dsss_arena=dsss_arena,
                    agua_neta=faury_orig['agua_cemento']['agua_total'],
                    densidad_cemento=faury_orig['cemento']['densidad'],
                    aditivos=faury_orig.get('volumen_aditivos', 0),
                    aire=faury_orig['aire']['volumen']
                )
                st.session_state.datos_completos['shilstone'] = nuevo_shil
                
                st.session_state.res_opt = None # Limpiar resultado opt
                st.success("✅ Optimización aplicada. Ve a la pestaña 'Resultados' para ver el informe actualizado.")
                st.rerun()

            # Gráficos Iowa Suite + Normativos
            tab_p45, tab_tar, tab_hay, tab_shil, tab_c33, tab_nsw, tab_il = st.tabs(["Power 45", "Tarantula", "Haystack", "Shilstone", "C33 & Individual", "NSW", "Illinois Tollway"])
            
            with tab_p45:
                # Datos para P45 Optimizado
                from modules.power45 import TAMICES_POWER45, calcular_error_power45
                from modules.graphics import (
                    crear_grafico_power45_interactivo,
                    crear_grafico_tarantula_interactivo, 
                    crear_grafico_haystack_interactivo,
                    crear_grafico_shilstone_interactivo,
                    crear_grafico_individual_combinado,
                    crear_grafico_nsw,
                    crear_grafico_illinois
                )
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
                
                with st.expander("ℹ️ ¿Qué es Power 45?"):
                    st.markdown("""
                    **Teoría de Fuller (Power 0.45)**
                    
                    Es la "línea de máxima densidad". Una curva que se pega a esta línea **verde** logra el empaquetamiento más compacto posible de las piedras y arena.
                    *   **Beneficio:** Menos huecos = Menos pasta de cemento necesaria para llenarlos = **Ahorro de dinero y mayor resistencia.**
                    *   **Zona Amarilla:** Muestra dónde te sobra o te falta material respecto a la perfección matemática.
                    """)
            
            with tab_tar:
                tmn_val = st.session_state.datos_completos.get('tmn', 25.0)
                fig = crear_grafico_tarantula_interactivo(TAMICES_ASTM, res['mezcla_retenido'], tmn_val)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("ℹ️ ¿Qué es la Tarántula?"):
                    st.markdown("""
                    **Curva Tarántula (Dr. Tyler Ley)**
                    
                    Es una evolución moderna para pavimentos. No busca la densidad máxima, sino la **trabajabilidad**.
                    *   **Cuerpo (Arena Gruesa + Gravilla):** Debe estar dentro de la "caja" azul para asegurar cohesión.
                    *   **Patas (Arena Fina):** Permite cierta flexibilidad en los finos, crucial para el terminado superficial.
                    *   **Cabeza (Grava Gruesa):** Controla el esqueleto estructural.
                    """)
            
            with tab_hay:
                fig = crear_grafico_haystack_interactivo(TAMICES_ASTM, res['mezcla_retenido'])
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("ℹ️ ¿Qué es Haystack (Pajar)?"):
                    st.markdown("""
                    **Distribución en "Pajar" (Haystack)**
                    
                    Es un chequeo visual simple para evitar "baches" (gaps) o "picos" excesivos en la granulometría de cada tamiz individual.
                    *   Una buena mezcla debe parecer un "cerro" suave o un pajar, sin saltos bruscos entre un tamiz y el siguiente.
                    *   Los límites rojos indican máximos y mínimos recomendados por normativa (ACI/ASTM) para cada tamaño.
                    """)
            
            with tab_shil:
                sf = res['shilstone_factors']
                eval_dummy = {'zona': 'N/A', 'descripcion': 'Optimización', 'calidad': 'N/A'}
                fig = crear_grafico_shilstone_interactivo(sf['cf'], sf['wf'], eval_dummy)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("ℹ️ ¿Qué es Shilstone?"):
                    st.markdown("""
                    **Diagrama de Factor de Cohesión (Coarseness Factor Chart)**
                    
                    Es el mapa definitivo para predecir cómo se comportará el concreto en obra.
                    *   **Eje X (Coarseness Factor):** ¿Cuánta piedra tengo vs. cuánta arena?
                    *   **Eje Y (Workability Factor):** ¿Cuánta "crema" (mortero) tengo para lubricar esa piedra?
                    *   **Zona II (Ideal):** El punto dulce. Mezcla bombeable, terminable y resistente.
                    *   **Zona I (Gap):** Faltan piedras intermedias, riesgo de segregación.
                    *   **Zona IV (Sandy):** Mucha arena, mezcla pegajosa y alta demanda de agua.
                    """)

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
                    
                    Define los requisitos para la granulometría de áridos finos y gruesos.
                    *   **Árido Fino (Arena):** Establece límites obligatorios para asegurar un concreto trabajable y resistente. La arena debe estar dentro de la banda mostrada.
                    *   **Combinación:** Aunque C33 regula los áridos por separado, es vital verificar cómo interactúan en la mezcla total.
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
                    
                    Especificación australiana que propone una banda ideal para la **granulometría combinada** de todos los áridos.
                    *   Es más flexible que las curvas teóricas estrictas (como Fuller).
                    *   Si tu curva combinada (azul) cae dentro de la banda roja, indica una mezcla bien graduada, con buena densidad y trabajabilidad.
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

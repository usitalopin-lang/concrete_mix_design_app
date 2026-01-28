"""
Aplicación Streamlit para Diseño de Mezclas de Concreto
Método Faury-Joisel con Análisis Shilstone y Optimización

Esta aplicación permite diseñar mezclas de concreto utilizando el método
Faury-Joisel, analizar la trabajabilidad con el método Shilstone,
optimizar proporciones de agregados y generar reportes PDF profesionales.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import io
import json

# Importar módulos propios
from modules.faury_joisel import disenar_mezcla_faury
from modules.shilstone import (
    calcular_shilstone_completo, graficar_shilstone, 
    graficar_shilstone_para_pdf
)
from modules.optimization import (
    optimizar_agregados, evaluar_cumplimiento_restricciones
)
from modules.power45 import (
    generar_curva_ideal_power45,
    evaluar_gradacion, calcular_mezcla_granulometrica
)
from modules.graphics import (
    crear_grafico_shilstone_interactivo,
    crear_grafico_power45_interactivo,
    crear_grafico_tarantula_interactivo,
    crear_grafico_haystack_interactivo,
    crear_grafico_gradaciones_individuales
)
from modules.pdf_generator import generar_reporte_pdf
from modules.gemini_integration import (
    analizar_mezcla, obtener_sugerencias, responder_pregunta,
    verificar_conexion, obtener_instrucciones_configuracion
)
from config.config import (
    TAMICES_MM, TAMICES_ASTM, CONSISTENCIAS, TIPOS_CEMENTO,
    TMN_OPCIONES, DEFAULTS, EXPOSICION_OPCIONES
)
from modules.auth import login_screen, logout
from modules.database import guardar_proyecto, cargar_proyectos_usuario

# Configuración de la página
st.set_page_config(
    page_title="Diseño de Mezclas de Concreto",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def inicializar_estado():
    """Inicializa las variables de estado de la sesión."""
    if 'resultados_faury' not in st.session_state:
        st.session_state.resultados_faury = None
    if 'resultados_shilstone' not in st.session_state:
        st.session_state.resultados_shilstone = None
    if 'resultados_optimizacion' not in st.session_state:
        st.session_state.resultados_optimizacion = None
    if 'datos_completos' not in st.session_state:
        st.session_state.datos_completos = {}
    if 'aridos_config' not in st.session_state:
        st.session_state.aridos_config = []
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None


def sidebar_inputs():
    """Genera la barra lateral con inputs del usuario."""
    st.sidebar.markdown("## ⚙️ Parámetros de Diseño")
    
    # Gestión de Archivos
    st.sidebar.markdown("### 💾 Gestión de Proyecto")
    
    # Cloud Save/Load
    with st.sidebar.expander("☁️ Nube", expanded=False):
        if st.button("Guardar en Nube", use_container_width=True):
             if st.session_state.get('datos_completos'):
                 if guardar_proyecto(st.session_state.datos_completos, st.session_state.user_email):
                     st.toast("✅ Proyecto guardado en la nube")
                 else:
                     st.toast("❌ Error al guardar")
             else:
                 st.toast("⚠️ No hay datos para guardar (calcula primero)")
        
        proyectos_nube = cargar_proyectos_usuario(st.session_state.user_email)
        if proyectos_nube:
            st.markdown("---")
            opciones_proy = [f"{p['timestamp']} - {p['nombre_proyecto']}" for p in proyectos_nube]
            seleccion = st.selectbox("Cargar desde Nube", ["Seleccionar..."] + opciones_proy)
            
            if seleccion != "Seleccionar...":
                 idx = opciones_proy.index(seleccion)
                 proyecto_elegido = proyectos_nube[idx]
                 if st.button("Cargar", key="btn_load_cloud"):
                     try:
                         data = json.loads(proyecto_elegido['datos_json'])
                         # Cargar datos
                         for key, value in data.items():
                            if key in ['fecha']:
                                try:
                                    st.session_state[key] = datetime.strptime(value, '%Y-%m-%d').date()
                                except:
                                    pass
                            else:
                                st.session_state[key] = value
                         st.success("Proyecto cargado!")
                         st.rerun()
                     except Exception as e:
                         st.error(f"Error al cargar: {e}")

    uploaded_file = st.sidebar.file_uploader("Cargar Local (JSON)", type=['json'])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            # Cargar datos básicos
            for key, value in data.items():
                if key in ['fecha']:
                    try:
                        st.session_state[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except:
                        pass
                else:
                    st.session_state[key] = value
            
            st.success("Proyecto cargado!")
            # Rerun experimental para actualizar widgets
            # st.rerun() 
        except Exception as e:
            st.error(f"Error al cargar: {e}")

    # Sección: Información del Proyecto
    st.sidebar.markdown("### 📋 Información del Proyecto")
    
    # Asegurar valores por defecto en session_state
    defaults = {
        'numero_informe': "001", 'cliente': "", 'obra': "", 
        'fecha': datetime.now().date(), 'resistencia_fc': DEFAULTS['resistencia_fc'],
        'desviacion_std': DEFAULTS['desviacion_std'], 
        'fraccion_def': int(DEFAULTS['fraccion_defectuosa'] * 100),
        'consistencia': list(CONSISTENCIAS.keys()).index(DEFAULTS['consistencia']),
        'asentamiento': DEFAULTS['asentamiento'],
        'tmn': DEFAULTS['tmn'],
        'aire_porcentaje': DEFAULTS['aire_porcentaje'],
        'tipo_cemento': TIPOS_CEMENTO[0],
        'densidad_cemento': DEFAULTS['densidad_cemento']
    }

    # Asegurar default durabilidad
    if 'condicion_exposicion' not in st.session_state:
        st.session_state['condicion_exposicion'] = EXPOSICION_OPCIONES[0]
            
    # Inicializar si no existen
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    numero_informe = st.sidebar.text_input("Número de Informe", key="numero_informe")
    cliente = st.sidebar.text_input("Cliente", key="cliente")
    obra = st.sidebar.text_input("Obra", key="obra")
    fecha = st.sidebar.date_input("Fecha", key="fecha")
    
    st.sidebar.markdown("---")
    
    # Sección: Parámetros de Resistencia
    st.sidebar.markdown("### 🎯 Parámetros de Resistencia")
    
    resistencia_fc = st.sidebar.number_input(
        "Resistencia especificada fc' (MPa)",
        min_value=15.0, max_value=80.0,
        step=1.0,
        key="resistencia_fc"
    )

    # Durabilidad
    condicion_exposicion = st.sidebar.selectbox(
        "Condición de Exposición",
        options=EXPOSICION_OPCIONES,
        key="condicion_exposicion",
        help="Define requisitos mínimos de durabilidad (ACI 318 / NCh170)"
    )
    
    desviacion_std = st.sidebar.number_input(
        "Desviación estándar s (MPa)",
        min_value=1.0, max_value=10.0,
        step=0.5,
        key="desviacion_std"
    )
    
    fraccion_def_val = st.sidebar.slider(
        "Fracción defectuosa (%)",
        min_value=5, max_value=20,
        step=5,
        key="fraccion_def"
    )
    fraccion_def = fraccion_def_val / 100
    
    st.sidebar.markdown("---")
    
    # Sección: Propiedades de la Mezcla
    st.sidebar.markdown("### 🧪 Propiedades de la Mezcla")
    
    # Consistencia necesita manejo especial porque es selectbox con opciones
    # Guardamos el índice o el valor string? El widget usa index.
    
    # Callback para actualizar asentamiento
    def actualizar_asentamiento():
        val = st.session_state.consistencia_val
        if val in CONSISTENCIAS:
            st.session_state.asentamiento = CONSISTENCIAS[val]

    consistencia_idx = st.sidebar.selectbox(
        "Consistencia",
        options=list(CONSISTENCIAS.keys()),
        index=0, # El valor real vendrá del key si existe
        key="consistencia_val",
        on_change=actualizar_asentamiento
    )
    consistencia = consistencia_idx 
    
    asentamiento = st.sidebar.text_input(
        "Asentamiento",
        key="asentamiento"
    )
    
    tmn = st.sidebar.selectbox(
        "Tamaño Máximo Nominal (mm)",
        options=TMN_OPCIONES,
        key="tmn",
        help="Tamaño de la partícula de árido más grande en la mezcla."
    )
    
    aire_porcentaje = st.sidebar.number_input(
        "Aire incorporado adicional (%)",
        min_value=0.0, max_value=8.0,
        step=0.5,
        key="aire_porcentaje",
        help="Aire atrapado intencionalmente para mejorar la durabilidad (ciclos hielo-deshielo)."
    )
    
    st.sidebar.markdown("---")
    
    # Sección: Cemento
    st.sidebar.markdown("### 🏭 Cemento")
    
    tipo_cemento = st.sidebar.selectbox(
        "Tipo de cemento",
        options=TIPOS_CEMENTO,
        key="tipo_cemento"
    )
    
    densidad_cemento = st.sidebar.number_input(
        "Densidad del cemento (kg/m³)",
        min_value=2000, max_value=4000,
        step=10,
        key="densidad_cemento",
        help="Densidad real del cemento. Típicamente entre 3000 y 3200 kg/m³."
    )
    
    # Validaciones inmediatas
    if densidad_cemento < 2500:
        st.toast("⚠️ La densidad del cemento parece muy baja (< 2500 kg/m³)")

    st.sidebar.markdown("---")
    
    # Sección: Aditivos
    st.sidebar.markdown("### 🧪 Aditivos")
    
    tipos_aditivos = [
        "Incorporador de Aire", "Plastificante", "Superplastificante", 
        "Hiperplastificante", "Impermeabilizante", "Fibra (Sintética/Metálica)",
        "Pigmento", "Cristalizador", "Microsílice"
    ]
    
    aditivos_seleccionados = st.sidebar.multiselect(
        "Seleccionar Aditivos",
        options=tipos_aditivos,
        key="aditivos_seleccion",
        help="Selecciona uno o más aditivos para incorporar a la mezcla."
    )
    
    aditivos_config = []
    
    if aditivos_seleccionados:
        with st.sidebar.expander("Configurar Aditivos", expanded=True):
            for aditivo in aditivos_seleccionados:
                st.markdown(f"**{aditivo}**")
                
                # Definir valores por defecto según tipo
                dosis_def = 0.5
                densidad_def = 1.2 
                if "Fibra" in aditivo:
                    densidad_def = 0.91 # Polipropileno típico
                    dosis_def = 0.6 # kg/m3 no %, ojo. Pero app usa % cemento por estandar.
                    # Mantenemos % cemento para simplicidad o aclaramos.
                    # Usuario pidió % del peso del cemento.
                
                col_dosis, col_dens = st.columns(2)
                
                with col_dosis:
                    dosis = st.number_input(
                        f"% Dosis ({aditivo})",
                        min_value=0.0, max_value=10.0,
                        value=dosis_def,
                        step=0.1,
                        key=f"dosis_{aditivo}",
                        help="% respecto al peso del cemento"
                    )
                
                with col_dens:
                    densidad = st.number_input(
                        f"Densidad (kg/L)",
                        min_value=0.5, max_value=3.0,
                        value=densidad_def,
                        step=0.1,
                        key=f"dens_{aditivo}"
                    )
                
                aditivos_config.append({
                    'nombre': aditivo,
                    'dosis_pct': dosis,
                    'densidad_kg_lt': densidad
                })

    # Botón guardar
    st.sidebar.markdown("### 💾 Guardar")
    
    nombre_archivo = st.sidebar.text_input(
        "Nombre del Archivo",
        value=f"proyecto_{datetime.now().strftime('%Y%m%d')}",
        help="Nombre para el archivo JSON de respaldo."
    )
    
    if st.sidebar.button("Preparar descarga"):
        # Recopilar todo el estado relevante
        estado_guardar = {
            'numero_informe': st.session_state.numero_informe,
            'cliente': st.session_state.cliente,
            'obra': st.session_state.obra,
            'fecha': str(st.session_state.fecha),
            'resistencia_fc': st.session_state.resistencia_fc,
            'desviacion_std': st.session_state.desviacion_std,
            'fraccion_def': st.session_state.fraccion_def,
            'consistencia': 'Auto' if 'consistencia_val' not in st.session_state else st.session_state.consistencia_val,
            'asentamiento': st.session_state.asentamiento,
            'tmn': st.session_state.tmn,
            'aire_porcentaje': st.session_state.aire_porcentaje,
            'tipo_cemento': st.session_state.tipo_cemento,
            'condicion_exposicion': st.session_state.condicion_exposicion,
            'aditivos_config': aditivos_config
        }
        
        # Añadir áridos si existen
        # Los áridos se guardan en session_state automágicamente por input_aridos si tienen keys
        # Pero input_aridos los devuelve.
        # Mejor guardar todo lo que empiece por nombre_, tipo_, drs_, etc.
        for k in st.session_state:
            if k.startswith(('nombre_', 'tipo_', 'drs_', 'drsss_', 'abs_', 'gran_')):
                estado_guardar[k] = st.session_state[k]

        json_str = json.dumps(estado_guardar, indent=2)
        st.sidebar.download_button(
            "Descargar JSON",
            json_str,
            file_name=f"{nombre_archivo}.json",
            mime="application/json"
        )
    
    # User Info Footer sidebar
    if st.session_state.get('authenticated'):
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{st.session_state.get('user_name', 'Usuario')}**")
        if st.sidebar.button("Cerrar Sesión"):
            logout()
    
    return {
        'numero_informe': numero_informe,
        'cliente': cliente,
        'obra': obra,
        'fecha': fecha.strftime('%d/%m/%Y'),
        'resistencia_fc': resistencia_fc,
        'desviacion_std': desviacion_std,
        'fraccion_def': fraccion_def,
        'consistencia': consistencia,
        'asentamiento': asentamiento,
        'tmn': tmn,
        'aire_porcentaje': aire_porcentaje,
        'tipo_cemento': tipo_cemento,
        'densidad_cemento': densidad_cemento,
        'tipo_cemento': tipo_cemento,
        'densidad_cemento': densidad_cemento,
        'condicion_exposicion': condicion_exposicion,
        'aditivos_config': aditivos_config
    }


def input_aridos():
    """Genera el formulario para ingresar datos de áridos."""
    st.markdown("### 🪨 Configuración de Áridos")
    
    num_aridos = st.radio(
        "Número de áridos",
        options=[2, 3],
        index=0,
        horizontal=True
    )
    
    aridos = []
    
    cols = st.columns(num_aridos)
    
    for i in range(num_aridos):
        with cols[i]:
            st.markdown(f"#### Árido {i+1}")
            
            if i == 0:
                nombre_default = "Grava Chancada 25mm"
                drs_default = 2730
                drsss_default = 2760
                abs_default = 0.9
                tipo_default = "Grueso"
            elif i == 1 and num_aridos == 2:
                nombre_default = "Arena 10mm"
                drs_default = 2610
                drsss_default = 2650
                abs_default = 1.6
                tipo_default = "Fino"
            elif i == 1:
                nombre_default = "Grava Rodada 25mm"
                drs_default = 2655
                drsss_default = 2680
                abs_default = 1.1
                tipo_default = "Intermedio"
            else:
                nombre_default = "Arena 10mm"
                drs_default = 2610
                drsss_default = 2650
                abs_default = 1.6
                tipo_default = "Fino"
            
            nombre = st.text_input(f"Nombre", nombre_default, key=f"nombre_{i}")
            
            tipo = st.selectbox(
                "Tipo",
                options=["Grueso", "Intermedio", "Fino"],
                index=["Grueso", "Intermedio", "Fino"].index(tipo_default),
                key=f"tipo_{i}"
            )
            
            drs = st.number_input(
                "DRS (kg/m³)",
                min_value=2000, max_value=3500,
                value=drs_default,
                key=f"drs_{i}"
            )
            
            drsss = st.number_input(
                "DRSSS (kg/m³)",
                min_value=2000, max_value=3500,
                value=drsss_default,
                key=f"drsss_{i}"
            )
            
            absorcion = st.number_input(
                "Absorción (%)",
                min_value=0.0, max_value=10.0,
                value=abs_default,
                step=0.1,
                key=f"abs_{i}",
                help="Porcentaje de agua que el árido puede absorber."
            )
            
            # Validación absorción
            if absorcion > 5.0:
                 st.toast(f"⚠️ Absorción alta ({absorcion}%) en Árido {i+1}", icon="💧")
            
            absorcion = absorcion / 100
            
            # Granulometría
            st.markdown("**Granulometría (% que pasa)**")
            
            # Valores por defecto según tipo
            if tipo == "Grueso":
                gran_default = [100, 100, 97, 76, 34, 21, 2, 1, 0, 0, 0, 0]
            elif tipo == "Intermedio":
                gran_default = [100, 100, 90, 71, 45, 32, 4, 2, 0, 0, 0, 0]
            else:  # Fino
                gran_default = [100, 100, 100, 100, 100, 100, 94, 74, 53, 37, 21, 8]
            
            granulometria = []
            
            # Mostrar en dos filas de 6 tamices cada una
            for row in range(2):
                cols_gran = st.columns(6)
                for j in range(6):
                    idx = row * 6 + j
                    with cols_gran[j]:
                        valor = st.number_input(
                            TAMICES_ASTM[idx],
                            min_value=0.0, max_value=100.0,
                            value=float(gran_default[idx]),
                            step=1.0,
                            key=f"gran_{i}_{idx}"
                        )
                        granulometria.append(valor)
            
            aridos.append({
                'nombre': nombre,
                'tipo': tipo,
                'DRS': drs,
                'DRSSS': drsss,
                'absorcion': absorcion,
                'granulometria': granulometria
            })
    
    return aridos


def mostrar_resultados_faury(resultados):
    """Muestra los resultados del método Faury-Joisel."""
    st.markdown("### 📊 Resultados del Método Faury-Joisel")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Resistencia media (fd)",
            f"{resultados['resistencia']['fd_mpa']:.1f} MPa",
            f"{resultados['resistencia']['fd_kgcm2']:.0f} kg/cm²"
        )
    
    with col2:
        st.metric(
            "Cantidad de Cemento",
            f"{resultados['cemento']['cantidad']:.0f} kg/m³"
        )
    
    with col3:
        st.metric(
            "Razón A/C",
            f"{resultados['agua_cemento']['razon']:.3f}"
        )
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(
            "Agua de amasado",
            f"{resultados['agua_cemento']['agua_amasado']:.1f} lt/m³"
        )
    
    with col5:
        st.metric(
            "Agua total",
            f"{resultados['agua_cemento']['agua_total']:.1f} lt/m³"
        )
    
    with col6:
        st.metric(
            "Compacidad",
            f"{resultados['compacidad']:.4f}"
        )
    
    st.markdown("---")

    
    # Tabla de cantidades
    st.markdown("#### Cantidades de Áridos (kg/m³)")
    
    cant_df = pd.DataFrame([
        {"Material": k.replace('_', ' ').title(), "Cantidad (kg/m³)": f"{v:.1f}"}
        for k, v in resultados['cantidades_kg_m3'].items()
    ])
    st.dataframe(cant_df, hide_index=True)
    
    # Granulometría de la mezcla
    st.markdown("#### Granulometría de la Mezcla")
    
    gran_data = []
    for i, tamiz in enumerate(TAMICES_ASTM):
        if i < len(resultados['granulometria_mezcla']):
            gran_data.append({
                "Tamiz": tamiz,
                "mm": TAMICES_MM[i],
                "Mezcla %": f"{resultados['granulometria_mezcla'][i]:.1f}",
                "Lím. Inf.": f"{resultados['banda_trabajo'][i][0]:.1f}",
                "Lím. Sup.": f"{resultados['banda_trabajo'][i][1]:.1f}"
            })
    
    gran_df = pd.DataFrame(gran_data)
    st.dataframe(gran_df, hide_index=True)


def mostrar_resultados_shilstone(resultados):
    """Muestra los resultados del análisis Shilstone."""
    st.markdown("### 📈 Análisis Shilstone")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CF", f"{resultados['CF']:.1f}")
    with col2:
        st.metric("W", f"{resultados['W']:.1f}")
    with col3:
        st.metric("Wadj", f"{resultados['Wadj']:.1f}")
    with col4:
        st.metric("FM", f"{resultados['FM']:.1f} lt/m³")
    
    # Evaluación
    evaluacion = resultados['evaluacion']
    
    if evaluacion['calidad'] == 'Óptima':
        st.success(f"**Zona:** {evaluacion['zona']}")
    elif evaluacion['calidad'] == 'Aceptable':
        st.warning(f"**Zona:** {evaluacion['zona']}")
    else:
        st.error(f"**Zona:** {evaluacion['zona']}")
    
    st.markdown(f"**Descripción:** {evaluacion['descripcion']}")
    
    if evaluacion['recomendaciones']:
        st.markdown("**Recomendaciones:**")
        for rec in evaluacion['recomendaciones']:
            st.markdown(f"- {rec}")
    
    # Gráfico
    st.markdown("#### Gráfico Shilstone")
    # Gráfico Interactivo
    st.markdown("#### Gráfico Shilstone Interactivo")
    fig_interactive = crear_grafico_shilstone_interactivo(
        resultados['CF'],
        resultados['Wadj'],
        resultados['evaluacion']
    )
    st.plotly_chart(fig_interactive, use_container_width=True)
    # plt.close(fig) # Ya no usamos pyplot aquí


def mostrar_resultados_optimizacion(resultados, granulometrias, tmn):
    """Muestra los resultados de la optimización."""
    st.markdown("### 🎯 Resultados de la Optimización")
    
    if resultados['exito']:
        st.success(f"✅ {resultados['mensaje']}")
        
        # Proporciones óptimas
        col1, col2, col3 = st.columns(3)
        
        for i, prop in enumerate(resultados['proporciones']):
            with [col1, col2, col3][i % 3]:
                st.metric(f"Árido {i+1}", f"{prop:.2f}%")
        
        # Errores
        st.markdown("#### Métricas de Error")
        
        err_col1, err_col2, err_col3 = st.columns(3)
        with err_col1:
            st.metric("Error Power 45", f"{resultados['error_power45']:.4f}")
        with err_col2:
            st.metric("Error Haystack", f"{resultados['error_haystack']:.4f}")
        with err_col3:
            st.metric("Error Tarantula", f"{resultados['error_tarantula']:.4f}")
        
        
        # Crear pestañas para los gráficos
        tab_p45, tab_tar, tab_hay, tab_ind = st.tabs([
            "📉 Power 45", 
            "🕷️ Tarántula", 
            "🌾 Haystack", 
            "📊 Gradaciones"
        ])

        # Preparar datos comunes
        tamices_nombres = TAMICES_ASTM
        mezcla_vals = resultados['mezcla_granulometria']
        # Asegurar longitud
        _, ideal_vals_p45 = generar_curva_ideal_power45(tmn, TAMICES_MM)
        if len(mezcla_vals) < len(ideal_vals_p45):
            mezcla_vals = mezcla_vals + [0] * (len(ideal_vals_p45) - len(mezcla_vals))

        with tab_p45:
             # Calcular eje X (tamiz^0.45)
            tamices_power = [t**0.45 for t in TAMICES_MM]
            
            fig_p45 = crear_grafico_power45_interactivo(
                tamices_nombres,
                tamices_power,
                ideal_vals_p45,
                mezcla_vals,
                resultados['error_power45']
            )
            st.plotly_chart(fig_p45, use_container_width=True)
            
            # Evaluación de gradación
            eval_grad = evaluar_gradacion(resultados['mezcla_granulometria'], tmn)
            if eval_grad['calidad'] == 'Excelente':
                st.success(f"**Calidad de Gradación:** {eval_grad['calidad']}")
            elif eval_grad['calidad'] == 'Buena':
                st.info(f"**Calidad de Gradación:** {eval_grad['calidad']}")
            else:
                st.warning(f"**Calidad de Gradación:** {eval_grad['calidad']}")
            st.markdown(f"**{eval_grad['descripcion']}**")

        with tab_tar:
            # Calcular retenidos de la MEZCLA
            retenidos_mezcla = []
            for i in range(len(mezcla_vals)):
                if i == 0:
                     # El primer tamiz suele ser 100% que pasa, retenido = 0? 
                     # Ojo: Retenido = Anterior - Actual
                     retenidos_mezcla.append(0) # Asumiendo tmn
                else:
                     ret = mezcla_vals[i-1] - mezcla_vals[i]
                     retenidos_mezcla.append(ret)
            
            # Ajuste primer elemento si mezcla_vals[0] != 100
            if mezcla_vals[0] < 100:
                 retenidos_mezcla[0] = 100 - mezcla_vals[0]
            
            fig_tar = crear_grafico_tarantula_interactivo(tamices_nombres, retenidos_mezcla, tmn)
            st.plotly_chart(fig_tar, use_container_width=True)
            st.info("La curva debe mantenerse dentro del área gris para minimizar problemas de segregación y cohesión.")

        with tab_hay:
            # Usamos los mismos retenidos
            fig_hay = crear_grafico_haystack_interactivo(tamices_nombres, retenidos_mezcla)
            st.plotly_chart(fig_hay, use_container_width=True)
            st.info("Visualización de retenidos para controlar excesos en tamices específicos.")

        with tab_ind:
            # Recuperar datos de session_state o pasarlos como argumento?
            # En la función principal se pasan 'granulometrias'
            if 'aridos_config' in st.session_state:
                aridos_data = st.session_state.aridos_config
                props = resultados['proporciones']
                
                fig_ind = crear_grafico_gradaciones_individuales(
                    tamices_nombres, 
                    aridos_data, 
                    props, 
                    mezcla_vals
                )
                st.plotly_chart(fig_ind, use_container_width=True)
            else:
                st.warning("No se pudieron cargar los datos de áridos individuales.")
        
    else:
        st.error(f"❌ {resultados['mensaje']}")


def seccion_gemini(datos_completos):
    """Sección de integración con Gemini AI."""
    st.markdown("### 🤖 Análisis con Inteligencia Artificial")
    
    # Verificar conexión
    estado = verificar_conexion()
    
    if not estado['funcionando']:
        # Si hay un mensaje de error específico (diferente a no configurado), mostrarlo
        if estado['mensaje'] and "no está configurada" not in estado['mensaje']:
             st.error(f"⚠️ {estado['mensaje']}")
        else:
             st.warning("⚠️ Gemini AI no está configurado")
        
        with st.expander("📋 Instrucciones de configuración"):
            st.markdown(obtener_instrucciones_configuracion())
        
        # Permitir ingresar API key manualmente
        api_key_manual = st.text_input(
            "O ingresa tu API key aquí:",
            type="password",
            help="Pega aquí tu Google API Key que empieza por AIza..."
        )
        
        if api_key_manual:
            with st.spinner("Verificando llave..."):
                estado = verificar_conexion(api_key_manual)
                if estado['funcionando']:
                    st.success("✅ API key válida! Guardando y recargando...")
                    st.session_state['gemini_api_key'] = api_key_manual
                    st.rerun()
                else:
                    st.error(f"❌ Error: {estado['mensaje']}")
        
        # Si aún no funciona (y no se acaba de arreglar arriba), salir
        if not estado['funcionando']:
            return
    
    api_key = st.session_state.get('gemini_api_key', None)
    
    # Pestañas de funcionalidad
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "💡 Sugerencias", "❓ Preguntas"])
    
    with tab1:
        st.markdown("#### Análisis Completo de la Mezcla")
        if st.button("🔍 Analizar Mezcla", key="btn_analizar"):
            with st.spinner("Analizando con Gemini AI..."):
                resultado = analizar_mezcla(datos_completos, api_key)
                
                if resultado['exito']:
                    st.markdown(resultado['analisis'])
                else:
                    st.error(f"Error: {resultado['error']}")
    
    with tab2:
        st.markdown("#### Sugerencias de Optimización")
        
        problema = st.text_area(
            "Describe un problema específico (opcional):",
            placeholder="Ej: La mezcla tiene baja trabajabilidad..."
        )
        
        if st.button("💡 Obtener Sugerencias", key="btn_sugerencias"):
            with st.spinner("Generando sugerencias..."):
                resultado = obtener_sugerencias(datos_completos, problema if problema else None, api_key)
                
                if resultado['exito']:
                    st.markdown(resultado['sugerencias'])
                else:
                    st.error(f"Error: {resultado['error']}")
    
    with tab3:
        st.markdown("#### Pregunta al Experto")
        
        pregunta = st.text_input(
            "Escribe tu pregunta:",
            placeholder="Ej: ¿Cómo puedo mejorar la durabilidad?"
        )
        
        if st.button("🗣️ Preguntar", key="btn_preguntar") and pregunta:
            with st.spinner("Procesando pregunta..."):
                resultado = responder_pregunta(datos_completos, pregunta, api_key)
                
                if resultado['exito']:
                    st.markdown(resultado['respuesta'])
                else:
                    st.error(f"Error: {resultado['error']}")


def generar_descarga_pdf(datos_completos, resultados_shilstone):
    """Genera y permite descargar el PDF."""
    st.markdown("### 📄 Generar Reporte PDF")
    
    if st.button("📥 Generar PDF", key="btn_pdf"):
        with st.spinner("Generando PDF..."):
            try:
                # Generar imagen Shilstone
                imagen_shilstone = None
                if resultados_shilstone:
                    imagen_shilstone = graficar_shilstone_para_pdf(
                        resultados_shilstone['CF'],
                        resultados_shilstone['Wadj'],
                        resultados_shilstone['FM']
                    )
                
                # Generar PDF
                pdf_bytes = generar_reporte_pdf(datos_completos, imagen_shilstone)
                
                st.success("✅ PDF generado exitosamente")
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Informe_Dosificacion_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error al generar PDF: {str(e)}")


def exportar_excel(datos_completos):
    """Permite exportar los resultados a Excel."""
    st.markdown("### 📊 Exportar a Excel")
    
    if st.button("📥 Exportar Excel", key="btn_excel"):
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja 1: Parámetros
                params_data = {
                    'Parámetro': ['fc\'', 's', 'fd', 'Cemento', 'A/C', 'Agua total', 'Compacidad'],
                    'Valor': [
                        datos_completos.get('fc', '-'),
                        datos_completos.get('desviacion_std', '-'),
                        datos_completos.get('faury_joisel', {}).get('resistencia', {}).get('fd_mpa', '-'),
                        datos_completos.get('faury_joisel', {}).get('cemento', {}).get('cantidad', '-'),
                        datos_completos.get('faury_joisel', {}).get('agua_cemento', {}).get('razon', '-'),
                        datos_completos.get('faury_joisel', {}).get('agua_cemento', {}).get('agua_total', '-'),
                        datos_completos.get('faury_joisel', {}).get('compacidad', '-')
                    ],
                    'Unidad': ['MPa', 'MPa', 'MPa', 'kg/m³', '-', 'lt/m³', 'm³/m³']
                }
                pd.DataFrame(params_data).to_excel(writer, sheet_name='Parámetros', index=False)
                
                # Hoja 2: Cantidades
                cantidades = datos_completos.get('faury_joisel', {}).get('cantidades_kg_m3', {})
                cant_data = {
                    'Material': list(cantidades.keys()),
                    'Cantidad (kg/m³)': list(cantidades.values())
                }
                pd.DataFrame(cant_data).to_excel(writer, sheet_name='Cantidades', index=False)
                
                # Hoja 3: Shilstone
                shil = datos_completos.get('shilstone', {})
                if shil:
                    shil_data = {
                        'Parámetro': ['CF', 'W', 'Wadj', 'FM', 'Zona'],
                        'Valor': [
                            shil.get('CF', '-'),
                            shil.get('W', '-'),
                            shil.get('Wadj', '-'),
                            shil.get('FM', '-'),
                            shil.get('evaluacion', {}).get('zona', '-')
                        ]
                    }
                    pd.DataFrame(shil_data).to_excel(writer, sheet_name='Shilstone', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output.getvalue(),
                file_name=f"Dosificacion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Error al exportar: {str(e)}")


def mostrar_ayuda():
    """Muestra la pestaña de ayuda."""
    st.markdown("### ❓ Guía de Usuario y Glosario")
    
    with st.expander("📘 Guía Paso a Paso", expanded=True):
        st.markdown("""
        1. **Datos de Entrada:**
           - Configura los parámetros de resistencia y durabilidad en la barra lateral.
           - Define los áridos disponibles (Grava, Arena, etc.) y sus propiedades.
           - Haz clic en **"Calcular Diseño"**.
        
        2. **Faury-Joisel:**
           - Revisa la dosificación calculada (cemento, agua, áridos).
           - Verifica que la resistencia media ($f_d$) cumpla con lo requerido.
        
        3. **Shilstone:**
           - Analiza el gráfico de trabajabilidad.
           - Busca que tu mezcla esté en la **Zona I (Óptima)** (área verde).
           - Sigue las recomendaciones si estás en una zona problemática (Rocky/Arenosa).
        
        4. **Optimización:**
           - Si la granulometría no es ideal, usa esta pestaña.
           - Ajusta los pesos de las restricciones (Haystack/Tarantula) y optimiza.
           - El sistema te dará los porcentajes exactos de cada árido.
        """)
    
    with st.expander("📚 Glosario Técnico"):
        st.markdown("""
        *   **CF (Coarseness Factor):** Factor de Grosor. Indica qué tan "rocosa" es la mezcla.
        *   **Wadj (Workability Factor Ajustado):** Factor de Trabajabilidad. Relacionado con la cantidad de finos y cemento.
        *   **Power 45:** Curva ideal teórica para máxima densidad.
        *   **Zona I (Óptima):** Zona del gráfico Shilstone donde la mezcla tiene buen desempeño y trabajabilidad.
        *   **Zona Rocky:** Exceso de grava, riesgo de segregación.
        *   **Zona Arenosa:** Exceso de finos, alta demanda de agua.
        """)
    
    st.info("💡 **Tip:** Pasa el mouse sobre los campos de entrada para ver ayudas específicas.")


def main():
    """Función principal de la aplicación."""
    inicializar_estado()
    
    # Gatekeeper: Login Check
    if not st.session_state.get('authenticated'):
        login_screen()
        return
    
    # Encabezado
    st.markdown('<p class="main-header">🏗️ Diseño de Mezclas de Concreto</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Método Faury-Joisel con Análisis Shilstone</p>', unsafe_allow_html=True)
    
    # Sidebar con inputs
    params = sidebar_inputs()
    
    # Contenido principal con pestañas
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Datos de Entrada",
        "📊 Faury-Joisel",
        "📈 Shilstone",
        "🎯 Optimización",
        "🤖 IA & Reportes",
        "❓ Ayuda"
    ])
    
    with tab1:
        st.markdown("## 📝 Entrada de Datos")
        
        # Áridos
        aridos = input_aridos()
        st.session_state.aridos_config = aridos
        
        st.markdown("---")
        
        # Botón de cálculo
        if st.button("🔄 Calcular Diseño", type="primary", key="btn_calcular"):
            with st.spinner("Calculando diseño de mezcla..."):
                try:
                    # Ejecutar Faury-Joisel
                    resultados_faury = disenar_mezcla_faury(
                        resistencia_fc=params['resistencia_fc'],
                        desviacion_std=params['desviacion_std'],
                        fraccion_def=params['fraccion_def'],
                        consistencia=params['consistencia'],
                        tmn=params['tmn'],
                        densidad_cemento=params['densidad_cemento'],
                        aridos=aridos,
                        aire_porcentaje=params['aire_porcentaje'],
                        condicion_exposicion=params['condicion_exposicion'],
                        aditivos_config=params['aditivos_config']
                    )
                    st.session_state.resultados_faury = resultados_faury
                    
                    # Calcular Shilstone
                    peso_aridos_total = sum(resultados_faury['cantidades_kg_m3'].values())
                    # AJUSTE: Si hay aditivos, pueden haber reducido el peso de áridos para mantener volumen.
                    # El shilstone debe usar el peso real de los áridos.
                    
                    dsss_arena = aridos[-1]['DRSSS']  # Arena es el último
                    
                    resultados_shilstone = calcular_shilstone_completo(
                        granulometria_mezcla=resultados_faury['granulometria_mezcla'],
                        cemento=resultados_faury['cemento']['cantidad'],
                        peso_aridos_total=peso_aridos_total,
                        dsss_arena=dsss_arena,
                        agua_neta=resultados_faury['agua_cemento']['agua_amasado'],
                        densidad_cemento=params['densidad_cemento'],
                        aire=resultados_faury['aire']['volumen']
                    )
                    st.session_state.resultados_shilstone = resultados_shilstone
                    
                    # Guardar datos completos
                    st.session_state.datos_completos = {
                        **params,
                        'fc': params['resistencia_fc'],
                        'fd': resultados_faury['resistencia']['fd_mpa'],
                        'aridos': aridos,
                        'faury_joisel': resultados_faury,
                        'shilstone': resultados_shilstone
                    }
                    
                    st.success("✅ Cálculo completado exitosamente")
                    st.info("Navega a las pestañas para ver los resultados detallados")
                    
                except Exception as e:
                    st.error(f"Error en el cálculo: {str(e)}")
    
    with tab2:
        if st.session_state.resultados_faury:
            mostrar_resultados_faury(st.session_state.resultados_faury)
        else:
            st.info("👈 Ingresa los datos y haz clic en 'Calcular Diseño' para ver los resultados")
    
    with tab3:
        if st.session_state.resultados_shilstone:
            mostrar_resultados_shilstone(st.session_state.resultados_shilstone)
        else:
            st.info("👈 Ingresa los datos y haz clic en 'Calcular Diseño' para ver los resultados")
    
    with tab4:
        st.markdown("## 🎯 Optimización de Agregados")
        
        if st.session_state.aridos_config:
            
            with st.expander("ℹ️ ¿Cómo funciona la Optimización?", expanded=True):
                st.markdown("""
                El algoritmo busca la **Mezcla Ideal** ajustando los porcentajes de cada árido.
                
                Tú controlas qué tan estricto ser con cada criterio usando los deslizadores ("Pesos"):
                *   **Peso alto (aprox 0.8 - 1.0):** El sistema hará todo lo posible por cumplir este criterio, aunque sacrifique otros.
                *   **Peso bajo (aprox 0.0 - 0.2):** Es una "sugerencia". Si se puede cumplir bien, si no, no importa tanto.
                """)

            st.markdown("### 🎚️ Parámetros de Control")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 1. Banda Granulométrica (Haystack)")
                peso_haystack = st.slider(
                    "Peso Haystack (Normativo)", 0.0, 1.0, 0.3,
                    help="Controla el cumplimiento de las bandas ASTM C33 / NCh170."
                )
                st.info(
                    "**Efecto:** Mantiene la arena dentro de los límites normativos.\n\n"
                    "🔴 **Alto:** Prioriza cumplir la norma estrictamente.\n"
                    "⚪ **Bajo:** Permite salirse de la banda si mejora la densidad.",
                    icon="📏"
                )

                st.markdown("#### 2. Retención Individual (Tarantula)")
                peso_tarantula = st.slider(
                    "Peso Tarantula (Cohesión)", 0.0, 1.0, 0.3,
                    help="Controla la cantidad retenida en cada tamiz individual."
                )
                st.info(
                    "**Efecto:** Evita 'valles' (falta de material) y 'picos' (exceso).\n\n"
                    "🔴 **Alto:** Mezcla más cohesiva, mejor terminación, bombeable.\n"
                    "⚪ **Bajo:** Puede generar mezclas más ásperas o segregables.",
                    icon="🕷️"
                )
            
            with col2:
                st.markdown("#### 3. Trabajabilidad (Shilstone)")
                peso_shilstone = st.slider(
                    "Peso Shilstone (Maquinabilidad)", 0.0, 1.0, 0.2,
                    help="Optimiza la posición en el gráfico de Coarseness Factor."
                )
                st.info(
                    "**Efecto:** Busca que la mezcla caiga en la 'Zona I - Óptima'.\n\n"
                    "🔴 **Alto:** Prioriza que la mezcla sea fácil de colocar y compactar.\n"
                    "⚪ **Bajo:** Se enfoca solo en la densidad máxima (Power 45).",
                    icon="📉"
                )

                # Algoritmo interno (oculto para simplicidad)
                metodo = 'SLSQP' 
            
            if st.button("🚀 Optimizar", key="btn_optimizar"):
                with st.spinner("Optimizando proporciones..."):
                    try:
                        granulometrias = [a['granulometria'] for a in st.session_state.aridos_config]
                        
                        resultados_opt = optimizar_agregados(
                            granulometrias=granulometrias,
                            tmn=params['tmn'],
                            num_agregados=len(granulometrias),
                            peso_haystack=peso_haystack,
                            peso_tarantula=peso_tarantula,
                            peso_shilstone=peso_shilstone,
                            metodo=metodo
                        )
                        
                        st.session_state.resultados_optimizacion = resultados_opt
                        mostrar_resultados_optimizacion(resultados_opt, granulometrias, params['tmn'])
                        
                    except Exception as e:
                        st.error(f"Error en la optimización: {str(e)}")
        else:
            st.info("👈 Configura los áridos en la pestaña 'Datos de Entrada' primero")
    
    with tab5:
        if st.session_state.datos_completos:
            # Gemini AI
            seccion_gemini(st.session_state.datos_completos)
            
            st.markdown("---")
            
            # Exportaciones
            col1, col2 = st.columns(2)
            
            with col1:
                generar_descarga_pdf(
                    st.session_state.datos_completos,
                    st.session_state.resultados_shilstone
                )
            
            with col2:
                exportar_excel(st.session_state.datos_completos)
        else:
            st.info("👈 Realiza el cálculo de diseño primero para acceder a estas funciones")
            
    with tab6:
        mostrar_ayuda()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            Aplicación de Diseño de Mezclas de Concreto | Método Faury-Joisel con Análisis Shilstone<br>
            Desarrollado con Streamlit | 2024
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

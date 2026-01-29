"""
Módulo de utilidades UI compartidas.
Contiene funciones de inicialización de estado y componentes de interfaz (sidebars, inputs)
que se reutilizan en las distintas páginas.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config.config import (
    DEFAULTS, CONSISTENCIAS, EXPOSICION_OPCIONES, TAMICES_ASTM, TMN_OPCIONES
)
from modules import catalogs
from modules.auth import logout
from modules.database import guardar_proyecto, cargar_proyectos_usuario
import json

def inicializar_estado():
    """Inicializa las variables de estado global si no existen."""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if 'datos_completos' not in st.session_state:
        st.session_state.datos_completos = None
        
    if 'resultados_faury' not in st.session_state:
        st.session_state.resultados_faury = None
        
    if 'resultados_shilstone' not in st.session_state:
        st.session_state.resultados_shilstone = None
        
    if 'resultados_optimizacion' not in st.session_state:
        st.session_state.resultados_optimizacion = None

    if 'aridos_config' not in st.session_state:
        st.session_state.aridos_config = []
        
    if 'analisis_ia' not in st.session_state:
        st.session_state.analisis_ia = None
        
    if 'res_opt' not in st.session_state:
        st.session_state.res_opt = None

def sidebar_inputs():
    """Renderiza los inputs comunes del Sidebar (Proyecto, Materiales)."""
    
    # No mostrar sidebar si no está autenticado
    if not st.session_state.get('authenticated'):
        return {}
    
    # Cloud Save/Load (Común para todos)
    with st.sidebar.expander("☁️ Guardar en Nube", expanded=False):
        if st.button("Guardar en Nube", use_container_width=True):
             if st.session_state.get('datos_completos') and st.session_state.get('user_email'):
                 if guardar_proyecto(st.session_state.datos_completos, st.session_state.user_email):
                     st.toast("✅ Proyecto guardado en la nube")
                 else:
                     st.toast("❌ Error al guardar")
             else:
                 st.toast("⚠️ No hay datos para guardar (calcula primero)")


    # --- CARGA DE PROYECTOS ---
    
    # Cargar desde Nube
    from modules.database import cargar_proyectos_usuario
    with st.sidebar.expander("☁️ Cargar desde Nube"):
        # Obtener usuario actual
        user_email = st.session_state.get('user_email')
        if not user_email:
             # Si no hay usuario (caso dev o error), intentar fallback o mostrar aviso
             st.warning("Usuario no identificado.")
        else:
             if st.button("🔄 Refrescar Lista"):
                  st.cache_data.clear() # Limpiar cache si usamos cache en cargar
             
             proyectos_nube = cargar_proyectos_usuario(user_email)
             if not proyectos_nube:
                  st.info("No se encontraron proyectos guardados.")
             else:
                  # Mapeo: "Fecha - Nombre" -> Proyecto
                  mapa_proy = {}
                  for p in proyectos_nube:
                       label = f"{p['timestamp']} - {p['nombre_proyecto']}"
                       mapa_proy[label] = p
                  
                  sel_proy = st.selectbox("Seleccionar Proyecto", list(mapa_proy.keys()))
                  
                  if st.button("📥 Cargar Seleccionado"):
                       try:
                           target = mapa_proy[sel_proy]
                           data_str = target['datos_json']
                           # Parsear si es string
                           if isinstance(data_str, str):
                               data = json.loads(data_str)
                           else:
                               data = data_str
                               
                           # Cargar al estado (Misma lógica que JSON local)
                           for key, value in data.items():
                                if key in ['fecha']:
                                     try:
                                         st.session_state[key] = datetime.strptime(value, '%Y-%m-%d').date()
                                     except:
                                         pass
                                else:
                                     st.session_state[key] = value
                           
                           st.success(f"Proyecto '{target['nombre_proyecto']}' cargado!")
                           st.rerun()
                       except Exception as e:
                           st.error(f"Error al cargar proyecto nube: {e}")

    uploaded_file = st.sidebar.file_uploader("Cargar Local (JSON)", type=['json'])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
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

    # Sección: Información del Proyecto
    st.sidebar.markdown("### 📋 Información del Proyecto")
    
    # Default loading logic moved inside input declarations via session_state check
    # But initialization should happen before inputs to avoid errors
    defaults = {
         'numero_informe': "001", 'cliente': "", 'obra': "", 
         'fecha': datetime.now().date(), 'resistencia_fc': DEFAULTS['resistencia_fc'],
         'desviacion_std': DEFAULTS['desviacion_std'], 
         'fraccion_def': int(DEFAULTS['fraccion_defectuosa'] * 100),
         'consistencia': list(CONSISTENCIAS.keys()).index(DEFAULTS['consistencia']),
         'asentamiento': DEFAULTS['asentamiento'],
         'tmn': DEFAULTS['tmn'],
         'aire_porcentaje': DEFAULTS['aire_porcentaje'],
         'densidad_cemento': DEFAULTS['densidad_cemento']
    }
    
    if 'condicion_exposicion' not in st.session_state:
        st.session_state['condicion_exposicion'] = EXPOSICION_OPCIONES[0]

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
    
    def actualizar_asentamiento():
        val = st.session_state.consistencia_val
        if val in CONSISTENCIAS:
            st.session_state.asentamiento = CONSISTENCIAS[val]

    consistencia_idx = st.sidebar.selectbox(
        "Consistencia",
        options=list(CONSISTENCIAS.keys()),
        index=0, 
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
    
    # Sección: Cemento (Catálogo)
    st.sidebar.markdown("### 🏭 Cemento")
    
    cementos_cat = catalogs.obtener_cementos()
    opciones_cemento = [f"{c['Marca']} - {c['Tipo']}" for c in cementos_cat]
    
    def actualizar_densidad_cemento():
        if 'tipo_cemento_sel' in st.session_state:
             idx = opciones_cemento.index(st.session_state.tipo_cemento_sel)
             st.session_state.densidad_cemento = float(cementos_cat[idx]['Densidad'])

    tipo_cemento_sel = st.sidebar.selectbox(
        "Tipo de cemento",
        options=opciones_cemento,
        key="tipo_cemento_sel",
        on_change=actualizar_densidad_cemento
    )
    tipo_cemento = tipo_cemento_sel 
    
    if 'densidad_cemento' not in st.session_state:
        st.session_state.densidad_cemento = float(cementos_cat[0]['Densidad']) if cementos_cat else 3000.0

    densidad_cemento = st.sidebar.number_input(
        "Densidad del cemento (kg/m³)",
        min_value=2000.0, max_value=4000.0,
        step=10.0,
        key="densidad_cemento"
    )

    st.sidebar.markdown("---")
    
    # Sección: Aditivos (Catálogo)
    st.sidebar.markdown("### 🧪 Aditivos")
    
    aditivos_cat = catalogs.obtener_aditivos()
    nombres_aditivos = [a['Nombre'] for a in aditivos_cat]
    
    aditivos_seleccionados = st.sidebar.multiselect(
        "Seleccionar Aditivos",
        options=nombres_aditivos,
        key="aditivos_seleccion"
    )
    
    aditivos_config = []
    
    if aditivos_seleccionados:
        with st.sidebar.expander("Configurar Aditivos", expanded=True):
            for aditivo in aditivos_seleccionados:
                st.markdown(f"**{aditivo}**")
                datos_ad = next((a for a in aditivos_cat if a['Nombre'] == aditivo), None)
                
                dosis_def = 0.5
                densidad_def = 1.2 
                if datos_ad:
                    dosis_def = float(datos_ad.get('Dosis_Min', 0.5))
                    densidad_def = float(datos_ad.get('Densidad', 1.2))
                
                col_dosis, col_dens = st.columns(2)
                with col_dosis:
                    dosis = st.number_input(f"% Dosis ({aditivo})", min_value=0.0, max_value=10.0, value=dosis_def, step=0.1, key=f"dosis_{aditivo}")
                with col_dens:
                    densidad = st.number_input(f"Densidad (kg/L)", min_value=0.5, max_value=3.0, value=densidad_def, step=0.1, key=f"dens_{aditivo}")
                
                aditivos_config.append({'nombre': aditivo, 'dosis_pct': dosis, 'densidad_kg_lt': densidad})

    # Botón guardar JSON local
    st.sidebar.markdown("### 💾 Local")
    nombre_archivo = st.sidebar.text_input("Nombre Archivo", value=f"Dosificacion_{datetime.now().strftime('%Y%m%d')}", key="nombre_archivo_local")
    
    # Retorna diccionario con todos los inputs
    return {
        'numero_informe': numero_informe,
        'cliente': cliente,
        'obra': obra,
        'fecha': fecha,
        'resistencia_fc': resistencia_fc,
        'desviacion_std': desviacion_std,
        'fraccion_def': fraccion_def,
        'consistencia': consistencia,
        'asentamiento': asentamiento,
        'tmn': tmn,
        'aire_porcentaje': aire_porcentaje,
        'tipo_cemento': tipo_cemento,
        'densidad_cemento': densidad_cemento,
        'condicion_exposicion': condicion_exposicion,
        'aditivos_config': aditivos_config,
        'nombre_archivo_local': nombre_archivo 
    }

def input_aridos_ui():
    """Genera el formulario para ingresar datos de áridos (Catalogo + Inputs)."""
    """Genera el formulario para ingresar datos de áridos (Catalogo + Inputs)."""
    
    # Detectar si hay áridos pre-cargados desde el Catálogo Histórico
    aridos_precargados = st.session_state.get('aridos_precargados', [])
    
    if aridos_precargados:
        st.success(f"✅ {len(aridos_precargados)} árido(s) pre-cargado(s) desde el Catálogo Histórico")
        usar_precargados = st.checkbox("Usar áridos pre-cargados", value=True)
        
        if usar_precargados:
            # Mostrar resumen
            with st.expander("📋 Ver Áridos Pre-cargados"):
                for i, arido in enumerate(aridos_precargados):
                    st.markdown(f"**{i+1}. {arido['nombre']}** - DRS: {arido['DRS']:.0f} kg/m³ - Abs: {arido['absorcion']*100:.2f}%")
            
            # Convertir al formato esperado
            aridos_resultado = []
            for arido in aridos_precargados:
                aridos_resultado.append({
                    'nombre': arido['nombre'],
                    'tipo': arido['tipo'],
                    'DRS': arido['DRS'],
                    'DRSSS': arido['DRSSS'],
                    'absorcion': arido['absorcion'],
                    'granulometria': arido['granulometria']
                })
            
            return aridos_resultado
    
    # Flujo normal (manual)
    num_aridos = st.radio("Número de áridos", options=[2, 3], index=0, horizontal=True)
    aridos = []
    cols = st.columns(num_aridos)
    aridos_cat = catalogs.obtener_aridos()
    
    # Filtrar duplicados y vacíos
    nombres_unicos = sorted(list(set([a['Nombre'] for a in aridos_cat if a.get('Nombre')])))
    opciones_cat = ["Personalizado"] + nombres_unicos
    
    for i in range(num_aridos):
        with cols[i]:
            st.markdown(f"#### Árido {i+1}")
            # Selectbox para elegir del catálogo (Nombre Familia)
            sel_cat = st.selectbox("📂 Catálogo", options=opciones_cat, key=f"cat_arido_{i}")
            
            # Lógica para seleccionar MUESTRA específica si hay múltiples
            datos = None
            if sel_cat != "Personalizado":
                # Buscar todas las coincidencias
                coincidencias = [a for a in aridos_cat if a['Nombre'] == sel_cat]
                
                if len(coincidencias) > 1:
                    # Crear etiquetas para identificar las muestras
                    # Buscamos columnas distintivas: Identificación, Lote, Fecha, o ID
                    opciones_muestra = []
                    for idx, c in enumerate(coincidencias):
                        # Intentar construir un label útil
                        label_parts = []
                        if c.get('Identificacion'): label_parts.append(str(c['Identificacion']))
                        elif c.get('Lote'): label_parts.append(str(c['Lote']))
                        
                        if c.get('Fecha'): label_parts.append(str(c['Fecha']))
                        
                        if not label_parts:
                            label = f"Muestra #{idx+1}"
                        else:
                            label = " - ".join(label_parts)
                        
                        opciones_muestra.append(label)
                    
                    sel_muestra = st.selectbox("🔖 Lote / Muestra", opciones_muestra, key=f"sel_muestra_{i}")
                    idx_elegido = opciones_muestra.index(sel_muestra)
                    datos = coincidencias[idx_elegido]
                elif len(coincidencias) == 1:
                    datos = coincidencias[0]
            
            # Valores por defecto base
            nombre_def, drs_def, drsss_def, abs_def, tipo_def = "Árido", 2650.0, 2700.0, 1.0, "Grueso"
            gran_def = [0.0] * 12 # Default vacío
            
            # Si se selecciona algo del catálogo, sobrescribir defaults
            # Si se selecciona algo del catálogo, sobrescribir defaults
            if datos: # Ya tenemos los datos exactos (sea único o elegido)
                nombre_def = datos.get('Nombre', nombre_def)
                tipo_def = datos.get('Tipo', tipo_def)
                
                def safe_float(val, default=0.0):
                    if val is None: return default
                    if isinstance(val, (int, float)): return float(val)
                    try:
                        return float(str(val).replace(',', '.'))
                    except (ValueError, TypeError):
                        return default

                drs_def = safe_float(datos.get('Densidad_Real'), drs_def)
                abs_def = safe_float(datos.get('Absorcion'), abs_def)
                
                # Calcular DRSSS si no viene
                v_drsss = datos.get('Densidad_SSS')
                if v_drsss and safe_float(v_drsss) > 0:
                    drsss_def = safe_float(v_drsss)
                else:
                    drsss_def = drs_def * (1 + abs_def/100)
                    
                # Cargar Granulometría usando el Mapeo
                    from config.config import MAPEO_COLUMNAS_EXCEL, TAMICES_ASTM
                    
                    # Crear diccionario de granulometría mapeada
                    gran_leida = {}
                    for col_excel, col_astm in MAPEO_COLUMNAS_EXCEL.items():
                        # Intentar buscar la columna del excel en los datos
                        val = datos.get(col_excel)
                        if val is not None:
                            gran_leida[col_astm] = safe_float(val)
                    
                    # Rellenar lista gran_def ordenada según TAMICES_ASTM
                    if gran_leida:
                        gran_def = []
                        for tamiz in TAMICES_ASTM:
                            gran_def.append(gran_leida.get(tamiz, 0.0))

            # TRUCO: Usar key dependiente de sel_cat para resetear inputs al cambiar selección
            sufijo = f"{i}_{sel_cat}" 
            
            nombre = st.text_input("Nombre", nombre_def, key=f"nombre_{sufijo}")
            
            # Indice para tipo
            idx_tipo = 0
            opts_tipo = ["Grueso", "Intermedio", "Fino"]
            if tipo_def in opts_tipo:
                 idx_tipo = opts_tipo.index(tipo_def)
                 
            tipo = st.selectbox("Tipo", opts_tipo, index=idx_tipo, key=f"tipo_{sufijo}")
            drs = st.number_input("DRS", min_value=1500.0, max_value=3500.0, value=drs_def, format="%.0f", key=f"drs_{sufijo}")
            drsss = st.number_input("DRSSS", min_value=1500.0, max_value=3500.0, value=drsss_def, format="%.0f", key=f"drsss_{sufijo}")
            absorcion = st.number_input("Abs %", min_value=0.0, max_value=10.0, value=abs_def, step=0.1, format="%.2f", key=f"abs_{sufijo}")
            
            st.markdown("**Granulometría**")
            
            # Pre-llenar granulometría según tipo si es genérico
            if sel_cat == "Personalizado" or all(x==0 for x in gran_def):
                if tipo == "Grueso": gran_def = [100, 100, 97, 76, 34, 21, 2, 1, 0, 0, 0, 0]
                elif tipo == "Fino": gran_def = [100, 100, 100, 100, 100, 100, 94, 74, 53, 37, 21, 8]
            
            granulometria = []
            cols_per_row = 7  # 7 columnas para que quepan 13 en 2 filas (7 y 6)
            
            # Asegurar que gran_def tenga la longitud correcta
            while len(gran_def) < len(TAMICES_ASTM):
                gran_def.append(0.0)

            # Generar inputs dinámicamente
            for i, tamiz_label in enumerate(TAMICES_ASTM):
                if i % cols_per_row == 0:
                    c_gran = st.columns(cols_per_row)
                
                with c_gran[i % cols_per_row]:
                     val = st.number_input(
                         tamiz_label, 
                         min_value=0.0, 
                         max_value=100.0, 
                         value=float(gran_def[i]), 
                         step=1.0, 
                         key=f"gran_{i}_{sufijo}"
                     )
                     granulometria.append(val)
            
            aridos.append({'nombre': nombre, 'tipo': tipo, 'DRS': drs, 'DRSSS': drsss, 'absorcion': absorcion/100, 'granulometria': granulometria})
            
    return aridos

def sidebar_user_info():
    """Footer del sidebar con usuario y logout."""
    if st.session_state.get('authenticated'):
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{st.session_state.get('user_name', 'Usuario')}**")
        if st.sidebar.button("Cerrar Sesión"):
            logout()

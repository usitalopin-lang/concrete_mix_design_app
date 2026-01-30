"""
Módulo de utilidades UI compartidas.
Contiene funciones de inicialización de estado y componentes de interfaz (sidebars, inputs)
que se reutilizan en las distintas páginas.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import (
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

    # NUEVO: Inputs Manuales de Diseño (Magallanes) - Movidos al tope
    col_ac, col_aire = st.sidebar.columns(2)
    with col_ac:
        razon_ac_manual = st.number_input(
            "Razón A/C Objetivo",
            min_value=0.20, max_value=1.50,
            value=DEFAULTS.get('razon_ac_manual', 0.43),
            step=0.01, format="%.2f",
            key="razon_ac_manual",
            help="Razón Agua/Cemento a utilizar en el diseño."
        )
    with col_aire:
        aire_litros_manual = st.number_input(
            "Aire Total (Litros)",
            min_value=0.0, max_value=100.0,
            value=40.0, step=1.0,
            key="aire_litros_manual",
            help="Volumen total de aire (atrapado + incorporado) en litros/m3."
        )

    condicion_exposicion = st.sidebar.selectbox(
        "Condición de Exposición (Ref)",
        options=EXPOSICION_OPCIONES,
        key="condicion_exposicion",
        help="Calculo estricto por resistencia. Durabilidad es solo referencia."
    )
    
    desviacion_std = st.sidebar.number_input(
        "Desviación estándar s (MPa)",
        min_value=1.0, max_value=10.0,
        value=1.5, step=0.5,
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

    from config import APLICACIONES_HORMIGON
    aplicacion = st.sidebar.selectbox(
        "Aplicación / Uso del Hormigón",
        options=APLICACIONES_HORMIGON,
        key="aplicacion",
        help="Define el uso final para que la IA y el diseño sean precisos (Bombeo, Pavimentos, etc.)"
    )

    st.sidebar.markdown("---")
    
    # Sección: Cemento (Catálogo)
    st.sidebar.markdown("### 🏭 Cemento")
    
    cementos_cat_raw = catalogs.obtener_cementos()
    
    # Deduplicar: crear mapeo "Marca - Tipo" -> Datos del primer registro encontrado
    cementos_dict = {}
    for c in cementos_cat_raw:
        label = f"{c['Marca']} - {c['Tipo']}".strip()
        if label and label not in cementos_dict:
            cementos_dict[label] = c
            
    opciones_cemento = sorted(list(cementos_dict.keys()))
    
    # Fallback si no hay cementos
    if not opciones_cemento:
        opciones_cemento = ["Default"]
        cementos_dict = {"Default": {'Densidad': 3000.0}}

    def actualizar_densidad_cemento():
        if 'tipo_cemento_sel' in st.session_state:
             sel = st.session_state.tipo_cemento_sel
             if sel in cementos_dict:
                 st.session_state.densidad_cemento = float(cementos_dict[sel]['Densidad'])

    tipo_cemento_sel = st.sidebar.selectbox(
        "Tipo de cemento",
        options=opciones_cemento,
        key="tipo_cemento_sel",
        on_change=actualizar_densidad_cemento
    )
    
    if 'densidad_cemento' not in st.session_state:
        # Inicializar con la densidad del primer elemento de opciones
        st.session_state.densidad_cemento = float(cementos_dict[opciones_cemento[0]]['Densidad'])

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
    # Deduplicar nombres de aditivos
    nombres_aditivos = sorted(list(set([str(a['Nombre']).strip() for a in aditivos_cat if a.get('Nombre')])))
    
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
                caracteristica = ""
                if datos_ad:
                    dosis_def = datos_ad.get('Dosis_Min', 0.5)
                    densidad_def = datos_ad.get('Densidad', 1.2)
                    caracteristica = datos_ad.get('Caracteristica', "")
                
                if caracteristica:
                    st.caption(f"ℹ️ {caracteristica}")
                
                col_dosis, col_dens = st.columns(2)
                with col_dosis:
                    # Permitir elegir modo de dosis (Porcentaje o Fijo L/m3)
                    modo_dosis = st.radio("Unidad", ["% p.c.", "L/m³"], horizontal=True, key=f"modo_{aditivo}")
                    
                    help_dosis = f"Sugerido (Catálogo): Min: {datos_ad.get('Dosis_Min', 0)} / Max: {datos_ad.get('Dosis_Max', 0)}" if datos_ad else ""
                    
                    if modo_dosis == "L/m³":
                        max_fijo = 100.0
                        val_ini = max(0.0, min(float(dosis_def), max_fijo))
                        val_dosis = st.number_input(f"L/m³", min_value=0.0, max_value=max_fijo, value=val_ini, step=0.1, key=f"d_fija_{aditivo}", help=help_dosis)
                        item_ad = {'nombre': aditivo, 'dosis_fija_lt': val_dosis}
                    else:
                        max_pct = 100.0
                        val_ini = max(0.0, min(float(dosis_def), max_pct))
                        val_dosis = st.number_input(f"% Dosis", min_value=0.0, max_value=max_pct, value=val_ini, step=0.1, key=f"d_pct_{aditivo}", help=help_dosis)
                        item_ad = {'nombre': aditivo, 'dosis_pct': val_dosis}
                
                with col_dens:
                    st.write("") # Alineación visual
                    st.write("") 
                    densidad = st.number_input(f"Densidad (kg/L)", min_value=0.0, max_value=3.0, value=float(densidad_def), step=0.01, key=f"dens_{aditivo}")
                    item_ad['densidad_kg_lt'] = densidad
                
                aditivos_config.append(item_ad)

    # Botón guardar JSON local
    st.sidebar.markdown("### 💾 Local")
    nombre_archivo = st.sidebar.text_input("Nombre Archivo", value=f"Dosificacion_{datetime.now().strftime('%Y%m%d')}", key="nombre_archivo_local")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Sincronizar Datos (Nube)", help="Limpia el caché y lee las hojas de Google Sheets nuevamente."):
        st.cache_data.clear()
        st.success("Caché limpiado. Actualizando...")
        st.rerun()

    # Obtener el objeto cemento completo para metadatos
    cemento_obj = next((c for c in cementos_cat_raw if f"{c['Marca']} - {c['Tipo']}" == tipo_cemento_sel), {})
    
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
        'aplicacion': aplicacion,
        'razon_ac_manual': razon_ac_manual,
        'aire_litros_manual': aire_litros_manual,
        'tipo_cemento': tipo_cemento_sel,
        'cemento_datos': cemento_obj, # El objeto completo del catálogo
        'densidad_cemento': densidad_cemento,
        'condicion_exposicion': condicion_exposicion,
        'aditivos_config': aditivos_config,
        'nombre_archivo_local': nombre_archivo 
    }

def input_aridos_ui():
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
    
    # Filtrar duplicados y vacíos, asegurando que todos sean strings para el sort
    nombres_unicos = sorted(list(set([str(a['Nombre']).strip() for a in aridos_cat if a.get('Nombre')])))
    opciones_cat = ["Personalizado"] + nombres_unicos
    
    for i_arido in range(num_aridos):
        with cols[i_arido]:
            st.markdown(f"#### Árido {i_arido+1}")
            # Selectbox para elegir del catálogo (Nombre Familia)
            sel_cat = st.selectbox("📂 Catálogo", options=opciones_cat, key=f"cat_arido_{i_arido}")
            
            # Lógica para seleccionar MUESTRA específica si hay múltiples
            datos = None
            sel_muestra_idx = -1 # Para hash de key

            if sel_cat != "Personalizado":
                # Buscar todas las coincidencias
                coincidencias_raw = [a for a in aridos_cat if a['Nombre'] == sel_cat]
                
                # --- FILTRO ESTRICTO PARA DISEÑO ---
                # Solo mostrar muestras con Densidad Real y al menos un tamiz con valor > 0
                coincidencias = []
                for c in coincidencias_raw:
                    # Helper para lidiar con valores no numéricos en Excel (ej: "-", "N/A")
                    def get_val(val):
                        if val is None: return 0.0
                        if isinstance(val, (int, float)): return float(val)
                        try:
                            return float(str(val).replace(',', '.'))
                        except:
                            return 0.0

                    # Verificar Densidad
                    tiene_densidad = get_val(c.get('Densidad_Real')) > 0
                    
                    # Verificar Granulometría (al menos un tamiz con valor > 0)
                    tiene_granulometria = False
                    from config import MAPEO_COLUMNAS_EXCEL
                    for col_excel in MAPEO_COLUMNAS_EXCEL.keys():
                        if get_val(c.get(col_excel)) > 0:
                            tiene_granulometria = True
                            break
                    
                    if tiene_densidad and tiene_granulometria:
                        coincidencias.append(c)
                
                if not coincidencias and coincidencias_raw:
                    st.warning(f"⚠️ Las {len(coincidencias_raw)} muestras de '{sel_cat}' en el catálogo están incompletas (faltan densidades o tamices).")

                if len(coincidencias) > 1:
                    # Crear etiquetas para identificar las muestras
                    # Buscamos columnas distintivas: id_muestra (N° Muestra), Identificacion, Lote, Fecha
                    opciones_muestra = []
                    for idx_m, c_m in enumerate(coincidencias):
                        # Intentar construir un label útil
                        label_parts = []
                        if c_m.get('id_muestra'): label_parts.append(str(c_m['id_muestra'])) # Prioridad 1: N° Muestra
                        if c_m.get('Identificacion'): label_parts.append(str(c_m['Identificacion']))
                        elif c_m.get('Lote'): label_parts.append(str(c_m['Lote']))
                        
                        if c_m.get('Fecha'): label_parts.append(str(c_m['Fecha']))
                        
                        if not label_parts:
                            label = f"Muestra #{idx_m+1}"
                        else:
                            label = " - ".join(label_parts)
                        
                        opciones_muestra.append(label)
                    
                    sel_muestra = st.selectbox("🔖 Lote / Muestra", opciones_muestra, key=f"sel_muestra_{i_arido}")
                    sel_muestra_idx = opciones_muestra.index(sel_muestra)
                    datos = coincidencias[sel_muestra_idx]
                elif len(coincidencias) == 1:
                    datos = coincidencias[0]
                    sel_muestra_idx = 0
            
            # Valores por defecto base
            from config import MAPEO_COLUMNAS_EXCEL, TAMICES_ASTM
            nombre_def, drs_def, drsss_def, abs_def, tipo_def = "Árido", 2650.0, 2700.0, 1.0, "Grueso"
            nombre_def, drs_def, drsss_def, abs_def, tipo_def = "Árido", 2650.0, 2700.0, 1.0, "Grueso"
            gran_def = [0.0] * 13 # Match TAMICES_ASTM length
            
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
                    
                    # CORRECCIÓN AUTOMÁTICA: Asegurar Granulometría Monótona (100% arriba de un 100%)
                    # Y llenar con 0 debajo de un 0 de forma coherente.
                    # Pasando[i] >= Pasando[i+1]
                    for idx_f in range(len(gran_def) - 2, -1, -1):
                        # Monotonicidad Básica: Retenido Acumulado no puede disminuir -> Pasante no puede aumentar
                        # Pasante[i] >= Pasante[i+1] (Tamiz i es más grande que i+1)
                        # Si dato[i+1] es mayor que dato[i], algo anda mal. 
                        # Asumimos que el dato "presente" manda. 
                        # CORRECCION: Si tengo 100 en #4 (idx 6) y 0 en 3/8 (idx 5), #4 manda? No, 3/8 manda.
                        # PERO aquí queremos rellenar huecos.
                        
                        val_actual = gran_def[idx_f]
                        val_menor = gran_def[idx_f + 1]
                        
                        # Estrategia de Relleno:
                        # 1. Si el tamiz más grande tiene 0 y el pequeño tiene valor -> Asumir que el grande es 100? No necesariamente.
                        # 2. Si el tamiz pequeño tiene 0 y el grande tiene valor -> El pequeño es 0? Sí, físico.
                        pass

                    # Lógica Robusta de Relleno 
                    # 1. Propagar 100% hacia arriba (Tamices grandes)
                    first_100_idx = -1
                    for idx_f in range(len(gran_def) - 1, -1, -1): # Desde el más fino al grande
                         if gran_def[idx_f] >= 99.0:
                             first_100_idx = idx_f
                             # Propagar a todos los tamices MÁS GRANDES (índices menores)
                             for prev_idx in range(idx_f):
                                 gran_def[prev_idx] = 100.0
                    
                    # 2. Propagar 0% hacia abajo (Tamices finos)
                    # Si un tamiz grande es 0 (y no es el 2"), los menores son 0
                    for idx_f in range(len(gran_def)):
                        if gran_def[idx_f] <= 0.5:
                             # Propagar 0 a los que siguen (índices mayores = más finos)
                             for next_idx in range(idx_f + 1, len(gran_def)):
                                 gran_def[next_idx] = 0.0

            # TRUCO: Usar key dependiente de sel_cat y sel_muestra_idx para forzar refresco
            # Si cambiamos de muestra, el sufijo cambia, y los defaults se recargan
            sufijo = f"{i_arido}_{sel_cat}_{sel_muestra_idx}" 
            
            nombre = st.text_input("Nombre", nombre_def, key=f"nombre_{sufijo}")
            
            # Indice para tipo
            idx_tipo = 0
            opts_tipo = ["Grueso", "Intermedio", "Fino"]
            if tipo_def in opts_tipo:
                 idx_tipo = opts_tipo.index(tipo_def)
                 
            tipo = st.selectbox("Tipo", opts_tipo, index=idx_tipo, key=f"tipo_{sufijo}")
            
            # --- Ajuste de Seguridad: Evitar BelowMinError/AboveMaxError ---
            drs_min, drs_max = 1000.0, 4000.0
            abs_min, abs_max = 0.0, 20.0
            
            drs_val = max(drs_min, min(float(drs_def), drs_max))
            drsss_val = max(drs_min, min(float(drsss_def), drs_max))
            abs_val = max(abs_min, min(float(abs_def), abs_max))
            
            drs = st.number_input("DRS (Densidad Real Seca)", min_value=drs_min, max_value=drs_max, value=drs_val, format="%.0f", key=f"drs_{sufijo}", help="kg/m³")
            drsss = st.number_input("DRSSS (Densidad Real SSS)", min_value=drs_min, max_value=drs_max, value=drsss_val, format="%.0f", key=f"drsss_{sufijo}", help="kg/m³")
            absorcion = st.number_input("Abs % (Absorción)", min_value=abs_min, max_value=abs_max, value=abs_val, step=0.1, format="%.2f", key=f"abs_{sufijo}")
            
            st.markdown("**Granulometría**")
            
            # Pre-llenar granulometría según tipo si es genérico
            if sel_cat == "Personalizado" or all(x==0 for x in gran_def):
                if tipo == "Grueso": gran_def = [100, 100, 97, 76, 34, 21, 2, 1, 0, 0, 0, 0]
                elif tipo == "Fino": gran_def = [100, 100, 100, 100, 100, 100, 94, 74, 53, 37, 21, 8]
            
            granulometria = []
            cols_per_row = 4  # Menos columnas para que se vean bien los números
            
            # Asegurar que gran_def tenga la longitud correcta
            while len(gran_def) < len(TAMICES_ASTM):
                gran_def.append(0.0)

            # Generar inputs dinámicamente
            for idx_t, tamiz_label in enumerate(TAMICES_ASTM):
                if idx_t % cols_per_row == 0:
                    c_gran = st.columns(cols_per_row)
                
                with c_gran[idx_t % cols_per_row]:
                     val = st.number_input(
                         tamiz_label, 
                         min_value=0.0, 
                         max_value=100.0, 
                         value=float(gran_def[idx_t]), 
                         step=1.0, 
                         key=f"gran_{idx_t}_{sufijo}"
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

def render_expert_guide():
    """Renderiza el expander informativo con la guía de selección de estrategias."""
    with st.expander("🎓 Guía de Experto: ¿Qué curva debo usar?", expanded=False):
        st.markdown("""
        **🏗️ Selección de Estrategia según Aplicación**
        
        Esta aplicación incluye los motores de optimización más avanzados del mundo. Elige tu herramienta según el hormigón y el método constructivo que vas a utilizar:

        #### 1. 🏭 Prefabricados Secos (Adoquines, Soleras, Bloques)
        *   **Herramienta:** Power 45 / Fuller
        *   **Meta:** Máxima Densidad / Empaquetamiento.
        *   **Por qué:** Estas máquinas "vibran y prensan" mezclas muy secas (Cono 0). Necesitas que los áridos encajen perfectamente (como un tetris) para que el bloque tenga resistencia inmediata y no se desmorone al desmoldar.
        *   **Shilstone:** Busca la Zona I (Rocky) o la frontera inferior de la Zona II, con bajo contenido de mortero.

        #### 2. 🛣️ Pavimentos Slipform (Moldaje Deslizante / Tren Pavimentador)
        *   **Herramienta:** Tarantula Curve (Tyler Ley) / Illinois Tollway
        *   **Meta:** Estabilidad de Borde y "Green Strength".
        *   **Por qué:** Para máquinas de alto rendimiento (Wirtgen/Gomaco), el hormigón debe ser "tixotrópico": fluido al vibrar, pero sólido al instante (en segundos) para que el borde no se caiga al pasar la máquina.
        *   **Ideal:** Si tu curva entra en la "Caja Tarántula" o banda de Illinois, garantizas que el pavimento no se deforme (Edge Slump).

        #### 3. 👷 Pavimentos Manuales (Moldes Fijos) y Pisos Industriales
        *   **Herramienta:** Shilstone (Zona II Alta)
        *   **Meta:** Acabado Superficial ("Finishability") y respuesta a la cercha.
        *   **Por qué:** A diferencia del Slipform, aquí el hormigón está contenido por moldes fijos. La prioridad no es que se sostenga solo, sino que tenga suficiente "crema" (arena media + pasta) para que la cercha vibratoria cierre los poros y el platacho deje una superficie lisa sin esfuerzo excesivo.
        *   **Advertencia:** No uses la estrategia Slipform aquí; te quedará una mezcla muy áspera ("huesuda") y difícil de terminar a mano.

        #### 4. 🏢 Hormigón Bombeable y Edificación (Docilidad > 10cm)
        *   **Herramienta:** Shilstone (Coarseness Factor Chart)
        *   **Meta:** Reología y Lubricación de Tubería.
        *   **Por qué:** Para bombear, la física cambia: necesitas una capa de mortero que lubrique las paredes del tubo para que la piedra deslice.
        *   **Objetivo:** Apunta al Centro de la ZONA II (Transfer Zone).
        *   **⚠️ Cuidado:** Si caes en Zona I (Abajo/Izquierda), tendrás segregación y bloquearás la bomba (mucha piedra, poca crema).
        *   **⚠️ Cuidado:** Si caes en Zona III (Arriba), será pegajoso, demandará mucha agua y podría fisurarse.
        """)

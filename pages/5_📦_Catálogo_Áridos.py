import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modules.utils_ui import inicializar_estado, sidebar_user_info
from modules.historical_data import cargar_aridos_historico, obtener_arido_promedio

st.set_page_config(page_title="Catálogo de Áridos", page_icon="📦", layout="wide")

inicializar_estado()

if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes iniciar sesión.")
    st.stop()

sidebar_user_info()

st.title("📦 Catálogo Histórico de Áridos")
st.markdown("Selecciona áridos históricos y pre-carga sus propiedades promedio para usar en el diseño.")

# Inicializar lista de áridos pre-cargados
if 'aridos_precargados' not in st.session_state:
    st.session_state.aridos_precargados = []

# Cargar datos históricos
with st.spinner("Cargando base de datos de áridos..."):
    df_aridos = cargar_aridos_historico()

if df_aridos.empty:
    st.error("❌ No se pudo cargar la planilla de Áridos. Verifica que la hoja 'Cat_Aridos' exista en Google Sheets.")
    st.stop()

# Obtener tipos únicos
tipos_disponibles = sorted(df_aridos['tipo_material'].dropna().unique().tolist())

st.markdown("---")

# Sección de selección
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🔍 Seleccionar Árido")
    
    tipo_seleccionado = st.selectbox(
        "Tipo de Árido",
        options=tipos_disponibles,
        help="Selecciona el tipo de árido del cual quieres obtener el promedio histórico"
    )
    
    col_fecha1, col_fecha2 = st.columns(2)
    with col_fecha1:
        fecha_desde = st.date_input(
            "Desde",
            value=datetime.now().date() - timedelta(days=180),
            help="Fecha inicial del rango"
        )
    with col_fecha2:
        fecha_hasta = st.date_input(
            "Hasta",
            value=datetime.now().date(),
            help="Fecha final del rango"
        )
    
    if st.button("📊 Calcular Promedio", type="primary"):
        resultado = obtener_arido_promedio(tipo_seleccionado, fecha_desde, fecha_hasta)
        
        if resultado is None:
            st.warning(f"⚠️ No se encontraron muestras de '{tipo_seleccionado}' en el rango seleccionado.")
            st.info("💡 **Sugerencia:** Amplía el rango de fechas o verifica el nombre del árido.")
        else:
            st.session_state.resultado_arido_actual = resultado
            st.success(f"✅ Promedio calculado con {resultado['n_muestras']} muestras")

with col2:
    st.markdown("### 📋 Áridos Pre-cargados")
    if st.session_state.aridos_precargados:
        for i, arido in enumerate(st.session_state.aridos_precargados):
            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"**{i+1}.** {arido['nombre']}")
            if col_b.button("🗑️", key=f"del_{i}"):
                st.session_state.aridos_precargados.pop(i)
                st.rerun()
    else:
        st.info("Ningún árido pre-cargado aún")
    
    if st.button("🧹 Limpiar Todo"):
        st.session_state.aridos_precargados = []
        st.rerun()

st.markdown("---")

# Mostrar resultado si existe
if 'resultado_arido_actual' in st.session_state:
    res = st.session_state.resultado_arido_actual
    
    st.markdown("### 📈 Resultado del Promedio")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Muestras", res['n_muestras'])
    col_m2.metric("DRS (kg/m³)", f"{res['DRS']:.0f}")
    col_m3.metric("DRSSS (kg/m³)", f"{res['DRSSS']:.0f}")
    col_m4.metric("Absorción (%)", f"{res['absorcion']*100:.2f}")
    
    st.caption(f"📅 Período: {res['fecha_primero']} → {res['fecha_ultimo']}")
    
    # Granulometría
    st.markdown("#### Granulometría Promedio")
    tamices_nombres = ['1 1/2"', '1"', '3/4"', '1/2"', '3/8"', 'N°4', 'N°8', 'N°16', 'N°30', 'N°50', 'N°100', 'N°200']
    df_gran = pd.DataFrame({
        'Tamiz': tamices_nombres,
        '% Pasante': res['granulometria']
    })
    st.dataframe(df_gran, use_container_width=True)
    
    # Detalle de muestras (si hay pocas)
    if res['muestras_detalle']:
        with st.expander("🔬 Ver Detalle de Muestras Individuales"):
            df_detalle = pd.DataFrame(res['muestras_detalle'])
            st.dataframe(df_detalle, use_container_width=True)
    
    # Botón para agregar a la lista
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("➕ Usar este Árido", type="primary"):
            # Verificar si ya existe
            nombres_existentes = [a['nombre'] for a in st.session_state.aridos_precargados]
            if res['nombre'] in nombres_existentes:
                st.warning("⚠️ Este árido ya está en la lista")
            else:
                st.session_state.aridos_precargados.append(res)
                st.success(f"✅ '{res['nombre']}' agregado a la lista")
                st.rerun()

# Botón para ir a Diseño
st.markdown("---")
if st.session_state.aridos_precargados:
    st.success(f"✅ Tienes {len(st.session_state.aridos_precargados)} árido(s) pre-cargado(s)")
    st.info("💡 **Siguiente paso:** Ve a la página '🏗️ Diseño' y los áridos se cargarán automáticamente.")

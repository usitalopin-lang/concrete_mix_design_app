
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.utils_ui import inicializar_estado, sidebar_user_info
from modules.historical_data import cargar_dosificaciones, cargar_resistencias, unir_dosificacion_resistencia

st.set_page_config(page_title="Análisis Histórico", page_icon="📈", layout="wide")

inicializar_estado()

if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes iniciar sesión.")
    st.stop()

sidebar_user_info()

st.title("📈 Análisis de Datos Históricos")
st.markdown("Visualización cruzada de **Recetas (Dosificaciones)** vs **Desempeño Real (Resistencias)**.")

# Cargar Datos
with st.spinner("Cargando bases de datos históricas..."):
    df_dos = cargar_dosificaciones()
    df_res = cargar_resistencias()

if df_dos.empty:
    st.error("❌ No se pudo cargar la planilla de Dosificaciones.")
    st.stop()

if df_res.empty:
    st.warning("⚠️ No se pudo cargar Resistencias. Mostrando solo recetas.")
    df_final = df_dos
else:
    # Unir
    df_final = unir_dosificacion_resistencia(df_dos, df_res)
    st.success(f"✅ Datos cruzados: {len(df_final)} recetas analizadas con historial.")

# Filtros
st.sidebar.header("🔍 Filtros")
grados = sorted(df_final['grado'].unique().tolist()) if 'grado' in df_final.columns else []
sel_grado = st.sidebar.multiselect("Grado", grados, default=grados[:1] if grados else None)

if sel_grado:
    df_view = df_final[df_final['grado'].isin(sel_grado)]
else:
    df_view = df_final

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Recetas Analizadas", len(df_view))
if 'promedio_fc' in df_view.columns:
    avg_fc = df_view['promedio_fc'].mean()
    c2.metric("Resistencia Media Global", f"{avg_fc:.1f} MPa")
    
    avg_std = df_view['desviacion_std'].mean()
    c3.metric("Desviación Std Promedio", f"{avg_std:.2f} MPa")

# Tablas y Gráficos
tab1, tab2 = st.tabs(["📊 Análisis Cruzado", "📋 Datos Crudos"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Dispersión de Resistencia por Grado")
        if 'promedio_fc' in df_view.columns and 'grado' in df_view.columns:
            fig = px.box(df_view, x="grado", y="promedio_fc", points="all", 
                         title="Distribución de Resistencias Reales por Grado",
                         color="grado")
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.markdown("### Recetas más usadas")
        if 'clave_mix' in df_view.columns:
            top_mixes = df_view['clave_mix'].value_counts().head(10)
            st.dataframe(top_mixes)

    st.markdown("### Detalle de Recetas con Desviación Real")
    cols_show = ['codigo', 'grado', 'tmn', 'docilidad', 'cemento_kg', 'agua_lt']
    if 'n_muestras' in df_view.columns:
        cols_show += ['n_muestras', 'promedio_fc', 'desviacion_std']
    
    # Filtrar columnas que existen
    cols_show = [c for c in cols_show if c in df_view.columns]
    st.dataframe(df_view[cols_show], use_container_width=True)

with tab2:
    st.subheader("Dosificaciones (Raw)")
    st.dataframe(df_dos)
    
    if not df_res.empty:
        st.subheader("Resistencias (Raw)")
        st.dataframe(df_res)

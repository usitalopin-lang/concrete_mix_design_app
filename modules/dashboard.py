"""
Módulo de Dashboard / Analítica.
Visualiza los KPIs históricos extraídos de la base de datos de proyectos.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from modules import database

def render_dashboard():
    """Renderiza el dashboard principal de analítica."""
    st.markdown("## 📊 Dashboard de Inteligencia")
    
    if not st.session_state.get('authenticated'):
        st.warning("Inicia sesión para ver tus estadísticas.")
        return

    # Cargar datos
    with st.spinner("Cargando métricas históricas..."):
        proyectos = database.cargar_proyectos_usuario(st.session_state.user_email)
    
    if not proyectos:
        st.info("Aún no tienes proyectos guardados con métricas históricas.")
        return

    df = pd.DataFrame(proyectos)
    
    # Conversión de tipos si es necesario
    numeric_cols = ['fc_objetivo', 'cemento_kg', 'agua_lt', 'razon_ac']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # KPIs Principales
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric("Total Proyectos", len(df))
    
    with kpi2:
        if 'cemento_kg' in df.columns:
            avg_cem = df['cemento_kg'].mean()
            st.metric("Consumo Promedio Cemento", f"{avg_cem:.0f} kg/m³")
    
    with kpi3:
        if 'fc_objetivo' in df.columns:
            avg_fc = df['fc_objetivo'].mean()
            st.metric("Resistencia Promedio", f"{avg_fc:.1f} MPa")
            
    st.markdown("---")
    
    # Gráfico 1: Relación Resistencia vs Cemento
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 📉 Eficiencia (Cemento vs Resistencia)")
        if 'cemento_kg' in df.columns and 'fc_objetivo' in df.columns:
            fig1 = px.scatter(
                df, 
                x='fc_objetivo', 
                y='cemento_kg',
                color='razon_ac' if 'razon_ac' in df.columns else None,
                hover_data=['nombre_proyecto'],
                title="Consumo de Cemento vs Resistencia",
                labels={'fc_objetivo': "f'c (MPa)", 'cemento_kg': "Cemento (kg/m³)", 'razon_ac': "Razón A/C"}
            )
            st.plotly_chart(fig1, use_container_width=True)
            
    with col_g2:
        st.markdown("#### 📅 Evolución en el Tiempo")
        if 'timestamp' in df.columns and 'cemento_kg' in df.columns:
            df['fecha'] = pd.to_datetime(df['timestamp'])
            fig2 = px.line(
                df.sort_values('fecha'), 
                x='fecha', 
                y='cemento_kg',
                markers=True,
                title="Historial de Consumo de Cemento"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Tabla de Datos
    with st.expander("Ver Datos Crudos"):
        st.dataframe(df)

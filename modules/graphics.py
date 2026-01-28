"""
Módulo de Gráficos Interactivos (Plotly)
Genera visualizaciones profesionales e interactivas para la aplicación.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional, Tuple

# Colores corporativos y profesionales
COLOR_PRIMARIO = '#1f77b4'  # Azul profesional
COLOR_SECUNDARIO = '#ff7f0e'  # Naranja
COLOR_BUENO = '#2ca02c'     # Verde
COLOR_ADVERTENCIA = '#d62728' # Rojo
COLOR_FONDO = '#ffffff'
COLOR_GRILLA = '#e5e5e5'

def mostrar_resultados_faury(resultados: Dict):
    """
    Muestra los resultados del diseño Faury-Joisel en formato tabular.
    
    Args:
        resultados: Diccionario con resultados del diseño
    """
    import streamlit as st
    import pandas as pd
    
    st.markdown("### 📊 Resultados del Diseño Faury-Joisel")
    
    # Métricas principales
    # Calcular Pasta (Agua + Cemento + Aire opcionalmente, pero purista es Cemento+Agua)
    # Volumen Cemento = Peso / Densidad
    densidad_cemento = 3.0 # Default si no viene
    if 'cemento' in resultados and 'densidad' in resultados['cemento']:
         densidad_cemento = resultados['cemento']['densidad']
    
    vol_cemento = resultados.get('cemento', {}).get('cantidad', 0) / densidad_cemento
    vol_agua = resultados.get('agua_cemento', {}).get('agua_total', 0)
    vol_aire = resultados.get('aire', {}).get('volumen', 0)
    
    # Pasta Cemento + Agua
    vol_pasta = vol_cemento + vol_agua
    pct_pasta = (vol_pasta / 1000.0) * 100
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Cemento", f"{resultados.get('cemento', {}).get('cantidad', 0)} kg/m³")
    with col2:
        st.metric("Agua", f"{resultados.get('agua_cemento', {}).get('agua_total', 0)} L/m³")
    with col3:
        st.metric("A/C", f"{resultados.get('agua_cemento', {}).get('razon', 0)}")
    with col4:
        st.metric("Aire", f"{resultados.get('aire', {}).get('volumen', 0)} L/m³")
    with col5:
        st.metric("Pasta", f"{vol_pasta:.0f} L/m³", help=f"Volumen Pasta (Cemento+Agua): {pct_pasta:.1f}% del total")

    
    # Tabla de cantidades
    st.markdown("#### Cantidades de Materiales")
    data_materiales = {
        'Material': ['Cemento'] + list(resultados['cantidades_kg_m3'].keys()) + ['Agua Total', 'Aire'],
        'Cantidad': [
            f"{resultados['cemento']['cantidad']:.1f} kg",
            *[f"{v:.1f} kg" for v in resultados['cantidades_kg_m3'].values()],
            f"{resultados['agua_cemento']['agua_total']:.1f} L",
            f"{resultados['aire']['volumen']:.1f} L"
        ]
    }
    df_mat = pd.DataFrame(data_materiales)
    st.dataframe(df_mat, use_container_width=True, hide_index=True)
    
    # Granulometría de la mezcla
    if 'granulometria_mezcla' in resultados and resultados['granulometria_mezcla']:
        st.markdown("#### Granulometría de la Mezcla")
        # Usar la longitud real de la granulometría
        gran_data = resultados['granulometria_mezcla']
        # Tamices estándar (12 elementos según TAMICES_MM en config)
        tamices_std = ['1.5"', '1"', '3/4"', '1/2"', '3/8"', '#4', '#8', '#16', '#30', '#50', '#100', '#200']
        
        # Ajustar longitud si es necesario
        tamices = tamices_std[:len(gran_data)]
        
        # Obtener datos de banda si existen
        banda = resultados.get('banda_trabajo', [])
        min_vals = [b[0] for b in banda[:len(tamices)]] if banda else [None]*len(tamices)
        max_vals = [b[1] for b in banda[:len(tamices)]] if banda else [None]*len(tamices)
        
        df_gran = pd.DataFrame({
            'Tamiz': tamices,
            '% Pasante': gran_data[:len(tamices)],
            'Límite Inf': min_vals,
            'Límite Sup': max_vals
        })
        st.dataframe(df_gran, use_container_width=True, hide_index=True)
        
        # --- Gráfico Logarítmico de Granulometría ---
        import plotly.graph_objects as go
        
        # Mapeo de tamices a apertura mm para eje X logarítmico
        tamiz_mm_map = {
            '1.5"': 37.5, '1"': 25.0, '3/4"': 19.0, '1/2"': 12.5, '3/8"': 9.5,
            '#4': 4.75, '#8': 2.36, '#16': 1.18, '#30': 0.60, '#50': 0.30, 
            '#100': 0.15, '#200': 0.075
        }
        
        # Obtener valores X (aperturas) filtrando los que existen en 'tamices'
        x_vals = []
        for t in tamices:
            x_vals.append(tamiz_mm_map.get(t, 0.1)) # Fallback 0.1 si no encuentra
            
        fig_gran = go.Figure()
        
        # Banda Superior
        if any(max_vals):
            # Filtrar Nones para graficar
            x_sup = [x for x, y in zip(x_vals, max_vals) if y is not None]
            y_sup = [y for y in max_vals if y is not None]
            
            fig_gran.add_trace(go.Scatter(
                x=x_sup, y=y_sup,
                mode='lines',
                name='Límite Superior',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate="Sup: %{y:.1f}%<extra></extra>"
            ))
            
        # Banda Inferior
        if any(min_vals):
            x_inf = [x for x, y in zip(x_vals, min_vals) if y is not None]
            y_inf = [y for y in min_vals if y is not None]
            
            fig_gran.add_trace(go.Scatter(
                x=x_inf, y=y_inf,
                mode='lines',
                name='Límite Inferior',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate="Inf: %{y:.1f}%<extra></extra>"
            ))

        # Curva Mezcla
        y_mezcla = gran_data[:len(tamices)]
        fig_gran.add_trace(go.Scatter(
            x=x_vals, y=y_mezcla,
            mode='lines+markers',
            name='Mezcla Diseñada',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6),
            hovertemplate="Mezcla: %{y:.1f}%<extra></extra>"
        ))
        
        fig_gran.update_layout(
            title="Curva Granulométrica (Escala Logarítmica)",
            xaxis=dict(
                title="Abertura (mm)", 
                type="log", 
                # autorange="reversed", # Comentado para match referencia (Menor -> Mayor izq->der)
                tickvals=[0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75, 9.5, 19.0, 37.5],
                ticktext=['#200', '#100', '#50', '#30', '#16', '#8', '#4', '3/8"', '3/4"', '1.5"'],
                gridcolor='#e6e6e6'
            ),
            yaxis=dict(
                title="% Pasante", 
                range=[0, 105],
                gridcolor='#e6e6e6'
            ),
            plot_bgcolor='white',
            hovermode="x unified",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig_gran, use_container_width=True)

# --- CONFIGURACIÓN ESTÉTICA CORPORATIVA ---
COLOR_PRIMARIO = '#1f77b4'    # Azul Ingeniería
COLOR_SECUNDARIO = '#ff7f0e'  # Naranja Contraste
COLOR_OK = '#2ca02c'          # Verde Éxito
COLOR_WARN = '#d62728'        # Rojo Alerta
COLOR_GRID = '#e6e6e6'
COLOR_FILL_REF = 'rgba(128, 128, 128, 0.1)' # Gris tenue para zonas de referencia

def _get_sieve_mm_map() -> Dict[str, float]:
    """Retorna mapeo estándar de tamices a mm."""
    return {
        '2"': 50.0, '1.5"': 37.5, '1"': 25.0, '3/4"': 19.0, '1/2"': 12.5, 
        '3/8"': 9.5, '#4': 4.75, '#8': 2.36, '#16': 1.18, '#30': 0.60, 
        '#50': 0.30, '#100': 0.15, '#200': 0.075
    }

def crear_grafico_shilstone_interactivo(cf: float, wf: float) -> go.Figure:
    """
    Genera el diagrama de Factor de Tosquedad (Coarseness Factor Chart).
    Dibuja la 'Trend Bar' diagonal correctamente.
    """
    fig = go.Figure()

    # --- Construcción de la Trend Bar (Zona II - Óptima) ---
    # La barra de tendencia suele definirse por una banda diagonal.
    # Usamos coordenadas aproximadas basadas en ACI / Iowa Method
    
    # Puntos del polígono para la Banda de Tendencia (Trend Bar) - Rectángulo Diagonal
    # Usamos un relleno Shape para mejor performance que Scatter con fill
    fig.add_shape(type="path",
        path=f"M 45,42 L 75,32 L 75,28 L 45,38 Z", # Ajuste visual de la diagonal
        fillcolor="rgba(46, 204, 113, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    # Anotaciones de Zonas (Contexto estático)
    fig.add_annotation(x=30, y=45, text="<b>ZONA I</b><br>Mezcla Pedregosa<br>(Gap Graded)", showarrow=False, font=dict(color="darkred", size=10))
    fig.add_annotation(x=60, y=35, text="<b>ZONA II</b><br>Bien Graduada", showarrow=False, font=dict(color="darkgreen", size=10))
    fig.add_annotation(x=65, y=20, text="<b>ZONA III</b><br>Mezcla Arenosa", showarrow=False, font=dict(color="darkorange", size=10))
    fig.add_annotation(x=90, y=45, text="<b>ZONA V</b><br>Muy Tosca", showarrow=False, font=dict(color="gray", size=10))

    # Líneas divisorias (Shapes)
    fig.add_shape(type="line", x0=45, y0=15, x1=45, y1=50, line=dict(color="black", width=1, dash="dot"))
    fig.add_shape(type="line", x0=75, y0=15, x1=75, y1=50, line=dict(color="black", width=1, dash="dot"))

    # --- Tu Mezcla (Punto) ---
    # Lógica de color semáforo simplificada para demo
    color_punto = COLOR_WARN
    # Lógica Aproximada: Si está en banda diagonal (y = -0.33x + b)
    # y_sup = -0.33 * cf + 57 (aprox)
    # y_inf = -0.33 * cf + 52 (aprox)
    y_sup = -0.333 * cf + 57
    y_inf = -0.333 * cf + 53
    
    if 45 <= cf <= 75 and y_inf <= wf <= y_sup:
        color_punto = COLOR_OK
    elif cf < 45 or cf > 75:
        color_punto = COLOR_WARN
    else:
        color_punto = COLOR_SECUNDARIO 

    fig.add_trace(go.Scatter(
        x=[cf], y=[wf],
        mode='markers+text',
        marker=dict(size=18, color=color_punto, line=dict(width=2, color='black'), symbol='star'),
        text=["<b>TU MEZCLA</b>"], textposition="top center",
        hovertemplate="<b>CF:</b> %{x:.1f}%<br><b>WF:</b> %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Diagrama de Factor de Tosquedad (Shilstone)", font=dict(size=18)),
        xaxis=dict(title="Factor de Tosquedad (CF) %", range=[20, 80], gridcolor=COLOR_GRID),
        yaxis=dict(title="Factor de Trabajabilidad (WF) %", range=[15, 50], gridcolor=COLOR_GRID),
        template="plotly_white",
        height=550,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    return fig

def crear_grafico_power45_interactivo(tamices_lbl: List[str], 
                                      tamices_mm: List[float], 
                                      pass_real: List[float], 
                                      pass_ideal: List[float]) -> go.Figure:
    """
    Gráfico Power 0.45 real.
    """
    # Calcular coordenadas X transformadas
    x_power = [d**0.45 for d in tamices_mm]
    
    fig = go.Figure()

    # Línea Ideal
    fig.add_trace(go.Scatter(
        x=x_power, y=pass_ideal,
        mode='lines',
        name='Referencia Power 0.45',
        line=dict(color='black', width=2, dash='dash'),
        hovertemplate="Ideal: %{y:.1f}%<extra></extra>"
    ))

    # Curva Real
    fig.add_trace(go.Scatter(
        x=x_power, y=pass_real,
        mode='lines+markers',
        name='Mezcla Diseñada',
        line=dict(color=COLOR_PRIMARIO, width=3),
        marker=dict(size=7),
        hovertemplate="<b>Mezcla</b><br>Pasa: %{y:.1f}%<extra></extra>"
    ))
    
    # Configuración Eje X
    fig.update_layout(
        title="Curva de Potencia 0.45 (Fuller)",
        xaxis=dict(
            title="Tamaño de Tamiz (Escala ^0.45)",
            tickvals=x_power,
            ticktext=tamices_lbl,
            gridcolor=COLOR_GRID
        ),
        yaxis=dict(title="% Pasante Acumulado", range=[0, 105], gridcolor=COLOR_GRID),
        template="plotly_white",
        height=500,
        hovermode="x unified"
    )
    return fig

def crear_grafico_tarantula_interactivo(tamices_lbl: List[str], 
                                        retenidos_ind: List[float],
                                        tmn: float = 0) -> go.Figure:
    """
    Gráfico de la Curva Tarántula con la 'Caja' de límites correcta.
    """
    fig = go.Figure()
    
    # Límite superior: 20% para la mayoría
    lim_sup = [20] * len(tamices_lbl)
    # Límite inferior: 4% para tamices significativos
    lim_inf = [4] * len(tamices_lbl)
    
    # Dibujar la "Caja" de aceptación
    fig.add_trace(go.Scatter(
        x=tamices_lbl + tamices_lbl[::-1],
        y=lim_sup + lim_inf[::-1],
        fill='toself',
        fillcolor='rgba(44, 160, 44, 0.15)', # Verde suave
        line=dict(color='rgba(44, 160, 44, 0.3)', dash='dot'),
        name='Rango Tarántula (4-20%)',
        hoverinfo='skip'
    ))

    # Línea de la Mezcla
    fig.add_trace(go.Scatter(
        x=tamices_lbl, y=retenidos_ind,
        mode='lines+markers',
        name='Retenido Individual',
        line=dict(color=COLOR_PRIMARIO, width=3),
        marker=dict(size=8, symbol='square'),
        hovertemplate="%{y:.1f}% Retenido<extra></extra>"
    ))

    fig.update_layout(
        title="Curva Tarántula (Retenido Individual)",
        xaxis=dict(title="Tamiz"),
        yaxis=dict(title="% Retenido Individual", range=[0, 30], gridcolor=COLOR_GRID),
        template="plotly_white",
        height=500
    )
    return fig

def crear_grafico_haystack_interactivo(tamices_nombres: List[str],
                                       retenidos_vals: List[float]) -> go.Figure:
    """
    Crea gráfico Haystack (% Retenido).
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tamices_nombres,
        y=retenidos_vals,
        mode='lines+markers',
        name='Tu Mezcla',
        line=dict(color=COLOR_SECUNDARIO, width=3),
        marker=dict(size=8, symbol='diamond')
    ))

    fig.update_layout(
        title=dict(text="Curva Haystack (% Retenido)", font=dict(size=20)),
        xaxis=dict(title="Tamiz"),
        yaxis=dict(title="% Retenido", range=[0, 30], gridcolor=COLOR_GRID),
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

def mostrar_resultados_optimizacion(resultado: Dict, granulometrias: List[List[float]], tmn: float):
    """
    Muestra los resultados de la optimización con gráficos interactivos CTO.
    """
    import streamlit as st
    from modules.power45 import generar_curva_ideal_power45
    
    st.markdown("### 🎯 Resultados de Optimización (Clase Mundial)")
    
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Error Power45", f"{resultado.get('error_power45', 0):.3f}")
    c2.metric("Penalización Shilstone", f"{resultado.get('error_shilstone', 0):.3f}")
    c3.metric("Objetivo Final", f"{resultado.get('objetivo', 0):.3f}")
    
    # Proporciones óptimas
    st.markdown("#### Proporciones Óptimas")
    props = resultado.get('proporciones', [])
    cols = st.columns(len(props) if props else 1)
    for i, prop in enumerate(props):
        cols[i % len(cols)].metric(f"Árido {i+1}", f"{prop:.2f}%")
    
    # Datos para gráficos
    mezcla_opt = resultado.get('mezcla_optimizada', [])
    curva_ideal, _ = generar_curva_ideal_power45(tmn)
    
    # Tamices y Mapeo MM
    tamices_lbl = ['1.5"', '1"', '3/4"', '1/2"', '3/8"', '#4', '#8', '#16', '#30', '#50', '#100', '#200']
    mapa_mm = _get_sieve_mm_map()
    tamices_mm = [mapa_mm.get(t, 0.1) for t in tamices_lbl]
    
    # Ajustar longitudes
    min_len = min(len(tamices_lbl), len(mezcla_opt))
    tam_lbl_viz = tamices_lbl[:min_len]
    tam_mm_viz = tamices_mm[:min_len]
    mezcla_viz = mezcla_opt[:min_len]
    ideal_viz = curva_ideal[:min_len]
    
    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📉 Power 45 (Real)", "🕷️ Tarántula", "🌾 Haystack", "🔷 Shilstone"])
    
    with tab1:
        fig_p45 = crear_grafico_power45_interactivo(tam_lbl_viz, tam_mm_viz, mezcla_viz, ideal_viz)
        st.plotly_chart(fig_p45, use_container_width=True)
        
    with tab2:
        if 'mezcla_retenido' in resultado:
            ret = resultado['mezcla_retenido'][:min_len]
            fig_tar = crear_grafico_tarantula_interactivo(tam_lbl_viz, ret, tmn)
            st.plotly_chart(fig_tar, use_container_width=True)
        else:
            st.info("Sin datos de retenido.")
            
    with tab3:
        if 'mezcla_retenido' in resultado:
            ret = resultado['mezcla_retenido'][:min_len]
            fig_hay = crear_grafico_haystack_interactivo(tam_lbl_viz, ret)
            st.plotly_chart(fig_hay, use_container_width=True)
    
    with tab4:
        if 'shilstone_factors' in resultado:
            sf = resultado['shilstone_factors']
            fig_shil = crear_grafico_shilstone_interactivo(sf['cf'], sf['wf'])
            st.plotly_chart(fig_shil, use_container_width=True)
            st.caption(f"CF: {sf['cf']}% | WF: {sf['wf']}%")
        else:
            st.warning("Faltan factores Shilstone.")

    # Evaluación de restricciones
    if 'evaluacion_restricciones' in resultado:
        with st.expander("📋 Ver Restricciones"):
            st.json(resultado['evaluacion_restricciones'])
def crear_grafico_shilstone_interactivo(cf: float, wf: float) -> go.Figure:
    """
    Crea el Diagrama de Shilstone Completo (Iowa Method).
    Zonas I, II, III definidas explícitamente.
    """
    fig = go.Figure()
    
    # --- Definición de Líneas de Frontera (Trend Bar) ---
    # Top Line (Separa Zona I de Zona II): (45, 41) -> (75, 31)
    # Bottom Line (Separa Zona II de Zona III): (45, 37) -> (75, 27) (Aprox, ajustado a banda de 4pts)
    # Iowa Spreadhseet suele usar una banda de ancho 4-6%.
    # Usaremos coordenadas estándar aproximadas para "Traffic Light".
    
    # ZONE II (WORKABLE) - BANDA CENTRAL
    x_band = [45, 75, 75, 45, 45]
    y_band = [41, 31, 27, 37, 41] # Vértices del paralelogramo Zona II
    
    # Relleno Zona II (Verde)
    fig.add_trace(go.Scatter(
        x=x_band, y=y_band,
        fill="toself",
        fillcolor="rgba(46, 204, 113, 0.3)", 
        line=dict(color="green", width=2),
        name="Zona II (Optimal)",
        hoverinfo="skip"
    ))
    
    # ZONE I (GAP GRADED) - ARRIBA
    # Polígono que cubre la zona superior
    x_zone1 = [20, 45, 75, 100, 100, 20, 20]
    y_zone1 = [60, 41, 31, 23, 60, 60, 60] # Por encima de la línea superior
    fig.add_trace(go.Scatter(
        x=x_zone1, y=y_zone1,
        fill="toself",
        fillcolor="rgba(231, 76, 60, 0.1)", # Rojo muy suave
        line=dict(width=0),
        name="Zona I (Gap-Graded)",
        hoverinfo="skip"
    ))
    
    # ZONE III (SANDY) - ABAJO
    x_zone3 = [20, 45, 75, 100, 100, 20, 20]
    y_zone3 = [0, 37, 27, 19, 0, 0, 0] # Por debajo de la línea inferior
    fig.add_trace(go.Scatter(
        x=x_zone3, y=y_zone3,
        fill="toself",
        fillcolor="rgba(241, 196, 15, 0.1)", # Amarillo suave
        line=dict(width=0),
        name="Zona III (Sandy)",
        hoverinfo="skip"
    ))
    
    # Líneas Negras Divisorias (Explicit Quadrants)
    # Límite Superior Zona II
    fig.add_trace(go.Scatter(x=[20, 85], y=[49.3, 27.6], mode='lines', line=dict(color='black', width=2, dash='dash'), showlegend=False)) # Proyección aprox
    # Mejor usar formas shapes para líneas exactas
    
    # Punto de la Mezcla
    in_zone_ii = 45 <= cf <= 75 and ( -0.333*cf + 52 <= wf <= -0.333*cf + 56) # Simple check visual logic
    
    color_punto = 'black'
    symbol_punto = 'star'
    size_punto = 20
    
    fig.add_trace(go.Scatter(
        x=[cf],
        y=[wf],
        mode='markers+text',
        name='Tu Mezcla',
        text=[" TU MEZCLA"],
        textposition="top right",
        marker=dict(size=size_punto, color=color_punto, symbol=symbol_punto, line=dict(width=2, color='white')),
        hovertemplate=f"<b>Tu Mezcla</b><br>CF: %{{x:.1f}}%<br>WF: %{{y:.1f}}%<extra></extra>"
    ))
    
    fig.update_layout(
        title="Diagrama de Shilstone (Zonas I, II, III)",
        xaxis=dict(title="Coarseness Factor (%)", range=[20, 80], dtick=5, showgrid=True, gridcolor='lightgray'),
        yaxis=dict(title="Workability Factor (%)", range=[15, 50], dtick=5, showgrid=True, gridcolor='lightgray'),
        template="plotly_white",
        height=600,
        shapes=[
            # Línea Superior Zona II (45,41) -> (75,31)
            dict(type="line", x0=45, y0=41, x1=75, y1=31, line=dict(color="black", width=3)),
            # Línea Inferior Zona II (45,37) -> (75,27)
            dict(type="line", x0=45, y0=37, x1=75, y1=27, line=dict(color="black", width=3)),
            # Línea Vertical CF=45
            dict(type="line", x0=45, y0=15, x1=45, y1=50, line=dict(color="gray", width=1, dash="dot")),
            # Línea Vertical CF=75
            dict(type="line", x0=75, y0=15, x1=75, y1=50, line=dict(color="gray", width=1, dash="dot"))
        ]
    )
    
    # Etiquetas de Zonas Grandes
    fig.add_annotation(x=35, y=45, text="<b>ZONA I</b><br>Segregación", font=dict(size=14, color="darkred"), showarrow=False)
    fig.add_annotation(x=60, y=34, text="<b>ZONA II</b><br>Óptima", font=dict(size=14, color="darkgreen"), showarrow=False)
    fig.add_annotation(x=65, y=22, text="<b>ZONA III</b><br>Muy Fina", font=dict(size=14, color="darkorange"), showarrow=False)
    
    return fig

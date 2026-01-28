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
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cemento", f"{resultados['cemento']['cantidad']:.1f} kg/m³")
    col2.metric("Agua", f"{resultados['agua_cemento']['agua_amasado']:.1f} L/m³")
    col3.metric("A/C", f"{resultados['agua_cemento']['razon']:.3f}")
    col4.metric("Aire", f"{resultados['aire']['volumen']:.1f} L/m³")
    
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

def crear_grafico_shilstone_interactivo(CF: float, Wadj: float, evaluacion: Dict) -> go.Figure:
    """
    Crea un gráfico interactivo de Shilstone usando Plotly.
    
    Args:
        CF: Coarseness Factor
        Wadj: Workability Factor Ajustado
        evaluacion: Diccionario con la evaluación de la zona
    
    Returns:
        Objeto go.Figure de Plotly
    """
    fig = go.Figure()

    # Definir Polígonos de Zonas (Coordenadas aproximadas basadas en Shilstone)
    
    # Zona 1 - Óptima (Verde)
    fig.add_trace(go.Scatter(
        x=[100, 85, 45, 45, 75, 100],
        y=[27, 27, 32, 45, 45, 36],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(44, 160, 44, 0)", width=0),
        fillcolor="rgba(44, 160, 44, 0.2)",
        name="Zona I - Óptima",
        hoverinfo="name"
    ))

    # Zona 2 - Rocky (Naranja/Beige)
    fig.add_trace(go.Scatter(
        x=[100, 75, 75, 100],
        y=[36, 45, 50, 50],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(255, 187, 120, 0.3)",
        name="Zona II - Rocky",
        hoverinfo="name"
    ))

    # Zona 3 - Sobrediseñada (Rosa)
    fig.add_trace(go.Scatter(
        x=[75, 45, 45, 75],
        y=[45, 45, 50, 50],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(255, 152, 150, 0.3)",
        name="Zona III - Sobrediseñada",
        hoverinfo="name"
    ))

    # Zona 4 - Arenosa (Azul claro)
    fig.add_trace(go.Scatter(
        x=[45, 0, 0, 45],
        y=[32, 37, 50, 50],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(174, 199, 232, 0.3)",
        name="Zona IV - Arenosa",
        hoverinfo="name"
    ))
    
    # Zona 5 - Baja Trabajabilidad (Gris/Violeta) - Fondo
    # Se dibuja implícitamente o como resto, pero podemos agregar un polígono grande abajo
    fig.add_trace(go.Scatter(
        x=[100, 85, 45, 0, 0, 100],
        y=[20, 27, 32, 37, 20, 20],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(197, 176, 213, 0.3)",
        name="Zona V - Baja Trabajabilidad",
        hoverinfo="name"
    ))

    # Líneas de contorno Zona I (para que resalte)
    fig.add_trace(go.Scatter(
        x=[100, 75, 45, 45, 85, 100],
        y=[36, 45, 45, 32, 27, 27],
        mode="lines",
        line=dict(color="green", width=2),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Punto de la Mezcla Actual
    color_punto = 'green' if evaluacion.get('calidad') == 'Óptima' else ('orange' if evaluacion.get('calidad') == 'Aceptable' else 'red')
    
    fig.add_trace(go.Scatter(
        x=[CF],
        y=[Wadj],
        mode='markers+text',
        marker=dict(size=14, color=color_punto, line=dict(width=2, color='black')),
        text=[f"<b>TU MEZCLA</b><br>CF: {CF}<br>Wadj: {Wadj}"],
        textposition="top center",
        name='Tu Mezcla',
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))

    # Configuración del Layout
    fig.update_layout(
        title=dict(text="Análisis de Trabajabilidad (Shilstone)", font=dict(size=20)),
        xaxis=dict(
            title="Coarseness Factor (CF)",
            range=[0, 100],
            gridcolor=COLOR_GRILLA,
            zeroline=False
        ),
        yaxis=dict(
            title="Workability Factor (W-adj)",
            range=[20, 50],
            gridcolor=COLOR_GRILLA,
            zeroline=False
        ),
        template="plotly_white",
        width=800,
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="closest"
    )
    
    # Anotaciones de Texto para las Zonas
    fig.add_annotation(x=60, y=38, text="ZONA I (ÓPTIMA)", showarrow=False, font=dict(color="green", size=12, weight="bold"))
    fig.add_annotation(x=90, y=42, text="Rocky", showarrow=False, font=dict(color="gray", size=10))
    fig.add_annotation(x=20, y=42, text="Arenosa", showarrow=False, font=dict(color="gray", size=10))
    
    return fig


def crear_grafico_power45_interactivo(tamices_nombres: List[str], 
                                      tamices_power: List[float], 
                                      ideal_vals: List[float], 
                                      real_vals: List[float],
                                      rmse: float) -> go.Figure:
    """
    Crea un gráfico interactivo Power 45.
    
    Args:
        tamices_nombres: Etiquetas de los tamices (ej: '1"', '#4')
        tamices_power: Valores X (tamiz^0.45)
        ideal_vals: Valores Y curva ideal
        real_vals: Valores Y curva real
        rmse: Error RMSE calculado
    
    Returns:
        Objeto go.Figure
    """
    fig = go.Figure()

    # Curva Ideal
    fig.add_trace(go.Scatter(
        x=tamices_power,
        y=ideal_vals,
        mode='lines+markers',
        name='Curva Ideal (Power 45)',
        line=dict(color=COLOR_PRIMARIO, width=3, dash='dash'),
        marker=dict(size=6, symbol='square'),
        hovertemplate='<b>Ideal</b><br>Tamiz: %{customdata}<br>% Pasa: %{y:.1f}%<extra></extra>',
        customdata=tamices_nombres
    ))

    # Curva Real
    fig.add_trace(go.Scatter(
        x=tamices_power,
        y=real_vals,
        mode='lines+markers',
        name='Tu Mezcla',
        line=dict(color=COLOR_SECUNDARIO, width=4),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='<b>Real</b><br>Tamiz: %{customdata}<br>% Pasa: %{y:.1f}%<extra></extra>',
        customdata=tamices_nombres
    ))
    
    # Relleno de diferencia
    fig.add_trace(go.Scatter(
        x=tamices_power + tamices_power[::-1],
        y=ideal_vals + real_vals[::-1],
        fill='toself',
        fillcolor='rgba(255, 127, 14, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='Desviación'
    ))

    # Layout
    fig.update_layout(
        title=dict(text=f"Curva de Gradación Power 45 (RMSE: {rmse:.2f})", font=dict(size=20)),
        xaxis=dict(
            title="Tamaño de Tamiz (Escala Power 0.45)",
            tickmode='array',
            tickvals=tamices_power,
            ticktext=tamices_nombres,
            gridcolor=COLOR_GRILLA
        ),
        yaxis=dict(
            title="% Que Pasa",
            range=[0, 105],
            gridcolor=COLOR_GRILLA
        ),
        template="plotly_white",
        width=900,
        height=550,
        legend=dict(x=0.02, y=0.98),
        hovermode="x unified"
    )

    return fig

def crear_grafico_tarantula_interactivo(tamices_nombres: List[str],
                                        retenidos_vals: List[float],
                                        tmn: float) -> go.Figure:
    """
    Crea gráfico de Curva Tarántula (% Retenido Individual).
    """
    fig = go.Figure()
    
    # Límites aproximados Tarantula (simplificado para ejemplo, idealmente parametrizar según tmn)
    # Límite superior genérico (ejemplo: 20% para gruesos, 15% finos)
    limite_sup = [22] * len(tamices_nombres)
    limite_inf = [4] * len(tamices_nombres)
    
    # Área Aceptable (Fondo)
    fig.add_trace(go.Scatter(
        x=tamices_nombres + tamices_nombres[::-1],
        y=limite_sup + limite_inf[::-1],
        fill='toself',
        fillcolor='rgba(200, 200, 200, 0.2)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Rango Aceptable',
        hoverinfo="skip"
    ))
    
    fig.add_trace(go.Scatter(
        x=tamices_nombres,
        y=retenidos_vals,
        mode='lines+markers',
        name='Tu Mezcla (% Retenido)',
        line=dict(color=COLOR_PRIMARIO, width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=dict(text="Curva Tarántula (% Retenido Individual)", font=dict(size=20)),
        xaxis=dict(title="Tamiz"),
        yaxis=dict(title="% Retenido Individual", range=[0, 30]),
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

def crear_grafico_haystack_interactivo(tamices_nombres: List[str],
                                       retenidos_vals: List[float]) -> go.Figure:
    """
    Crea gráfico Haystack (% Retenido).
    Similar a Tarantula pero con enfoque en banda de trabajo.
    """
    fig = go.Figure()
    
    # Límites Haystack (Ejemplo visual: picos en el centro)
    # Esto es ilustrativo, los límites reales dependen de la norma
    
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
        yaxis=dict(title="% Retenido", range=[0, 30]),
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

def crear_grafico_gradaciones_individuales(tamices_nombres: List[str],
                                           aridos: List[Dict],
                                           proporciones: List[float],
                                           mezcla_final: List[float]) -> go.Figure:
    """
    Crea gráfico con todas las curvas individuales y la combinada.
    """
    fig = go.Figure()
    
    # Curvas individuales
    for i, arido in enumerate(aridos):
        if i < len(proporciones):
            nombre = f"{arido['nombre']} ({proporciones[i]:.1f}%)"
            fig.add_trace(go.Scatter(
                x=tamices_nombres,
                y=arido['granulometria'],
                mode='lines',
                name=nombre,
                line=dict(width=2, dash='dot'),
                opacity=0.7
            ))
            
    # Curva Combinada
    fig.add_trace(go.Scatter(
        x=tamices_nombres,
        y=mezcla_final,
        mode='lines+markers',
        name='Mezcla Combinada',
        line=dict(color='black', width=4),
        marker=dict(size=6, color='black')
    ))

    fig.update_layout(
        title=dict(text="Gradaciones Individuales y Combinada", font=dict(size=20)),
        xaxis=dict(title="Tamiz", type='category'), # Category para mantener orden
        yaxis=dict(title="% Que Pasa", range=[0, 105]),
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

def mostrar_resultados_optimizacion(resultado: Dict, granulometrias: List[List[float]], tmn: float):
    """
    Muestra los resultados de la optimización con gráficos interactivos.
    
    Args:
        resultado: Diccionario con resultados de optimización
        granulometrias: Lista de granulometrías de áridos
        tmn: Tamaño máximo nominal
    """
    import streamlit as st
    from modules.power45 import generar_curva_ideal_power45
    
    st.markdown("### 🎯 Resultados de Optimización")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Error Power45", f"{resultado.get('error_power45', 0):.3f}")
    col2.metric("Penalización Total", f"{resultado.get('penalizacion_total', 0):.3f}")
    col3.metric("Objetivo Final", f"{resultado.get('objetivo', 0):.3f}")
    
    # Proporciones óptimas
    st.markdown("#### Proporciones Óptimas")
    props = resultado.get('proporciones', [])
    for i, prop in enumerate(props):
        st.write(f"**Árido {i+1}:** {prop:.2f}%")
    
    # Gráfico de comparación con Power45
    curva_ideal, tamices_mm = generar_curva_ideal_power45(tmn)
    mezcla_opt = resultado.get('mezcla_optimizada', [])
    
    # Tamices estándar (12 elementos)
    tamices_nombres = ['1.5"', '1"', '3/4"', '1/2"', '3/8"', '#4', '#8', '#16', '#30', '#50', '#100', '#200']
    
    # Ajustar longitudes para que coincidan
    min_len = min(len(tamices_nombres), len(curva_ideal), len(mezcla_opt)) if mezcla_opt else min(len(tamices_nombres), len(curva_ideal))
    
    fig = go.Figure()
    
    # Curva ideal Power45
    fig.add_trace(go.Scatter(
        x=tamices_nombres[:min_len],
        y=curva_ideal[:min_len],
        mode='lines',
        name='Curva Ideal (Power 45)',
        line=dict(color=COLOR_BUENO, width=3, dash='dash')
    ))
    
    # Mezcla optimizada
    if mezcla_opt:
        fig.add_trace(go.Scatter(
            x=tamices_nombres[:min_len],
            y=mezcla_opt[:min_len],
            mode='lines+markers',
            name='Mezcla Optimizada',
            line=dict(color=COLOR_PRIMARIO, width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Comparación con Curva Ideal Power 45",
        xaxis=dict(title="Tamiz", type='category'),
        yaxis=dict(title="% Que Pasa", range=[0, 105]),
        template="plotly_white",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Evaluación de restricciones
    if 'evaluacion_restricciones' in resultado:
        with st.expander("📋 Evaluación de Restricciones"):
            eval_rest = resultado['evaluacion_restricciones']
            st.json(eval_rest)

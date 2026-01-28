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

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

    # --- ESTILO TÉCNICO IDÉNTICO AL EXCEL (Coordenadas Exactas) ---
    
    # Line 1 (Límite Superior)
    # Excel: (100, 36) -> (35, 45)
    fig.add_trace(go.Scatter(
        x=[100, 35], y=[36, 45],
        mode="lines", line=dict(color="black", width=3), showlegend=False, hoverinfo="skip"
    ))
    
    # Line 2 (Límite Inferior)
    # Excel: (100, 27) -> (85, 27) -> (15, 37) -> (0, 37)
    fig.add_trace(go.Scatter(
        x=[100, 85, 15, 0], y=[27, 27, 37, 37],
        mode="lines", line=dict(color="black", width=3), showlegend=False, hoverinfo="skip"
    ))
    
    # Line 3 (División Vertical Derecha - Zona V vs III)
    # Excel: (75, 28.43) -> (75, 39.46)
    # Nota: Conecta Límite Inferior con Límite Superior
    fig.add_trace(go.Scatter(
        x=[75, 75], y=[28.43, 39.46],
        mode="lines", line=dict(color="black", width=2), showlegend=False, hoverinfo="skip"
    ))
    
    # Line 4 (División Vertical Izquierda - Zona I vs II)
    # Excel: (45, 32.71) -> (45, 43.62)
    fig.add_trace(go.Scatter(
        x=[45, 45], y=[32.71, 43.62],
        mode="lines", line=dict(color="black", width=2), showlegend=False, hoverinfo="skip"
    ))

    # Punto de la Mezcla Actual
    fig.add_trace(go.Scatter(
        x=[CF], y=[Wadj],
        mode='markers',
        marker=dict(size=14, color='red', line=dict(width=1, color='black')),
        name='Tu Mezcla',
        text=[f"CF: {CF:.1f}, Wadj: {Wadj:.1f}"],
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))

    # Configuración del Layout TÉCNICO
    fig.update_layout(
        title=dict(text="Shilstone Chart", font=dict(size=24, color="black", family="Times New Roman")),
        xaxis=dict(
            title="Coarseness Factor",
            range=[100, 0], # INVERTIDO
            dtick=20,
            gridcolor='black', gridwidth=1,
            zeroline=False, showline=True, linecolor='black', linewidth=2, mirror=True
        ),
        yaxis=dict(
            title="Workability Factor",
            range=[20, 45],
            dtick=5,
            gridcolor='black', gridwidth=1,
            zeroline=False, showline=True, linecolor='black', linewidth=2, mirror=True
        ),
        template="plotly_white",
        width=700, height=500,
        showlegend=False
    )
    
    # Textos Grandes de Zonas (Posiciones ajustadas visualmente al Excel)
    fig.add_annotation(x=87.5, y=30, text="I<br>Gap", showarrow=False, font=dict(size=16, color="black", family="Arial Black"))
    fig.add_annotation(x=60, y=41, text="II", showarrow=False, font=dict(size=16, color="black", family="Arial Black"))
    fig.add_annotation(x=10, y=41, text="III<br>Small Agg", showarrow=False, font=dict(size=14, color="black", family="Arial Black"))
    fig.add_annotation(x=87.5, y=42, text="IV<br>Sandy", showarrow=False, font=dict(size=14, color="black", family="Arial Black"))
    fig.add_annotation(x=30, y=24, text="V<br>Coarse", showarrow=False, font=dict(size=16, color="black", family="Arial Black"))
    
    return fig


def crear_grafico_power45_interactivo(tamices_nombres: List[str], 
                                      tamices_power: List[float], 
                                      ideal_vals: List[float], 
                                      real_vals: List[float],
                                      rmse: float) -> go.Figure:
    fig = go.Figure()

    # Curva Ideal (Verde en Excel)
    fig.add_trace(go.Scatter(
        x=tamices_power, y=ideal_vals,
        mode='lines', name='Max Density',
        line=dict(color='green', width=3),
        hovertemplate='Ideal: %{y:.1f}%<extra></extra>'
    ))

    # Límites +- (Rojos en Excel) - Aproximación visual
    # Suelen ser +-5% aprox
    fig.add_trace(go.Scatter(
        x=tamices_power, y=[min(100, v+5) for v in ideal_vals],
        mode='lines', line=dict(color='red', width=1, dash='solid'),
        name='Limits', hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=tamices_power, y=[max(0, v-5) for v in ideal_vals],
        mode='lines', line=dict(color='red', width=1, dash='solid'),
        showlegend=False, hoverinfo='skip'
    ))

    # Curva Real (Azul con X)
    fig.add_trace(go.Scatter(
        x=tamices_power, y=real_vals,
        mode='lines+markers', name='Mixture',
        line=dict(color='blue', width=3),
        marker=dict(symbol='x', size=8, color='blue'),
        hovertemplate='Real: %{y:.1f}%<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text="Power 45", font=dict(size=20, family="Times New Roman")),
        xaxis=dict(
            title="Sieve (^0.45)",
            tickmode='array', tickvals=tamices_power, ticktext=tamices_nombres,
            showgrid=True, gridcolor='black', linecolor='black', mirror=True
        ),
        yaxis=dict(
            title="% Passing",
            range=[0, 100],
            showgrid=True, gridcolor='black', linecolor='black', mirror=True
        ),
        template="plotly_white",
        width=800, height=500,
        legend=dict(
            x=0.7, y=0.1,
            bordercolor="black", borderwidth=1, bgcolor="white"
        )
    )

    return fig

def crear_grafico_tarantula_interactivo(tamices_nombres: List[str],
                                        retenidos_vals: List[float],
                                        tmn: float = 25.0) -> go.Figure:
    """
    Tarantula Style: % Retained Individual (Updated to match Excel screenshot)
    """
    fig = go.Figure()

    # Límites exactos Excel (Líneas Azules Punteadas)
    # 2" a 1": 0-0
    # 3/4": 0-20
    # 1/2" a #4: 4-20
    # #8 a #16: 0-12
    # #30 a #50: 4-20
    # #100: 0-10
    # #200: 0-0
    
    # Crear vectores de límites "escalonados" visualmente
    # Pero para simplificar en plotly usaremos lineas directas
    # Mapeo manual aproximado a la visual del Excel
    
    lim_sup = [0, 0, 0, 20, 20, 20, 20, 12, 12, 20, 20, 10, 0] # Extendiendo a 13 valores
    lim_inf = [0, 0, 0, 0, 4, 4, 4, 0, 0, 4, 4, 0, 0]
    
    # Ajustar longitud a tamices input
    n = len(tamices_nombres)
    lim_sup = lim_sup[:n]
    lim_inf = lim_inf[:n]
    
    fig.add_trace(go.Scatter(
        x=tamices_nombres, y=lim_sup,
        mode='lines', name='Limits',
        line=dict(color='blue', width=1, dash='dash'),
        hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=tamices_nombres, y=lim_inf,
        mode='lines',
        line=dict(color='blue', width=1, dash='dash'),
        showlegend=False, hoverinfo='skip'
    ))

    # Curva Real (Roja con Diamantes)
    fig.add_trace(go.Scatter(
        x=tamices_nombres, y=retenidos_vals,
        mode='lines+markers', name='Percent Retained, % vol',
        line=dict(color='red', width=3),
        marker=dict(symbol='diamond', size=8, color='red')
    ))

    fig.update_layout(
        title=dict(text="Tarantula", font=dict(size=20, family="Times New Roman")),
        xaxis=dict(
            title="Sieve",
            showgrid=True, gridcolor='black', linecolor='black', mirror=True,
            tickangle=-90
        ),
        yaxis=dict(
            title="Percent Retained, % vol",
            range=[0, 25],
            showgrid=True, gridcolor='black', linecolor='black', mirror=True
        ),
        template="plotly_white",
        width=800, height=400,
        legend=dict(
            x=0.6, y=0.9,
            bordercolor="black", borderwidth=1, bgcolor="white"
        )
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

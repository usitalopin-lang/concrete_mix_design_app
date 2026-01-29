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

    # Definir Polígonos de Zonas (Calibrados según Excel de Referencia)
    
    # Zona 1 - Óptima ("Banana Shape")
    # Límite Inferior: (100, 27) -> (85, 27) -> (15, 37) -> (0, 37)
    # Límite Superior: (0, 45) -> (35, 45) -> (100, 36)
    x_zona1 = [100, 85, 15, 0, 0, 35, 100, 100]
    y_zona1 = [27, 27, 37, 37, 45, 45, 36, 27]
    
    fig.add_trace(go.Scatter(
        x=x_zona1,
        y=y_zona1,
        fill="toself",
        mode="lines",
        line=dict(color="rgba(44, 160, 44, 0)", width=0),
        fillcolor="rgba(44, 160, 44, 0.2)",
        name="Zona I - Óptima (Excel)",
        hoverinfo="name"
    ))

    # Zona 2 - Arenosa (Bajo la zona óptima, CF < 45)
    fig.add_trace(go.Scatter(
        x=[45, 0, 0, 45],
        y=[20, 20, 37, 32], # Ajustado para conectar con la zona 1
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(255, 187, 120, 0.3)",
        name="Zona II - Arenosa",
        hoverinfo="name"
    ))

    # Zona 3 - Pedregosa (Sobre la zona óptima, CF > 75) - Ajuste conceptual
    fig.add_trace(go.Scatter(
        x=[75, 100, 100, 75],
        y=[45, 36, 20, 20],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(255, 152, 150, 0.3)",
        name="Zona III - Pedregosa",
        hoverinfo="name"
    ))

    # Zona IV - Indeseable (Wadj > 45)
    fig.add_trace(go.Scatter(
        x=[0, 100, 100, 0],
        y=[45, 45, 50, 50],
        fill="toself",
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="rgba(214, 39, 40, 0.1)",
        name="Zona IV - Exceso Finos",
        hoverinfo="name"
    ))
    
    # Líneas de contorno Zona I (para que resalte)
    fig.add_trace(go.Scatter(
        x=x_zona1,
        y=y_zona1,
        mode="lines",
        line=dict(color="green", width=2, dash='solid'),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Punto de la Mezcla Actual
    color_punto = 'black'
    # Validar si está dentro aproximadamente
    dentro_cf = (15 <= CF <= 100)
    dentro_w = (27 <= Wadj <= 45)
    if dentro_cf and dentro_w:
        color_punto = 'green'
    else:
        color_punto = 'red'
    
    fig.add_trace(go.Scatter(
        x=[CF],
        y=[Wadj],
        mode='markers+text',
        marker=dict(size=14, color=color_punto, line=dict(width=2, color='white')),
        text=[f"<b>TU MEZCLA</b><br>CF: {CF:.1f}<br>Wadj: {Wadj:.1f}"],
        textposition="top center",
        name='Tu Mezcla',
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))

    # Configuración del Layout
    fig.update_layout(
        title=dict(text="Análisis de Trabajabilidad (Shilstone - Calibrado)", font=dict(size=20)),
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
        hovermode="closest",
        shapes=[
            # Línea divisoria CF=45
            dict(type="line", x0=45, y0=20, x1=45, y1=50, line=dict(color="gray", dash="dot", width=1)),
            # Línea divisoria CF=75
            dict(type="line", x0=75, y0=20, x1=75, y1=50, line=dict(color="gray", dash="dot", width=1))
        ]
    )
    
    # Anotaciones
    fig.add_annotation(x=55, y=32, text="<b>ZONA I</b><br>(Óptima)", showarrow=False, font=dict(color="green", size=13))
    fig.add_annotation(x=25, y=25, text="Arenosa", showarrow=False, font=dict(color="gray", size=11))
    fig.add_annotation(x=90, y=25, text="Pedregosa", showarrow=False, font=dict(color="gray", size=11))
    
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
        title=dict(text=f"Curva de Gradación Power 45 (Desviación: {rmse:.2f})", font=dict(size=20)),
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
                                        tmn: float = 25.0) -> go.Figure:
    """
    Crea gráfico de Curva Tarántula / Haystack calibrado con límites del Excel.
    Muestra el % Pasante Acumulado vs Límites de la Banda.
    
    Nota: Recibe 'retenidos_vals' (individuales) pero DEBE convertir a Pasante para usar
    los límites del Excel (95-100, 75-90, etc). OJO: El Excel usa Pasante para Haystack Limits.
    """
    fig = go.Figure()
    
    # CONVERTIR RETENIDO INDIVIDUAL A PASANTE ACUMULADO
    # Asumimos que retenidos_vals suma 100 (o aprox)
    # Pasante[i] = 100 - (Acumulado Retenido hasta i)
    # Pero retenidos_vals suele venir ordenado de mayor a menor tamiz?
    # Vamos a recalcular pasante desde 0 (si es retenido individual)
    # Pasante N = 100 - sum(ret[0]...ret[N])
    
    acumulados = []
    curr = 0
    for val in retenidos_vals:
        curr += val
        acumulados.append(curr)
        
    pasante_vals = [max(0, 100 - x) for x in acumulados]
    
    # LÍMITES CALIBRADOS DEL EXCEL (Haystack Limits)
    # Mapeo por nombre de tamiz (aprox)
    limites_excel = {
        '2"': (100, 100), '50mm': (100, 100),
        '1 1/2"': (100, 100), '37.5mm': (100, 100),
        '1"': (100, 100), '25mm': (100, 100),
        '3/4"': (95, 100), '19mm': (95, 100),
        '1/2"': (75, 90), '12.5mm': (75, 90),
        '3/8"': (55, 75), '9.5mm': (55, 75),
        '#4': (38, 50), '4.75mm': (38, 50),
        '#8': (30, 42), '2.36mm': (30, 42),
        '#16': (22, 34), '1.18mm': (22, 34),
        '#30': (16, 30), '0.6mm': (16, 30),
        '#50': (5, 15), '0.3mm': (5, 15),
        '#100': (0, 7), '0.15mm': (0, 7),
        '#200': (0, 4), '0.075mm': (0, 4)
    }
    
    # Construir vectores de límites alineados con tamices_nombres
    lim_sup = []
    lim_inf = []
    labels_clean = []
    
    for t in tamices_nombres:
        # Limpieza simple de etiqueta para matchear
        key = t.replace('Nº', '#').strip()
        if key in limites_excel:
            inf, sup = limites_excel[key]
            lim_inf.append(inf)
            lim_sup.append(sup)
        else:
            # Default amplio si no matchea
            lim_inf.append(0)
            lim_sup.append(100)
    
    # Área Aceptable (Túnel Tarántula)
    fig.add_trace(go.Scatter(
        x=tamices_nombres + tamices_nombres[::-1],
        y=lim_sup + lim_inf[::-1],
        fill='toself',
        fillcolor='rgba(200, 200, 200, 0.4)',
        line=dict(color='rgba(100,100,100,0.2)'),
        name='Banda Tarántula (Excel)',
        hoverinfo="skip"
    ))
    
    fig.add_trace(go.Scatter(
        x=tamices_nombres,
        y=pasante_vals,
        mode='lines+markers',
        name='Tu Mezcla (% Pasante)',
        line=dict(color=COLOR_PRIMARIO, width=3),
        marker=dict(size=8, symbol='diamond')
    ))

    fig.update_layout(
        title=dict(text="Curva Tarántula (% Pasante Acumulado)", font=dict(size=20)),
        xaxis=dict(title="Tamiz"),
        yaxis=dict(title="% Que Pasa", range=[0, 105]),
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

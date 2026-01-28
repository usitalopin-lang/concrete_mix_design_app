import plotly.graph_objects as go
from config.config import TAMICES_ASTM

def crear_grafico_shilstone_interactivo(cf: float, wf: float) -> go.Figure:
    fig = go.Figure()
    # Trend Bar (Zona II)
    fig.add_shape(type="path", path="M 45,42 L 75,32 L 75,28 L 45,38 Z",
                  fillcolor="rgba(46, 204, 113, 0.2)", line=dict(width=0))
    fig.add_trace(go.Scatter(x=[cf], y=[wf], mode='markers+text', 
                  marker=dict(size=15, color='black', symbol='star'),
                  text=["TU MEZCLA"], textposition="top center"))
    fig.update_layout(title="Diagrama Shilstone",
                      xaxis=dict(title="Factor de Tosquedad (CF)", range=[20, 80]),
                      yaxis=dict(title="Factor de Trabajabilidad (WF)", range=[15, 50]),
                      height=500, template="plotly_white")
    return fig

def crear_grafico_power45_interactivo(tamices_lbl: list, tamices_mm: list, real: list, ideal: list) -> go.Figure:
    x_pow = [t**0.45 for t in tamices_mm]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_pow, y=ideal, name="Ideal Power 45", line=dict(dash='dash', color='gray')))
    fig.add_trace(go.Scatter(x=x_pow, y=real, name="Tu Mezcla", line=dict(color='blue', width=3)))
    fig.update_layout(title="Curva Power 0.45 (Fuller)",
                      xaxis=dict(title="Tamiz ^ 0.45", tickvals=x_pow, ticktext=tamices_lbl),
                      yaxis=dict(title="% Pasante", range=[0, 100]),
                      height=500, template="plotly_white")
    return fig

# Placeholders para evitar errores de importación
# --- Gráficos Avanzados (Restaurados) ---

def crear_grafico_tarantula_interactivo(tamices_lbl: list, retenidos: list) -> go.Figure:
    """Implementa la Carta Tarántula (Retenidos Individuales)."""
    fig = go.Figure()
    # Límites Tarántula (Simplificados Iowa: 8-18% para tamices significativos)
    fig.add_hrect(y0=8, y1=18, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Ideal (8-18%)")
    
    fig.add_trace(go.Bar(x=tamices_lbl, y=retenidos, name="% Retenido", marker_color='blue'))
    fig.update_layout(title="Carta Tarántula (% Retenido Individual)",
                      xaxis_title="Tamiz", yaxis_title="% Retenido",
                      yaxis=dict(range=[0, 30]), height=500, template="plotly_white")
    return fig

def crear_grafico_haystack_interactivo(tamices_lbl: list, retenidos: list) -> go.Figure:
    """Gráfico 'Haystack' (Pajar) para ver distribución de tamaños."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tamices_lbl, y=retenidos, fill='tozeroy', mode='none', name="Distribución"))
    fig.update_layout(title="Distribución Haystack (Pajar)",
                      xaxis_title="Tamiz", yaxis_title="% Retenido",
                      height=400, template="plotly_white")
    return fig

def mostrar_resultados_optimizacion(res_opt, tamices_lbl, tamices_mm):
    pass # Managed in UI directly now

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
def mostrar_resultados_faury(res): pass
def mostrar_resultados_optimizacion(res, a, b): pass
def crear_grafico_tarantula_interactivo(*args): return go.Figure()
def crear_grafico_haystack_interactivo(*args): return go.Figure()
def crear_grafico_gradaciones_individuales(*args): return go.Figure()

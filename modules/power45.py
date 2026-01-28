"""
Módulo Power 45 para análisis granulométrico de agregados
Implementa el cálculo de la curva ideal Power 45 y métricas de error.
"""

import numpy as np
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import io


# Tamices estándar para Power 45 (en mm)
TAMICES_POWER45 = [50, 37.5, 25, 19, 12.5, 9.5, 4.75, 2.36, 1.18, 0.6, 0.3, 0.15, 0.075]
TAMICES_NOMBRES = ['2"', '1½"', '1"', '¾"', '½"', '⅜"', '#4', '#8', '#16', '#30', '#50', '#100', '#200']


def calcular_valor_power45(tamiz_mm: float) -> float:
    """
    Calcula el valor Power 45 para un tamaño de tamiz.
    
    Fórmula: valor = tamiz^0.45
    
    Args:
        tamiz_mm: Tamaño del tamiz en mm
    
    Returns:
        Valor elevado a la potencia 0.45
    """
    if tamiz_mm <= 0:
        return 0.0
    return tamiz_mm ** 0.45


def generar_curva_ideal_power45(tmn: float, tamices: List[float] = None) -> Tuple[List[float], List[float]]:
    """
    Genera la curva ideal de gradación Power 45 para un TMN dado.
    
    La curva ideal va de 0% (tamiz más fino) a 100% (TMN).
    
    Args:
        tmn: Tamaño máximo nominal en mm
        tamices: Lista de tamices en mm (opcional, usa estándar si no se proporciona)
    
    Returns:
        Tupla (tamices, porcentajes_ideales)
    """
    if tamices is None:
        tamices = TAMICES_POWER45.copy()
    
    # Calcular valores ^0.45
    valores_45 = [calcular_valor_power45(t) for t in tamices]
    max_valor = calcular_valor_power45(tmn)
    min_valor = calcular_valor_power45(tamices[-1]) if tamices else calcular_valor_power45(0.075)
    
    # Normalizar a escala 0-100
    ideales = []
    for i, t in enumerate(tamices):
        if t >= tmn:
            ideales.append(100.0)
        else:
            v = valores_45[i]
            if max_valor - min_valor > 0:
                pct = ((v - min_valor) / (max_valor - min_valor)) * 100
                ideales.append(max(0, min(100, pct)))
            else:
                ideales.append(50.0)
    
    return tamices, ideales


def calcular_error_power45(mezcla_pct: List[float], ideal_pct: List[float], 
                           metodo: str = 'cuadratico') -> float:
    """
    Calcula el error entre la curva de mezcla real y la curva ideal Power 45.
    
    Args:
        mezcla_pct: Lista con % que pasa de la mezcla real
        ideal_pct: Lista con % que pasa de la curva ideal
        metodo: 'cuadratico' para suma de cuadrados, 'absoluto' para suma de valores absolutos
    
    Returns:
        Error total
    """
    if len(mezcla_pct) != len(ideal_pct):
        # Ajustar longitudes si difieren
        min_len = min(len(mezcla_pct), len(ideal_pct))
        mezcla_pct = mezcla_pct[:min_len]
        ideal_pct = ideal_pct[:min_len]
    
    if metodo == 'cuadratico':
        error = sum((m - i) ** 2 for m, i in zip(mezcla_pct, ideal_pct))
    else:  # absoluto
        error = sum(abs(m - i) for m, i in zip(mezcla_pct, ideal_pct))
    
    return round(error, 4)


def calcular_error_power45_normalizado(mezcla_pct: List[float], ideal_pct: List[float]) -> float:
    """
    Calcula el error normalizado (RMSE) entre la curva real y la ideal.
    
    Args:
        mezcla_pct: Lista con % que pasa de la mezcla real
        ideal_pct: Lista con % que pasa de la curva ideal
    
    Returns:
        RMSE (Root Mean Square Error)
    """
    if len(mezcla_pct) != len(ideal_pct):
        min_len = min(len(mezcla_pct), len(ideal_pct))
        mezcla_pct = mezcla_pct[:min_len]
        ideal_pct = ideal_pct[:min_len]
    
    n = len(mezcla_pct)
    if n == 0:
        return 0.0
    
    mse = sum((m - i) ** 2 for m, i in zip(mezcla_pct, ideal_pct)) / n
    rmse = np.sqrt(mse)
    
    return round(rmse, 4)


def calcular_retenido(pasa: List[float]) -> List[float]:
    """
    Calcula el porcentaje retenido en cada tamiz a partir del % que pasa.
    
    Args:
        pasa: Lista con % que pasa por cada tamiz
    
    Returns:
        Lista con % retenido en cada tamiz
    """
    retenido = []
    for i in range(len(pasa)):
        if i == 0:
            ret = 100 - pasa[i]
        else:
            ret = pasa[i-1] - pasa[i]
        retenido.append(max(0, ret))
    return retenido


def calcular_mezcla_granulometrica(proporciones: List[float], 
                                    granulometrias: List[List[float]]) -> List[float]:
    """
    Calcula la granulometría de una mezcla de agregados.
    
    Args:
        proporciones: Lista con proporciones de cada agregado (suman 100)
        granulometrias: Lista de granulometrías (% que pasa) de cada agregado
    
    Returns:
        Granulometría de la mezcla (% que pasa)
    """
    if not proporciones or not granulometrias:
        return []
    
    # Normalizar proporciones a fracciones
    total_prop = sum(proporciones)
    if total_prop > 0:
        fracciones = [p / total_prop for p in proporciones]
    else:
        fracciones = [1.0 / len(proporciones)] * len(proporciones)
    
    # Determinar número de tamices
    num_tamices = len(granulometrias[0]) if granulometrias else 0
    
    mezcla = [0.0] * num_tamices
    for i in range(num_tamices):
        for j, frac in enumerate(fracciones):
            if j < len(granulometrias) and i < len(granulometrias[j]):
                mezcla[i] += frac * granulometrias[j][i]
    
    return [round(v, 2) for v in mezcla]


def graficar_power45(mezcla_pct: List[float], tmn: float, 
                     titulo: str = "Análisis Power 45",
                     tamices: List[float] = None) -> plt.Figure:
    """
    Genera gráfico comparativo de curva real vs curva ideal Power 45.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
        tmn: Tamaño máximo nominal en mm
        titulo: Título del gráfico
        tamices: Lista de tamices en mm
    
    Returns:
        Figura de matplotlib
    """
    if tamices is None:
        tamices = TAMICES_POWER45.copy()
    
    # Generar curva ideal
    _, ideal = generar_curva_ideal_power45(tmn, tamices)
    
    # Ajustar longitud de mezcla si es necesario
    if len(mezcla_pct) < len(tamices):
        mezcla_pct = mezcla_pct + [0] * (len(tamices) - len(mezcla_pct))
    elif len(mezcla_pct) > len(tamices):
        mezcla_pct = mezcla_pct[:len(tamices)]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Eje X en escala Power 45
    x_valores = [t ** 0.45 for t in tamices]
    
    # Curva ideal
    ax.plot(x_valores, ideal, 'b-', linewidth=2, label='Curva Ideal Power 45', marker='s', markersize=6)
    
    # Curva de mezcla
    ax.plot(x_valores, mezcla_pct, 'r-', linewidth=2, label='Mezcla Real', marker='o', markersize=8)
    
    # Área de diferencia
    ax.fill_between(x_valores, mezcla_pct, ideal, alpha=0.3, color='yellow', label='Diferencia')
    
    # Configuración
    ax.set_xlabel('Tamaño de Tamiz (mm^0.45)', fontsize=12, fontweight='bold')
    ax.set_ylabel('% Que Pasa', fontsize=12, fontweight='bold')
    ax.set_title(titulo, fontsize=14, fontweight='bold')
    
    # Etiquetas de tamices
    ax.set_xticks(x_valores)
    ax.set_xticklabels(TAMICES_NOMBRES[:len(tamices)], rotation=45, ha='right')
    
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)
    
    # Mostrar error
    error = calcular_error_power45_normalizado(mezcla_pct, ideal)
    ax.text(0.98, 0.02, f'RMSE: {error:.2f}', transform=ax.transAxes,
            fontsize=11, fontweight='bold', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig


def graficar_power45_para_pdf(mezcla_pct: List[float], tmn: float) -> bytes:
    """
    Genera el gráfico Power 45 y lo retorna como bytes para incluir en PDF.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
        tmn: Tamaño máximo nominal en mm
    
    Returns:
        Imagen en formato PNG como bytes
    """
    fig = graficar_power45(mezcla_pct, tmn)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf.getvalue()


def evaluar_gradacion(mezcla_pct: List[float], tmn: float) -> Dict:
    """
    Evalúa la calidad de la gradación de la mezcla.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
        tmn: Tamaño máximo nominal en mm
    
    Returns:
        Diccionario con evaluación de la gradación
    """
    _, ideal = generar_curva_ideal_power45(tmn)
    
    # Ajustar longitudes
    min_len = min(len(mezcla_pct), len(ideal))
    mezcla_pct = mezcla_pct[:min_len]
    ideal = ideal[:min_len]
    
    error_cuad = calcular_error_power45(mezcla_pct, ideal, 'cuadratico')
    rmse = calcular_error_power45_normalizado(mezcla_pct, ideal)
    
    # Evaluar calidad
    if rmse < 5:
        calidad = 'Excelente'
        descripcion = 'Gradación muy cercana a la curva ideal Power 45.'
    elif rmse < 10:
        calidad = 'Buena'
        descripcion = 'Gradación aceptable con pequeñas desviaciones.'
    elif rmse < 15:
        calidad = 'Regular'
        descripcion = 'Gradación con desviaciones moderadas. Considerar ajustes.'
    else:
        calidad = 'Deficiente'
        descripcion = 'Gradación alejada de la curva ideal. Se requieren ajustes significativos.'
    
    # Analizar desviaciones por zona
    desviaciones = {
        'gruesos': [],
        'intermedios': [],
        'finos': []
    }
    
    for i, (m, id) in enumerate(zip(mezcla_pct, ideal)):
        diff = m - id
        if i < 6:  # Gruesos (hasta #4)
            desviaciones['gruesos'].append(diff)
        elif i < 9:  # Intermedios (#8 a #30)
            desviaciones['intermedios'].append(diff)
        else:  # Finos (#50 a #200)
            desviaciones['finos'].append(diff)
    
    recomendaciones = []
    
    avg_gruesos = np.mean(desviaciones['gruesos']) if desviaciones['gruesos'] else 0
    avg_finos = np.mean(desviaciones['finos']) if desviaciones['finos'] else 0
    
    if avg_gruesos > 5:
        recomendaciones.append('Reducir proporción de agregado grueso')
    elif avg_gruesos < -5:
        recomendaciones.append('Aumentar proporción de agregado grueso')
    
    if avg_finos > 5:
        recomendaciones.append('Reducir proporción de finos')
    elif avg_finos < -5:
        recomendaciones.append('Aumentar proporción de finos')
    
    if not recomendaciones:
        recomendaciones.append('Mantener proporciones actuales')
    
    return {
        'error_cuadratico': error_cuad,
        'rmse': rmse,
        'calidad': calidad,
        'descripcion': descripcion,
        'recomendaciones': recomendaciones,
        'desviacion_gruesos': round(avg_gruesos, 2),
        'desviacion_finos': round(avg_finos, 2)
    }

import numpy as np
from typing import List, Tuple
from config.config import TAMICES_MM

def calcular_valor_power45(tamiz_mm: float) -> float:
    return tamiz_mm ** 0.45 if tamiz_mm > 0 else 0.0

def generar_curva_ideal_power45(tmn: float, tamices: List[float] = None) -> Tuple[List[float], List[float]]:
    if tamices is None: tamices = TAMICES_MM
    max_val = calcular_valor_power45(tmn)
    ideales = []
    for t in tamices:
        if t >= tmn: ideales.append(100.0)
        else:
            v = calcular_valor_power45(t)
            pct = (v / max_val) * 100 if max_val > 0 else 0
            ideales.append(max(0.0, min(100.0, pct)))
    return tamices, ideales

    return round(np.sqrt(mse), 4)

# --- Funciones Restauradas para Optimización (Iowa Method) ---

def calcular_mezcla_granulometrica(proporciones: List[float], granulometrias: List[List[float]]) -> List[float]:
    """Calcula la curva granulométrica combinada ponderada."""
    mezcla = np.zeros(len(granulometrias[0]))
    for pct, gran in zip(proporciones, granulometrias):
        mezcla += np.array(gran) * (pct / 100.0)
    return mezcla.tolist()

def calcular_retenido(mezcla_pasante: List[float]) -> List[float]:
    """Calcula el % retenido individual en cada tamiz."""
    retenidos = []
    anterior = 100.0
    for pasa in mezcla_pasante:
        ret = anterior - pasa
        retenidos.append(max(0.0, round(ret, 2)))
        anterior = pasa
    return retenidos

# Alias de compatibilidad para optimization.py
calcular_error_power45 = calcular_error_power45_normalizado

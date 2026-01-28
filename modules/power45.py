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

def calcular_error_power45_normalizado(mezcla_pct: List[float], ideal_pct: List[float]) -> float:
    min_len = min(len(mezcla_pct), len(ideal_pct))
    if min_len == 0: return 0.0
    mse = sum((m - i) ** 2 for m, i in zip(mezcla_pct[:min_len], ideal_pct[:min_len])) / min_len
    return round(np.sqrt(mse), 4)

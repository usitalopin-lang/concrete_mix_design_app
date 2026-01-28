from typing import Dict, List
import numpy as np

def calcular_CF(pasa_3_8: float, pasa_8: float) -> float:
    Q = 100 - pasa_3_8
    I = pasa_3_8 - pasa_8
    return round((Q / (Q + I)) * 100, 2) if (Q + I) > 0 else 0.0

def calcular_Wadj(pasa_8: float, cemento: float) -> float:
    W = pasa_8
    adj = 0.0588 * cemento - 19.647
    return round(W + adj, 2)

def evaluar_zona(CF: float, Wadj: float) -> Dict:
    evaluacion = {'zona': 'Transición', 'calidad': 'Aceptable'}
    if 45 <= CF <= 75 and 29 <= Wadj <= 44:
        evaluacion = {'zona': 'Zona II (Óptima)', 'calidad': 'Excelente'}
    elif CF > 75:
        evaluacion = {'zona': 'Zona I (Pedregosa)', 'calidad': 'Riesgo Segregación'}
    elif CF < 45:
        evaluacion = {'zona': 'Zona IV (Arenosa)', 'calidad': 'Pegajosa'}
    return evaluacion

def calcular_shilstone_completo(granulometria: List[float], tamices_mm: List[float], cemento: float, **kwargs) -> Dict:
    def get_val(target_mm):
        if not tamices_mm: return 0.0
        idx = min(range(len(tamices_mm)), key=lambda i: abs(tamices_mm[i] - target_mm))
        return granulometria[idx] if idx < len(granulometria) else 0.0
    
    pasa_3_8 = get_val(9.5)
    pasa_8 = get_val(2.36)
    CF = calcular_CF(pasa_3_8, pasa_8)
    Wadj = calcular_Wadj(pasa_8, cemento)
    
    return {'CF': CF, 'Wadj': Wadj, 'W': round(pasa_8, 2), 'evaluacion': evaluar_zona(CF, Wadj)}

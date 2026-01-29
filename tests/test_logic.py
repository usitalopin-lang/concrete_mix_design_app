"""
Script de prueba para verificar la lógica avanzada de diseño de mezclas.
Prueba:
1. Reducción de agua por aditivos.
2. Override de proporciones personalizadas.
"""

import sys
import os

# Agregar directorio raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.faury_joisel import disenar_mezcla_faury
from config import DEFAULTS

def test_logic():
    print("🧪 Iniciando pruebas de lógica avanzada...\n")
    
    # Datos base
    fc = 30
    s_dev = 4
    frac_def = 0.1
    cons = 'Blanda' # 6-9 cm
    tmn = 20
    dens_cem = 3100
    aridos = [
        {'nombre': 'Grava', 'DRS': 2700, 'absorcion': 0.01, 'granulometria': [0]*12},
        {'nombre': 'Arena', 'DRS': 2600, 'absorcion': 0.02, 'granulometria': [100]*12}
    ]
    
    # --- PRUEBA 1: Reducción de Agua ---
    print("--- Prueba 1: Reducción de Agua ---")
    
    # Caso Base (Sin Aditivos)
    res_base = disenar_mezcla_faury(fc, s_dev, frac_def, cons, tmn, dens_cem, aridos)
    w_base = res_base['agua_cemento']['agua_amasado']
    print(f"Agua Base: {w_base} lt/m3")
    
    # Caso Con Superplastificante
    aditivos = [{'nombre': 'Superplastificante X', 'dosis_pct': 1.0, 'densidad_kg_lt': 1.2}]
    res_sp = disenar_mezcla_faury(fc, s_dev, frac_def, cons, tmn, dens_cem, aridos, aditivos_config=aditivos)
    w_sp = res_sp['agua_cemento']['agua_amasado']
    print(f"Agua con SP: {w_sp} lt/m3")
    
    reduccion = (w_base - w_sp) / w_base
    print(f"Reducción: {reduccion:.1%}")
    
    if 0.11 <= reduccion <= 0.13:
        print("✅ Lógica de aditivos CORRECTA (prox 12%)")
    else:
        print("❌ FALLO en lógica de aditivos")

    print("\n--- Prueba 2: Proporciones Personalizadas ---")
    # Intentar forzar 30% Grueso, 70% Arena
    custom_props = [30.0, 70.0]
    
    res_custom = disenar_mezcla_faury(
        fc, s_dev, frac_def, cons, tmn, dens_cem, aridos, 
        proporciones_personalizadas=custom_props
    )
    
    props_vol = res_custom['proporciones_volumetricas']
    total_arido_vol = props_vol['grueso'] + props_vol['fino']
    pct_grueso = props_vol['grueso'] / total_arido_vol
    pct_fino = props_vol['fino'] / total_arido_vol
    
    print(f"Input Custom: Grueso={custom_props[0]}%, Fino={custom_props[1]}%")
    print(f"Output Volumétrico relativo: Grueso={pct_grueso:.1%}, Fino={pct_fino:.1%}")
    
    if abs(pct_grueso - 0.30) < 0.01:
        print("✅ Override de proporciones CORRECTO")
    else:
        print("❌ FALLO en override de proporciones")

if __name__ == "__main__":
    test_logic()

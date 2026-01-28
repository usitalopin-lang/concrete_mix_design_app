"""
Script de prueba para verificar la lógica 'Magallanes' (Manual A/C y Aire).
Prueba:
1. Override de A/C.
2. Cálculo de Agua = Cemento * A/C.
3. Override de Aire.
"""

import sys
import os

# Agregar directorio raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.faury_joisel import disenar_mezcla_faury

def test_magallanes():
    print("Iniciando pruebas de logica Magallanes...\n")
    
    # Datos base
    fc = 30
    s_dev = 4
    frac_def = 0.1
    cons = 'Blanda' 
    tmn = 20
    dens_cem = 3100
    aridos = [
        {'nombre': 'Grava', 'DRS': 2700, 'absorcion': 0.01, 'granulometria': [0]*12},
        {'nombre': 'Arena', 'DRS': 2600, 'absorcion': 0.02, 'granulometria': [100]*12}
    ]
    
    print("--- Prueba Manual A/C y Aire ---")
    
    manual_ac = 0.50
    manual_aire = 25.0 # Litros
    
    res = disenar_mezcla_faury(
        fc, s_dev, frac_def, cons, tmn, dens_cem, aridos,
        manual_ac=manual_ac,
        manual_aire_litros=manual_aire
    )
    
    # Validaciones
    out_ac = res['agua_cemento']['razon']
    out_aire = res['aire']['volumen']
    out_cemento = res['cemento']['cantidad']
    out_agua = res['agua_cemento']['agua_amasado']
    
    print(f"Input: A/C={manual_ac}, Aire={manual_aire}L")
    print(f"Output: A/C={out_ac}, Aire={out_aire}L")
    print(f"Output Calc: Cemento={out_cemento}, Agua={out_agua}")
    
    # Check A/C
    if abs(out_ac - manual_ac) < 0.01:
        print("[OK] A/C Manual respetado.")
    else:
        print("[FAIL] FALLO A/C Manual.")
        
    # Check Aire
    if abs(out_aire - manual_aire) < 0.1:
        print("[OK] Aire Manual respetado.")
    else:
        print("[FAIL] FALLO Aire Manual.")
        
    # Check Relation Water = Cement * A/C
    expected_agua = out_cemento * manual_ac
    if abs(out_agua - expected_agua) < 1.0:
        print(f"[OK] Relacion Agua = Cemento * A/C correcta ({out_agua} vs {expected_agua}).")
    else:
        print(f"[FAIL] FALLO relacion agua. Agua={out_agua}, Esperada={expected_agua}")

if __name__ == "__main__":
    test_magallanes()

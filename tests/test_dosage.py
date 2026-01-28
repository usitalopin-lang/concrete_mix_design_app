
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.faury_joisel import disenar_mezcla_faury

def test_dosage_reference_g30():
    """
    Test dosage logic with parameters extracted from INF-DOH-1842_G30-8.xlsx
    """
    print("Testing Dosage Logic with G30 Reference Parameters...")
    
    # Inputs from reference_analysis.txt
    inputs = {
        'resistencia_fc': 30.0,
        'desviacion_std': 4.0,
        'fraccion_def': 0.10, # 10%
        'consistencia': 'Blanda', # "Blanda"
        'tmn': 25, # 25mm
        'densidad_cemento': 3140,
        'aire_porcentaje': 0.0, # Not specified, assuming 0 extra
        'aridos': [
            {
                'nombre': 'Grava Chancada 25 mm',
                'tipo': 'Grueso',
                'DRS': 2730,
                'absorcion': 0.009,
                'granulometria': [100, 100, 97, 76, 34, 21, 2, 1, 0, 0, 0, 0]
            },
            {
                'nombre': 'Grava Rodada 25 mm',
                'tipo': 'Intermedio',
                'DRS': 2655,
                'absorcion': 0.011,
                'granulometria': [100, 100, 90, 71, 45, 32, 4, 2, 0, 0, 0, 0]
            },
            {
                'nombre': 'Arena 10 mm',
                'tipo': 'Fino',
                'DRS': 2610,
                'absorcion': 0.016,
                'granulometria': [100, 100, 100, 100, 100, 100, 94, 74, 53, 37, 21, 8]
            }
        ]
    }
    
    # Run design
    resultado = disenar_mezcla_faury(
        resistencia_fc=inputs['resistencia_fc'],
        desviacion_std=inputs['desviacion_std'],
        fraccion_def=inputs['fraccion_def'],
        consistencia=inputs['consistencia'],
        tmn=inputs['tmn'],
        densidad_cemento=inputs['densidad_cemento'],
        aridos=inputs['aridos'],
        aire_porcentaje=inputs['aire_porcentaje']
    )
    
    # Print Results
    print("\n--- RESULTS ---")
    print(json.dumps(resultado, indent=2))
    
    # Simple Validations
    assert resultado['resistencia']['fd_mpa'] > 30, "Mean strength should be > fc"
    assert resultado['cemento']['cantidad'] > 200, "Cement content too low"
    print("\n[OK] Verification Successful: Results are within expected ranges.")

if __name__ == "__main__":
    test_dosage_reference_g30()

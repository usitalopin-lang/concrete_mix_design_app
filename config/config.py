"""
Configuración global - Diseño de Mezclas de Concreto.
Estándares: ASTM C33, ACI 211.1, NCh 170.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuración General ---
APP_TITLE = "Diseño de Mezclas - Hormigón Experto"
APP_ICON = "🏗️"

# --- Tamices Estándar (ASTM E11) ---
TAMICES_MM = [50.0, 37.5, 25.0, 19.0, 12.5, 9.5, 4.75, 2.36, 1.18, 0.60, 0.30, 0.15, 0.075]
TAMICES_ASTM = ['2"', '1 1/2"', '1"', '3/4"', '1/2"', '3/8"', '#4', '#8', '#16', '#30', '#50', '#100', '#200']

# Mapeo para leer desde Excel/Google Sheets
MAPEO_COLUMNAS_EXCEL = {
    '2" (50mm)': '2"', '1 1/2" (40mm)': '1 1/2"', '1" (25mm)': '1"', 
    '3/4" (20mm)': '3/4"', '1/2" (12.5mm)': '1/2"', '3/8" (10mm)': '3/8"', 
    'N°4 (5mm)': '#4', 'N°8 (2.5mm)': '#8', 'N°16 (1.25mm)': '#16', 
    'N°30 (0.63mm)': '#30', 'N°50 (0.315mm)': '#50', 'N°100 (0.16mm)': '#100', 
    'N°200 (0.08mm)': '#200'
}

# --- Tablas de Diseño ---
TABLA_AGUA_ACI = {
    9.5:  {'S1': 207, 'S2': 228, 'S3': 243}, 12.5: {'S1': 199, 'S2': 216, 'S3': 228},
    19.0: {'S1': 190, 'S2': 205, 'S3': 216}, 25.0: {'S1': 179, 'S2': 193, 'S3': 202},
    37.5: {'S1': 166, 'S2': 181, 'S3': 190}, 50.0: {'S1': 154, 'S2': 169, 'S3': 178}
}

TABLA_AIRE = {9.5: 30, 12.5: 25, 19.0: 20, 25.0: 15, 37.5: 10, 50.0: 5}

TABLA_AC = {150: 0.80, 200: 0.70, 250: 0.62, 300: 0.55, 350: 0.48, 400: 0.43, 450: 0.38}

TABLA_COEF_T = {0.05: 1.645, 0.10: 1.282, 0.20: 0.842}

PARAMETROS_FAURY = {
    'Fluida': {'M': 0.32, 'N': 0.20}, 'Blanda': {'M': 0.28, 'N': 0.22},
    'Plástica':{'M': 0.24, 'N': 0.24}, 'Seca':   {'M': 0.20, 'N': 0.26},
    'Muy Fluida': {'M': 0.36, 'N': 0.18} # Estimación basada en tendencia
}

REQUISITOS_DURABILIDAD = {
    "Sin riesgo": {'max_ac': 0.60, 'min_cemento': 250},
    "Hormigón a la vista": {'max_ac': 0.50, 'min_cemento': 300},
    "Congelamiento/Deshielo": {'max_ac': 0.45, 'min_cemento': 320},
    "Sulfatos/Marino": {'max_ac': 0.40, 'min_cemento': 350}
}

# Tolerancias banda de trabajo (+/- %)
TOLERANCIAS_BANDA = {
    '2"': 0, '1 1/2"': 4, '1"': 4, '3/4"': 4, '1/2"': 4, '3/8"': 4,
    '#4': 4, '#8': 4, '#16': 4, '#30': 4, '#50': 3, '#100': 2, '#200': 3
}

DEFAULTS = {
    'fc': 30, 
    'resistencia_fc': 30, 
    'desviacion': 1.5, 
    'desviacion_std': 1.5,
    'densidad_cemento': 3100, 
    'tmn': 25.0,
    'fraccion_defectuosa': 0.10,
    'consistencia': 'Blanda',
    'asentamiento': '6-9 cm',
    'aire_porcentaje': 1.0,
    'razon_ac_manual': 0.43,
    'aire_litros_manual': 40.0
}

# --- Constantes para UI (Restauradas) ---
CONSISTENCIAS = {
    'Seca': '0-3 cm',
    'Plástica': '4-5 cm',
    'Blanda': '6-9 cm',
    'Fluida': '10-16 cm',
    'Muy Fluida': '17-21 cm'
}

# --- Pesos de Importancia (Optimización Multi-objetivo) ---
# Estos pesos balancean la importancia de cada criterio en la optimización
PESOS_OPTIMIZACION = {
    'haystack': 0.30,   # Cumplimiento límites ASTM C33
    'tarantula': 0.30,  # Cohesión y gradación (pavimentos)
    'shilstone': 0.20,  # Trabajabilidad y bombeabilidad
    'power45': 0.20     # Ajuste a la curva ideal matemática (objetivo base)
}

# --- Opciones de Aplicación / Elemento ---
APLICACIONES_HORMIGON = [
    "Pavimento / Piso Industrial",
    "Estructural Bombeable",
    "Estructural No Bombeable (Grúa/Capacho)",
    "Pilotes / Fundaciones",
    "Prefabricado Liviano (Bloques/Soleras)",
    "Prefabricado Pesado (Vigas/Dovelas)"
]

TMN_OPCIONES = [9.5, 12.5, 19.0, 25.0, 37.5, 50.0]

# Generar lista de opciones desde el diccionario
EXPOSICION_OPCIONES = list(REQUISITOS_DURABILIDAD.keys())

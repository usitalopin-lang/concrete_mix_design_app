"""
Configuración y constantes para el diseño de mezclas de concreto
Basado en método Faury-Joisel y análisis Shilstone
"""

# Tamices estándar en mm
TAMICES_MM = [40, 25, 20, 12.5, 10, 5, 2.36, 1.18, 0.6, 0.315, 0.16, 0.08]

# Tabla Estimada de Agua (lt/m3) - Basada en ACI 211.1
# Keys: TMN (mm), Values: {Slump Check: Water}
# Slumps: S1=3-5cm, S2=8-10cm, S3=15-18cm
TABLA_AGUA_ACI = {
    10: {'S1': 205, 'S2': 225, 'S3': 240},
    12.5: {'S1': 200, 'S2': 215, 'S3': 230},
    19: {'S1': 185, 'S2': 200, 'S3': 210},
    20: {'S1': 185, 'S2': 200, 'S3': 210}, # Aprox 19/20mm
    25: {'S1': 180, 'S2': 195, 'S3': 205},
    37.5: {'S1': 165, 'S2': 180, 'S3': 190}, # Aprox 40
    40: {'S1': 160, 'S2': 175, 'S3': 185},   # Aprox 37.5/40mm
    50: {'S1': 160, 'S2': 175, 'S3': 185}
}

# Requisitos de Durabilidad (ACI 318 / NCh170)
# Clave: Condición, Valor: {max_ac: float, min_cemento: int}
REQUISITOS_DURABILIDAD = {
    "Sin riesgo": {'max_ac': 1.0, 'min_cemento': 250},
    "Baja permeabilidad / Corrosión moderada": {'max_ac': 0.50, 'min_cemento': 300},
    "Corrosión severa / Cloruros": {'max_ac': 0.40, 'min_cemento': 330},
    "Sulfatos moderados": {'max_ac': 0.50, 'min_cemento': 300},
    "Sulfatos severos": {'max_ac': 0.45, 'min_cemento': 330},
    "Congelamiento y deshielo": {'max_ac': 0.45, 'min_cemento': 300}
}
exposicion_opciones = list(REQUISITOS_DURABILIDAD.keys())
EXPOSICION_OPCIONES = exposicion_opciones


# Tamices nomenclatura ASTM
TAMICES_ASTM = ['1½"', '1"', '¾"', '½"', '⅜"', 'Nº4', 'Nº8', 'Nº16', 'Nº30', 'Nº50', 'Nº100', 'Nº200']

# Tamices para Power 45 (en mm)
TAMICES_POWER45 = [50, 37.5, 25, 19, 12.5, 9.5, 4.75, 2.36, 1.18, 0.6, 0.3, 0.15, 0.075]

# Tabla de razón A/C según resistencia (kg/cm²)
TABLA_AC = {
    200: 0.65,
    250: 0.60,
    300: 0.52,
    350: 0.47,
    400: 0.43,
    450: 0.40,
    500: 0.37,
    550: 0.34
}

# Tabla de aire ocluido según tamaño máximo (mm -> lt/m³)
TABLA_AIRE = {
    10: 50,
    12.5: 45,
    20: 40,
    25: 35,
    40: 25,
    50: 20
}

# Coeficiente t según fracción defectuosa
TABLA_COEF_T = {
    0.05: 1.645,   # 5%
    0.10: 1.282,   # 10%
    0.15: 1.036,   # 15%
    0.20: 0.842    # 20%
}

# Parámetros de curva Faury según consistencia
PARAMETROS_FAURY = {
    'Seca': {'M': 30, 'N': 25.95},
    'Plástica': {'M': 31, 'N': 26.95},
    'Blanda': {'M': 32, 'N': 27.95},
    'Fluida': {'M': 33, 'N': 28.95}
}

# Tipos de consistencia con asentamiento típico
CONSISTENCIAS = {
    'Seca': '0-2 cm',
    'Plástica': '3-5 cm',
    'Blanda': '6-9 cm',
    'Fluida': '10-15 cm'
}

# Restricciones Haystack (ASTM C33) - % que pasa
# (límite_inferior, límite_superior)
RESTRICCIONES_HAYSTACK = {
    50: (100, 100),
    37.5: (95, 100),
    25: (None, None),  # Depende de TMN
    19: (None, None),
    12.5: (None, None),
    9.5: (None, None),
    4.75: (None, None),
    2.36: (None, None),
    1.18: (50, 85),
    0.6: (25, 60),
    0.3: (10, 30),
    0.15: (2, 10),
    0.075: (0, 5)
}

# Restricciones Tarantula - % retenido (límite_alto, límite_bajo)
RESTRICCIONES_TARANTULA = {
    '1½"': (0, 0),
    '1"': (16, 0),
    '¾"': (20, 0),
    '½"': (20, 4),
    '⅜"': (20, 4),
    'Nº4': (20, 4),
    'Nº8': (12, 0),
    'Nº16': (12, 0),
    'Nº30': (20, 4),
    'Nº50': (20, 4),
    'Nº100': (10, 0),
    'Nº200': (5, 0)
}

# Zonas Shilstone - Límites de CF y Wadj
ZONAS_SHILSTONE = {
    'optima': {
        'CF_min': 45,
        'CF_max': 75,
        'Wadj_min': 27,
        'Wadj_max': 45
    }
}

# Tolerancias para banda de trabajo por tamiz
TOLERANCIAS_BANDA = {
    '1½"': 4, '1"': 4, '¾"': 4, '½"': 4, '⅜"': 4, 'Nº4': 4,
    'Nº8': 4, 'Nº16': 4, 'Nº30': 4, 'Nº50': 3, 'Nº100': 2, 'Nº200': 3
}

# Valores por defecto
DEFAULTS = {
    'resistencia_fc': 30.0,
    'desviacion_std': 4.0,
    'fraccion_defectuosa': 0.10,
    'consistencia': 'Blanda',
    'densidad_cemento': 3140,
    'tmn': 25,
    'asentamiento': '6 ± 2 cm',
    'aire_porcentaje': 2.0
}

# Tipos de cemento comunes
TIPOS_CEMENTO = [
    'Cemento Portland Puzolánico',
    'Cemento Portland Tipo I',
    'Cemento Portland Tipo II',
    'Cemento Portland Tipo III',
    'Cemento Portland Tipo IV',
    'Cemento Portland Tipo V',
    'Cemento con Escoria',
    'Cemento Alta Resistencia'
]

# Tamaños máximos nominales comunes
TMN_OPCIONES = [10, 12.5, 20, 25, 40, 50]

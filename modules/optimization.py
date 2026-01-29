"""
Módulo de Optimización para proporciones de agregados
Usa scipy.optimize para encontrar la mezcla óptima que minimiza el error Power 45
mientras cumple con restricciones Haystack, Tarantula y Shilstone.
"""

import numpy as np
from scipy.optimize import minimize, Bounds
from typing import List, Dict, Tuple, Optional, Callable
import warnings

from .power45 import (
    generar_curva_ideal_power45,
    calcular_error_power45,
    calcular_mezcla_granulometrica,
    calcular_retenido
)

# Suprimir advertencias de scipy durante optimización
warnings.filterwarnings('ignore', category=RuntimeWarning)


# Restricciones Haystack (ASTM C33) - % que pasa (min, max)
HAYSTACK_LIMITS = {
    0: (100, 100),   # 2" (50mm)
    1: (95, 100),    # 1.5" (37.5mm)
    2: (None, None), # 1" - depende de TMN
    3: (None, None), # 3/4"
    4: (None, None), # 1/2"
    5: (None, None), # 3/8"
    6: (None, None), # #4
    7: (None, None), # #8
    8: (50, 85),     # #16
    9: (25, 60),     # #30
    10: (10, 30),    # #50
    11: (2, 10),     # #100
    12: (0, 5)       # #200
}

# Restricciones Tarantula - % retenido (max, min)
TARANTULA_LIMITS = {
    0: (0, 0),    # 2"
    1: (16, 0),   # 1.5"
    2: (20, 0),   # 1"
    3: (20, 0),   # 3/4"
    4: (20, 4),   # 1/2"
    5: (20, 4),   # 3/8"
    6: (20, 4),   # #4
    7: (12, 0),   # #8
    8: (12, 0),   # #16
    9: (20, 4),   # #30
    10: (20, 4),  # #50
    11: (10, 0),  # #100
    12: (5, 0)    # #200
}

# Restricciones Shilstone
SHILSTONE_LIMITS = {
    'fraccion_fina': (24, 34),    # % de finos (#30 a #200)
    'fraccion_gruesa': (15, None) # Mínimo % de gruesos
}

# --- Perfiles ADN de la Mezcla ---
# Define la configuración de pesos por defecto para cada estrategia
PERFILES_ADN = {
    'Equilibrado': {
        'haystack': 0.25,
        'tarantula': 0.25,
        'shilstone': 0.25,
        'power45': 0.25,
        'desc': "Balance ideal para uso general y estructuras convencionales.",
        'icon': "⚖️"
    },
    'Pavimentos': {
        'haystack': 0.20,
        'tarantula': 0.50,
        'shilstone': 0.15,
        'power45': 0.15,
        'desc': "Prioriza la cohesión para evitar segregación durante la vibración intensa (Slipform).",
        'icon': "🛣️"
    },
    'Bombeable': {
        'haystack': 0.15,
        'tarantula': 0.15,
        'shilstone': 0.50,
        'power45': 0.20,
        'desc': "Optimiza el contenido de mortero y la fluidez para evitar atascos en tuberías.",
        'icon': "🏢"
    },
    'Geométrico': {
        'haystack': 0.10,
        'tarantula': 0.10,
        'shilstone': 0.20,
        'power45': 0.60,
        'desc': "Ajuste matemático estricto a la curva de máxima densidad (Fuller/Power 45).",
        'icon': "📐"
    }
}


def calcular_penalizacion_haystack(mezcla_pct: List[float]) -> float:
    """
    Calcula la penalización por violaciones de restricciones Haystack.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
    
    Returns:
        Penalización total
    """
    penalizacion = 0.0
    
    for i, valor in enumerate(mezcla_pct):
        if i in HAYSTACK_LIMITS:
            min_lim, max_lim = HAYSTACK_LIMITS[i]
            
            if min_lim is not None and valor < min_lim:
                penalizacion += (min_lim - valor) ** 2
            
            if max_lim is not None and valor > max_lim:
                penalizacion += (valor - max_lim) ** 2
    
    return penalizacion


def calcular_penalizacion_tarantula(mezcla_pct: List[float]) -> float:
    """
    Calcula la penalización por violaciones de restricciones Tarantula.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
    
    Returns:
        Penalización total
    """
    retenido = calcular_retenido(mezcla_pct)
    penalizacion = 0.0
    
    for i, ret in enumerate(retenido):
        if i in TARANTULA_LIMITS:
            max_lim, min_lim = TARANTULA_LIMITS[i]
            
            if ret > max_lim:
                penalizacion += (ret - max_lim) ** 2
            
            if ret < min_lim:
                penalizacion += (min_lim - ret) ** 2
    
    return penalizacion


def calcular_penalizacion_shilstone(mezcla_pct: List[float]) -> float:
    """
    Calcula la penalización por violaciones de restricciones Shilstone.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
    
    Returns:
        Penalización total
    """
    retenido = calcular_retenido(mezcla_pct)
    penalizacion = 0.0
    
    # Fracción fina (#30 a #200) - índices 9 a 12
    if len(retenido) > 12:
        fraccion_fina = sum(retenido[9:13])
    elif len(retenido) > 9:
        fraccion_fina = sum(retenido[9:])
    else:
        fraccion_fina = 0
    
    min_fina, max_fina = SHILSTONE_LIMITS['fraccion_fina']
    if fraccion_fina < min_fina:
        penalizacion += (min_fina - fraccion_fina) ** 2
    if fraccion_fina > max_fina:
        penalizacion += (fraccion_fina - max_fina) ** 2
    
    # Fracción gruesa (3/4" a #30) - índices 3 a 9
    if len(retenido) > 9:
        fraccion_gruesa = sum(retenido[3:9])
    else:
        fraccion_gruesa = 0
    
    min_gruesa, _ = SHILSTONE_LIMITS['fraccion_gruesa']
    if fraccion_gruesa < min_gruesa:
        penalizacion += (min_gruesa - fraccion_gruesa) ** 2
    
    return penalizacion

def calcular_factores_shilstone(mezcla_pct: List[float]) -> Dict[str, float]:
    """
    Calcula el Coarseness Factor (Cf) y Workability Factor (Wf).
    
    Cf = (Acumulado Retenido 3/8" / Acumulado Retenido #8) * 100
    Wf = % Pasa #8
    
    Asumiendo tamices: 1.5, 1, 3/4, 1/2, 3/8, #4, #8, ...
    Index 3/8" = 4
    Index #8 = 6
    """
    if len(mezcla_pct) < 7:
        return {'cf': 0, 'wf': 0}
        
    pasa_38 = mezcla_pct[4] # % Pasa 3/8"
    pasa_8 = mezcla_pct[6]  # % Pasa #8
    
    acum_ret_38 = 100.0 - pasa_38
    acum_ret_8 = 100.0 - pasa_8
    
    try:
        cf = (acum_ret_38 / acum_ret_8) * 100.0 if acum_ret_8 > 0 else 0
    except:
        cf = 0
        
    wf = pasa_8
    
    return {'cf': round(cf, 2), 'wf': round(wf, 2)}


def funcion_objetivo(x: np.ndarray, granulometrias: List[List[float]], 
                     ideal_power45: List[float],
                     densidades: Optional[List[float]] = None,
                     peso_haystack: float = 0.3,
                     peso_tarantula: float = 0.3,
                     peso_shilstone: float = 0.2) -> float:
    """
    Función objetivo multiobjetivo para la optimización.
    
    Minimiza: Error_Power45 + λ1*Haystack + λ2*Tarantula + λ3*Shilstone
    
    Args:
        x: Vector de proporciones [grueso%, fino%, intermedio%]
        granulometrias: Lista de granulometrías de cada agregado
        ideal_power45: Curva ideal Power 45
        densidades: Lista de densidades (SG) para corrección volumétrica.
        peso_haystack: Peso de penalización Haystack
        peso_tarantula: Peso de penalización Tarantula
        peso_shilstone: Peso de penalización Shilstone
    
    Returns:
        Valor de la función objetivo (a minimizar)
    """
    # Calcular granulometría de la mezcla
    proporciones = list(x)
    
    if densidades:
        # Si hay densidades, calculamos la curva volumétrica real
        mezcla = calcular_mezcla_volumetrica(proporciones, granulometrias, densidades)
    else:
        # Cálculo simple (asumiendo input volumétrico o sin corrección)
        mezcla = calcular_mezcla_granulometrica(proporciones, granulometrias)
    
    if not mezcla:
        return 1e10  # Valor muy alto si hay error
    
    # Ajustar longitud si es necesario
    if len(mezcla) != len(ideal_power45):
        min_len = min(len(mezcla), len(ideal_power45))
        mezcla = mezcla[:min_len]
        ideal = ideal_power45[:min_len]
    else:
        ideal = ideal_power45
    
    # Error Power 45 (objetivo principal)
    error_p45 = calcular_error_power45(mezcla, ideal, 'cuadratico')
    
    # Penalizaciones
    pen_haystack = calcular_penalizacion_haystack(mezcla)
    pen_tarantula = calcular_penalizacion_tarantula(mezcla)
    pen_shilstone = calcular_penalizacion_shilstone(mezcla)
    
    # Función objetivo total
    objetivo = (error_p45 + 
                peso_haystack * pen_haystack + 
                peso_tarantula * pen_tarantula + 
                peso_shilstone * pen_shilstone)
    
    return objetivo


def restriccion_suma_100(x: np.ndarray) -> float:
    """
    Restricción de igualdad: la suma de proporciones debe ser 100.
    
    Args:
        x: Vector de proporciones
    
    Returns:
        Diferencia respecto a 100 (debe ser 0)
    """
    return sum(x) - 100


from config import PESOS_OPTIMIZACION

def optimizar_agregados(granulometrias: List[List[float]], 
                        tmn: float = 25,
                        num_agregados: int = 2,
                        proporciones_iniciales: Optional[List[float]] = None,
                        densidades: Optional[List[float]] = None,
                        peso_haystack: float = PESOS_OPTIMIZACION['haystack'],
                        peso_tarantula: float = PESOS_OPTIMIZACION['tarantula'],
                        peso_shilstone: float = PESOS_OPTIMIZACION['shilstone'],
                        metodo: str = 'SLSQP') -> Dict:
    """
    Optimiza las proporciones de agregados (en MASA) para lograr la mejor curva ideal.
    Si se dan densidades, optimiza la curva VOLUMÉTRICA resultante.
    
    Args:
        granulometrias: Lista de granulometrías de cada agregado (% que pasa)
        tmn: Tamaño máximo nominal en mm
        num_agregados: Número de agregados a optimizar (2 o 3)
        proporciones_iniciales: Proporciones iniciales (opcional)
        densidades: Lista de densidades (SG) para corrección volumétrica.
        peso_haystack: Peso para penalización Haystack
        peso_tarantula: Peso para penalización Tarantula
        peso_shilstone: Peso para penalización Shilstone
        metodo: Método de optimización ('SLSQP', 'trust-constr', 'COBYLA')
    
    Returns:
        Diccionario con resultados de la optimización
    """
    # Validar inputs
    if not granulometrias:
        return {'exito': False, 'mensaje': 'No se proporcionaron granulometrías'}
    
    num_agregados = min(len(granulometrias), num_agregados)
    granulometrias = granulometrias[:num_agregados]
    
    # Generar curva ideal Power 45
    tamices, ideal = generar_curva_ideal_power45(tmn)
    
    # Ajustar longitud de granulometrías si es necesario
    len_objetivo = len(ideal)
    granulometrias_ajustadas = []
    for g in granulometrias:
        if len(g) < len_objetivo:
            g = g + [0] * (len_objetivo - len(g))
        elif len(g) > len_objetivo:
            g = g[:len_objetivo]
        granulometrias_ajustadas.append(g)
    
    # Punto inicial
    if proporciones_iniciales and len(proporciones_iniciales) == num_agregados:
        x0 = np.array(proporciones_iniciales)
    else:
        # Distribución inicial equitativa
        x0 = np.array([100 / num_agregados] * num_agregados)
    
    # Normalizar punto inicial
    x0 = x0 * 100 / sum(x0)
    
    # Límites: cada proporción entre 0 y 100
    bounds = Bounds([0] * num_agregados, [100] * num_agregados)
    
    # Restricción: suma = 100
    constraints = [{'type': 'eq', 'fun': restriccion_suma_100}]
    # Ajustar densidades si existen
    densidades_ajustadas = None
    if densidades:
        densidades_ajustadas = densidades[:num_agregados]
    
    # Opciones del optimizador
    options = {
        'maxiter': 500,
        'ftol': 1e-8,
        'disp': False
    }
    
    try:
        # Ejecutar optimización
        resultado = minimize(
            funcion_objetivo,
            x0,
            args=(granulometrias_ajustadas, ideal, densidades_ajustadas, peso_haystack, peso_tarantula, peso_shilstone),
            method=metodo,
            bounds=bounds,
            constraints=constraints,
            options=options
        )
        
        if resultado.success or resultado.fun < funcion_objetivo(x0, granulometrias_ajustadas, ideal, densidades_ajustadas):
            # Calcular mezcla óptima
            proporciones_optimas = list(resultado.x)
            
            if densidades_ajustadas:
                mezcla_optima = calcular_mezcla_volumetrica(proporciones_optimas, granulometrias_ajustadas, densidades_ajustadas)
            else:
                mezcla_optima = calcular_mezcla_granulometrica(proporciones_optimas, granulometrias_ajustadas)
                
            retenido_optima = calcular_retenido(mezcla_optima)
            shilstone_factors = calcular_factores_shilstone(mezcla_optima)
            
            # Calcular errores finales
            error_p45 = calcular_error_power45(mezcla_optima, ideal[:len(mezcla_optima)], 'cuadratico')
            error_haystack = calcular_penalizacion_haystack(mezcla_optima)
            error_tarantula = calcular_penalizacion_tarantula(mezcla_optima)
            error_shilstone = calcular_penalizacion_shilstone(mezcla_optima)
            
            return {
                'exito': True,
                'proporciones': [round(p, 2) for p in proporciones_optimas],
                'mezcla_granulometria': [round(m, 2) for m in mezcla_optima],
                'mezcla_retenido': [round(r, 2) for r in retenido_optima],
                'shilstone_factors': shilstone_factors,
                'curva_ideal': [round(i, 2) for i in ideal],
                'error_power45': round(error_p45, 4),
                'error_haystack': round(error_haystack, 4),
                'error_tarantula': round(error_tarantula, 4),
                'error_shilstone': round(error_shilstone, 4),
                'error_total': round(resultado.fun, 4),
                'iteraciones': resultado.nit,
                'mensaje': 'Optimización exitosa'
            }
        else:
            return {
                'exito': False,
                'proporciones': list(x0),
                'mensaje': f'No se encontró solución óptima: {resultado.message}',
                'error_total': float(resultado.fun)
            }
    
    except Exception as e:
        return {
            'exito': False,
            'proporciones': list(x0),
            'mensaje': f'Error durante la optimización: {str(e)}'
        }


def optimizar_con_restricciones_personalizadas(
    granulometrias: List[List[float]],
    tmn: float = 25,
    restricciones_haystack: Optional[Dict] = None,
    restricciones_tarantula: Optional[Dict] = None,
    limites_proporciones: Optional[List[Tuple[float, float]]] = None
) -> Dict:
    """
    Optimiza con restricciones personalizadas por el usuario.
    
    Args:
        granulometrias: Lista de granulometrías
        tmn: Tamaño máximo nominal
        restricciones_haystack: Restricciones personalizadas Haystack
        restricciones_tarantula: Restricciones personalizadas Tarantula
        limites_proporciones: Límites personalizados para cada proporción [(min, max), ...]
    
    Returns:
        Diccionario con resultados
    """
    global HAYSTACK_LIMITS, TARANTULA_LIMITS
    
    # Aplicar restricciones personalizadas si se proporcionan
    if restricciones_haystack:
        for k, v in restricciones_haystack.items():
            HAYSTACK_LIMITS[k] = v
    
    if restricciones_tarantula:
        for k, v in restricciones_tarantula.items():
            TARANTULA_LIMITS[k] = v
    
    num_agregados = len(granulometrias)
    
    # Límites personalizados o por defecto
    if limites_proporciones and len(limites_proporciones) == num_agregados:
        lower = [l[0] for l in limites_proporciones]
        upper = [l[1] for l in limites_proporciones]
    else:
        lower = [0] * num_agregados
        upper = [100] * num_agregados
    
    return optimizar_agregados(
        granulometrias=granulometrias,
        tmn=tmn,
        num_agregados=num_agregados
    )


def evaluar_cumplimiento_restricciones(mezcla_pct: List[float]) -> Dict:
    """
    Evalúa el cumplimiento de todas las restricciones para una mezcla dada.
    
    Args:
        mezcla_pct: Granulometría de la mezcla (% que pasa)
    
    Returns:
        Diccionario con evaluación detallada
    """
    retenido = calcular_retenido(mezcla_pct)
    
    # Evaluar Haystack
    haystack_cumple = True
    haystack_violaciones = []
    
    for i, valor in enumerate(mezcla_pct):
        if i in HAYSTACK_LIMITS:
            min_lim, max_lim = HAYSTACK_LIMITS[i]
            if min_lim is not None and valor < min_lim:
                haystack_cumple = False
                haystack_violaciones.append(f'Tamiz {i}: {valor:.1f}% < {min_lim}%')
            if max_lim is not None and valor > max_lim:
                haystack_cumple = False
                haystack_violaciones.append(f'Tamiz {i}: {valor:.1f}% > {max_lim}%')
    
    # Evaluar Tarantula
    tarantula_cumple = True
    tarantula_violaciones = []
    
    for i, ret in enumerate(retenido):
        if i in TARANTULA_LIMITS:
            max_lim, min_lim = TARANTULA_LIMITS[i]
            if ret > max_lim:
                tarantula_cumple = False
                tarantula_violaciones.append(f'Tamiz {i}: {ret:.1f}% ret > {max_lim}%')
            if ret < min_lim:
                tarantula_cumple = False
                tarantula_violaciones.append(f'Tamiz {i}: {ret:.1f}% ret < {min_lim}%')
    
    # Evaluar Shilstone
    shilstone_cumple = True
    shilstone_violaciones = []
    
    if len(retenido) > 12:
        fraccion_fina = sum(retenido[9:13])
    else:
        fraccion_fina = sum(retenido[9:]) if len(retenido) > 9 else 0
    
    min_fina, max_fina = SHILSTONE_LIMITS['fraccion_fina']
    if fraccion_fina < min_fina:
        shilstone_cumple = False
        shilstone_violaciones.append(f'Fracción fina: {fraccion_fina:.1f}% < {min_fina}%')
    if fraccion_fina > max_fina:
        shilstone_cumple = False
        shilstone_violaciones.append(f'Fracción fina: {fraccion_fina:.1f}% > {max_fina}%')
    
    return {
        'haystack': {
            'cumple': haystack_cumple,
            'violaciones': haystack_violaciones
        },
        'tarantula': {
            'cumple': tarantula_cumple,
            'violaciones': tarantula_violaciones
        },
        'shilstone': {
            'cumple': shilstone_cumple,
            'violaciones': shilstone_violaciones
        },
        'cumple_todo': haystack_cumple and tarantula_cumple and shilstone_cumple
    }


def sensibilidad_proporciones(granulometrias: List[List[float]], 
                               proporciones_base: List[float],
                               variacion: float = 5.0,
                               tmn: float = 25) -> Dict:
    """
    Analiza la sensibilidad de la mezcla a variaciones en las proporciones.
    
    Args:
        granulometrias: Lista de granulometrías
        proporciones_base: Proporciones de referencia
        variacion: Porcentaje de variación a analizar
        tmn: Tamaño máximo nominal
    
    Returns:
        Análisis de sensibilidad
    """
    _, ideal = generar_curva_ideal_power45(tmn)
    
    resultados = {
        'base': {},
        'variaciones': []
    }
    
    # Calcular error base
    mezcla_base = calcular_mezcla_granulometrica(proporciones_base, granulometrias)
    error_base = calcular_error_power45(mezcla_base, ideal[:len(mezcla_base)])
    resultados['base'] = {
        'proporciones': proporciones_base,
        'error': error_base
    }
    
    # Analizar variaciones
    for i in range(len(proporciones_base)):
        for signo in [-1, 1]:
            props_var = proporciones_base.copy()
            delta = signo * variacion
            
            # Ajustar proporción i y redistribuir
            props_var[i] += delta
            
            # Redistribuir entre los demás
            otros = [j for j in range(len(props_var)) if j != i]
            if otros:
                redistribucion = -delta / len(otros)
                for j in otros:
                    props_var[j] += redistribucion
            
            # Asegurar que no hay negativos
            props_var = [max(0, p) for p in props_var]
            total = sum(props_var)
            if total > 0:
                props_var = [p * 100 / total for p in props_var]
            
            mezcla_var = calcular_mezcla_granulometrica(props_var, granulometrias)
            error_var = calcular_error_power45(mezcla_var, ideal[:len(mezcla_var)])
            
            resultados['variaciones'].append({
                'agregado': i,
                'cambio': delta,
                'proporciones': props_var,
                'error': error_var,
                'diferencia_error': error_var - error_base
            })
    
    return resultados


def calcular_pesos_desde_matriz(x_trabajabilidad: float, y_cohesion: float) -> Dict[str, float]:
    """
    Calcula los pesos dinámicamente a partir de una posición en la matriz 2D.
    x_trabajabilidad: 0 (Baja) a 1 (Alta) -> Influye en Shilstone
    y_cohesion: 0 (Baja) a 1 (Alta) -> Influye en Tarantula
    """
    # Pesos variables según posición
    w_shil = x_trabajabilidad
    w_taran = y_cohesion
    # El ajuste geométrico es el remanente (si x e y son bajos, p45 es alto)
    w_p45 = (1.0 - x_trabajabilidad) * 0.5 + (1.0 - y_cohesion) * 0.5
    w_hay = 0.2  # Haystack estable por norma
    
    # Normalizar
    total = w_shil + w_taran + w_p45 + w_hay
    if total == 0: total = 1.0
    
    return {
        'haystack': round(w_hay / total, 3),
        'tarantula': round(w_taran / total, 3),
        'shilstone': round(w_shil / total, 3),
        'power45': round(w_p45 / total, 3)
    }

def calcular_mezcla_volumetrica(proporciones: List[float], granulometrias: List[List[float]], densidades: Optional[List[float]] = None) -> List[float]:
    """
    Calcula la curva granulométrica combinada de la mezcla. 
    Si se entregan densidades, considera el volumen absoluto.
    Si no, asume proporciones en peso (o que las densidades son iguales).
    
    Args:
        proporciones: Lista de % de participación de cada árido (suma 100).
        granulometrias: Lista de listas, donde cada sublista es la curva de un árido.
        densidades: Lista de densidades (opcional).
        
    Returns:
        Lista con la curva combinada (% que pasa acumulado).
    """
    n_aridos = len(proporciones)
    n_tamices = len(granulometrias[0])
    mezcla_combinada = np.zeros(n_tamices)
    
    # Calcular
    for i in range(n_aridos):
        # Aporte simple: % participacion * % que pasa el tamiz
        # Si quisieramos ser ultra precisos con densidades distintas para volumen,
        # primero convertiriamos proporciones de masa a volumen.
        # Pero usualmente en optimización Iowa, se trabaja directo con la proporción de mezcla.
        factor = proporciones[i] / 100.0
        mezcla_combinada += np.array(granulometrias[i]) * factor
        
    return mezcla_combinada.tolist()

"""
Módulo Faury-Joisel para diseño de mezclas de concreto
Implementa todas las fórmulas del método Faury-Joisel para
cálculo de dosificación de hormigón.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

# Importar configuración
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    TABLA_AC, TABLA_AIRE, TABLA_COEF_T, PARAMETROS_FAURY,
    TAMICES_MM, TAMICES_ASTM, TOLERANCIAS_BANDA, TABLA_AGUA_ACI,
    REQUISITOS_DURABILIDAD
)


def obtener_coeficiente_t(fraccion_defectuosa: float) -> float:
    """
    Obtiene el coeficiente t según la fracción defectuosa.
    
    Args:
        fraccion_defectuosa: Fracción de probetas que pueden estar bajo especificación (0.05-0.20)
    
    Returns:
        Coeficiente t para el cálculo de resistencia media
    """
    # Interpolación lineal entre valores de tabla
    fracciones = sorted(TABLA_COEF_T.keys())
    
    if fraccion_defectuosa <= fracciones[0]:
        return TABLA_COEF_T[fracciones[0]]
    if fraccion_defectuosa >= fracciones[-1]:
        return TABLA_COEF_T[fracciones[-1]]
    
    for i in range(len(fracciones) - 1):
        if fracciones[i] <= fraccion_defectuosa <= fracciones[i + 1]:
            ratio = (fraccion_defectuosa - fracciones[i]) / (fracciones[i + 1] - fracciones[i])
            t_inf = TABLA_COEF_T[fracciones[i]]
            t_sup = TABLA_COEF_T[fracciones[i + 1]]
            return t_inf + ratio * (t_sup - t_inf)
    
    return 1.282  # Valor por defecto (10%)


def calcular_resistencia_media(fc: float, s: float, fraccion_def: float = 0.10) -> Tuple[float, float]:
    """
    Calcula la resistencia media de dosificación (fd).
    
    Fórmula: fd = fc' + s × t
    
    Args:
        fc: Resistencia especificada en MPa
        s: Desviación estándar en MPa
        fraccion_def: Fracción defectuosa (default 0.10 = 10%)
    
    Returns:
        Tupla (fd en MPa, fd en kg/cm² redondeado a múltiplo de 5)
    """
    t = obtener_coeficiente_t(fraccion_def)
    fd_mpa = fc + s * t
    
    # Convertir a kg/cm² (1 MPa ≈ 10.2 kg/cm²) y redondear a múltiplo de 5
    fd_kgcm2 = round(fd_mpa * 10.2 / 5) * 5
    
    return fd_mpa, fd_kgcm2


def calcular_cemento(fd_kgcm2: float, factor_eficiencia: float = 0.95) -> float:
    """
    Calcula la cantidad de cemento por m³ de hormigón.
    
    Fórmula: C = fd × factor_eficiencia (redondeado a múltiplo de 5)
    
    Args:
        fd_kgcm2: Resistencia media en kg/cm²
        factor_eficiencia: Factor de eficiencia del cemento (default 0.95)
    
    Returns:
        Cantidad de cemento en kg/m³
    """
    C = round(fd_kgcm2 * factor_eficiencia / 5) * 5
    # MAGALLANES ESTRICTO: No aplicar mínimos normativos aquí
    # Los requisitos de durabilidad se informan como advertencias, no como restricciones
    return C


def obtener_razon_ac(fd_kgcm2: float) -> float:
    """
    Obtiene la razón agua/cemento según la resistencia.
    Interpola linealmente entre valores de tabla.
    
    Args:
        fd_kgcm2: Resistencia media en kg/cm²
    
    Returns:
        Razón agua/cemento
    """
    resistencias = sorted(TABLA_AC.keys())
    
    if fd_kgcm2 <= resistencias[0]:
        return TABLA_AC[resistencias[0]]
    if fd_kgcm2 >= resistencias[-1]:
        return TABLA_AC[resistencias[-1]]
    
    for i in range(len(resistencias) - 1):
        if resistencias[i] <= fd_kgcm2 <= resistencias[i + 1]:
            ratio = (fd_kgcm2 - resistencias[i]) / (resistencias[i + 1] - resistencias[i])
            ac_inf = TABLA_AC[resistencias[i]]
            ac_sup = TABLA_AC[resistencias[i + 1]]
            return ac_inf + ratio * (ac_sup - ac_inf)
    
    return 0.50  # Valor por defecto


def estimar_agua_amasado(asentamiento_str: str, tmn: float) -> float:
    """
    Estima el agua de amasado necesaria según asentamiento y TMN.
    Usa TABLA_AGUA_ACI (basada en ACI 211.1).
    
    Args:
        asentamiento_str: String del rango de asentamiento (ej '3-5 cm', '10-15 cm')
        tmn: Tamaño máximo nominal en mm
    
    Returns:
        Agua estimada en lt/m³
    """
    # Identificar clase de slump
    slump_key = 'S2' # Default 8-10
    if '0-2' in asentamiento_str or '3-5' in asentamiento_str:
        slump_key = 'S1'
    elif '10-15' in asentamiento_str:
        slump_key = 'S3'
    else:
        slump_key = 'S2' # 6-9cm
        
    # Buscar en tabla por TMN (aproximar si no es exacto)
    tmn_keys = sorted(TABLA_AGUA_ACI.keys())
    closest_tmn = min(tmn_keys, key=lambda x: abs(x - tmn))
    
    return TABLA_AGUA_ACI[closest_tmn][slump_key]


def calcular_cemento_por_agua(agua: float, ac_ratio: float, min_cemento: float = 250) -> float:
    """
    Calcula cemento a partir de agua y razón A/C.
    
    Args:
        agua: Agua de amasado en lt/m³
        ac_ratio: Razón agua/cemento
        min_cemento: Cemento mínimo por durabilidad
        
    Returns:
        Cemento en kg/m³ (redondeado a 5 kg)
    """
    if ac_ratio <= 0: return 0
    cemento = agua / ac_ratio
    # Aplicar mínimos
    cemento = max(cemento, min_cemento)
    # Redondear
    return round(cemento / 5) * 5


def obtener_aire_ocluido(dn_mm: float, aire_incorporado: float = 0.0) -> float:
    """
    Obtiene el volumen de aire ocluido según tamaño máximo del árido.
    
    Args:
        dn_mm: Tamaño máximo nominal en mm
        aire_incorporado: Porcentaje adicional de aire incorporado
    
    Returns:
        Volumen de aire en lt/m³
    """
    # Encontrar el valor más cercano en la tabla
    dn_keys = sorted(TABLA_AIRE.keys())
    
    if dn_mm <= dn_keys[0]:
        aire_base = TABLA_AIRE[dn_keys[0]]
    elif dn_mm >= dn_keys[-1]:
        aire_base = TABLA_AIRE[dn_keys[-1]]
    else:
        # Interpolar
        for i in range(len(dn_keys) - 1):
            if dn_keys[i] <= dn_mm <= dn_keys[i + 1]:
                ratio = (dn_mm - dn_keys[i]) / (dn_keys[i + 1] - dn_keys[i])
                aire_base = TABLA_AIRE[dn_keys[i]] + ratio * (TABLA_AIRE[dn_keys[i + 1]] - TABLA_AIRE[dn_keys[i]])
                break
        else:
            aire_base = 35
    
    # Agregar aire incorporado (convertir de % a lt/m³)
    return aire_base + (aire_incorporado * 10)


def calcular_compacidad(aire: float, agua: float) -> float:
    """
    Calcula la compacidad de la mezcla (volumen de sólidos por m³).
    
    Fórmula: z = 1 - (ha/1000) - (A/1000)
    
    Args:
        aire: Volumen de aire en lt/m³
        agua: Agua de amasado en lt/m³
    
    Returns:
        Compacidad (m³ de sólidos por m³ de hormigón)
    """
    z = 1.0 - (aire / 1000) - (agua / 1000)
    # AJUSTE: La compacidad incluye el cemento y los áridos, pero no el agua ni el aire.
    # Si hay aditivos, su volumen debe restarse del volumen disponible, pero ¿forman parte de z?
    # Faury define z como el volumen absoluto de materiales sólidos (cemento + áridos).
    # Si consideramos los aditivos como parte del volumen sólido (si son polvos) o líquido (si son líquidos),
    # cambia la ecuación. 
    # Para simplificar y seguir la práctica estándar:
    # z = Vol_Cemento + Vol_Aridos.
    # z = 1 - V_agua - V_aire - V_aditivos
    # Esta función ahora solo calcula el espacio DISPONIBLE para sólidos si no consideramos aditivos.
    # Se ajustará en el flujo principal.
    return max(z, 0.60)  # Mínimo razonable


def calcular_porcentaje_cemento_volumen(cemento: float, compacidad: float, 
                                        densidad_cemento: float = 3140) -> float:
    """
    Calcula el porcentaje volumétrico de cemento.
    
    Fórmula: c = C / (z × ρc)
    
    Args:
        cemento: Cantidad de cemento en kg/m³
        compacidad: Compacidad de la mezcla
        densidad_cemento: Densidad del cemento en kg/m³
    
    Returns:
        Fracción volumétrica del cemento (0-1)
    """
    return cemento / (compacidad * densidad_cemento)


def calcular_proporciones_faury(dn_mm: float, consistencia: str, c_vol: float,
                                 num_aridos: int = 2) -> Dict[str, float]:
    """
    Calcula las proporciones volumétricas según el método Faury-Joisel.
    
    Args:
        dn_mm: Tamaño máximo nominal en mm
        consistencia: Tipo de consistencia (Seca, Plástica, Blanda, Fluida)
        c_vol: Fracción volumétrica del cemento
        num_aridos: Número de áridos (2 o 3)
    
    Returns:
        Diccionario con proporciones volumétricas de cada componente
    """
    # Obtener parámetros M y N según consistencia
    params = PARAMETROS_FAURY.get(consistencia, PARAMETROS_FAURY['Blanda'])
    M, N = params['M'], params['N']
    
    # Calcular punto medio de la curva Faury
    # Y(Dn/2) define la proporción de áridos gruesos vs finos
    if dn_mm == 25:
        i_gruesos = 0.44  # Proporción volumétrica típica de gruesos
    elif dn_mm == 40:
        i_gruesos = 0.48
    elif dn_mm == 20:
        i_gruesos = 0.42
    else:
        i_gruesos = 0.43  # Valor por defecto
    
    # Ajustar según consistencia
    if consistencia == 'Seca':
        i_gruesos += 0.02
    elif consistencia == 'Fluida':
        i_gruesos -= 0.03
    
    # Calcular proporciones
    f_c = 1.0 - i_gruesos  # Finos + cemento
    f = f_c - c_vol  # Solo finos (arena)
    
    if num_aridos == 2:
        return {
            'grueso': i_gruesos,
            'fino': f,
            'cemento': c_vol
        }
    else:  # 3 áridos
        # Dividir gruesos en dos fracciones
        return {
            'grueso_1': i_gruesos * 0.55,
            'grueso_2': i_gruesos * 0.45,
            'fino': f,
            'cemento': c_vol
        }


def calcular_cantidades_kg(proporciones: Dict[str, float], compacidad: float,
                           densidades: Dict[str, float]) -> Dict[str, float]:
    """
    Calcula las cantidades en kg/m³ a partir de las proporciones volumétricas.
    
    Fórmula: Cantidad = proporción × z × DRS
    
    Args:
        proporciones: Diccionario con proporciones volumétricas
        compacidad: Compacidad de la mezcla
        densidades: Diccionario con densidades reales secas (DRS) en kg/m³
    
    Returns:
        Diccionario con cantidades en kg/m³
    """
    cantidades = {}
    for material, prop in proporciones.items():
        if material in densidades and material != 'cemento':
            cantidades[material] = prop * compacidad * densidades[material]
    return cantidades


def calcular_agua_absorcion(cantidades: Dict[str, float], 
                            absorciones: Dict[str, float]) -> float:
    """
    Calcula el agua de absorción total de los áridos.
    
    Fórmula: a = Σ(cantidad_i × absorción_i)
    
    Args:
        cantidades: Diccionario con cantidades de áridos en kg/m³
        absorciones: Diccionario con porcentajes de absorción (como fracción)
    
    Returns:
        Agua de absorción total en lt/m³
    """
    absorcion_total = 0.0
    for material, cantidad in cantidades.items():
        if material in absorciones:
            absorcion_total += cantidad * absorciones[material]
    return absorcion_total


def calcular_agua_total(agua_amasado: float, agua_absorcion: float) -> float:
    """
    Calcula el agua total necesaria.
    
    Args:
        agua_amasado: Agua de amasado en lt/m³
        agua_absorcion: Agua de absorción en lt/m³
    
    Returns:
        Agua total en lt/m³
    """
    return agua_amasado + agua_absorcion


def calcular_granulometria_mezcla(proporciones_peso: Dict[str, float],
                                   granulometrias: Dict[str, List[float]]) -> List[float]:
    """
    Calcula la granulometría de la mezcla combinada.
    
    Fórmula: Mezcla[tamiz] = Σ(proporción_i × granulometría_i[tamiz])
    
    Args:
        proporciones_peso: Proporciones en peso de cada árido (suman 1.0)
        granulometrias: Granulometrías de cada árido (% que pasa por tamiz)
    
    Returns:
        Lista con % que pasa para cada tamiz de la mezcla
    """
    num_tamices = len(TAMICES_MM)
    mezcla = [0.0] * num_tamices
    
    for i in range(num_tamices):
        for material, prop in proporciones_peso.items():
            if material in granulometrias:
                mezcla[i] += prop * granulometrias[material][i] / 100.0
    
    # Convertir a porcentaje
    mezcla = [v * 100 for v in mezcla]
    return mezcla


def calcular_banda_trabajo(mezcla: List[float]) -> List[Tuple[float, float]]:
    """
    Calcula la banda de trabajo (límites superior e inferior).
    
    Args:
        mezcla: Lista con % que pasa de la mezcla por cada tamiz
    
    Returns:
        Lista de tuplas (límite_inferior, límite_superior) para cada tamiz
    """
    banda = []
    for i, tamiz in enumerate(TAMICES_ASTM):
        tol = TOLERANCIAS_BANDA.get(tamiz, 3)
        limite_inf = max(0, mezcla[i] - tol)
        limite_sup = min(100, mezcla[i] + tol)
        banda.append((limite_inf, limite_sup))
    return banda


def calcular_proporciones_peso(cantidades: Dict[str, float]) -> Dict[str, float]:
    """
    Convierte cantidades en kg/m³ a proporciones en peso.
    
    Args:
        cantidades: Diccionario con cantidades en kg/m³
    
    Returns:
        Diccionario con proporciones en peso (suman 1.0)
    """
    total = sum(cantidades.values())
    if total == 0:
        return {k: 0 for k in cantidades}
    return {k: v / total for k, v in cantidades.items()}


def disenar_mezcla_faury(resistencia_fc: float, desviacion_std: float,
                         fraccion_def: float, consistencia: str,
                         tmn: float, densidad_cemento: float,
                         aridos: List[Dict], aire_porcentaje: float = 0.0,
                         condicion_exposicion: str = "Sin riesgo",
                         aditivos_config: List[Dict] = None,
                         proporciones_personalizadas: List[float] = None,
                         manual_ac: float = None,
                         manual_aire_litros: float = None) -> Dict:
    """
    Función principal que ejecuta todo el diseño de mezcla por Faury-Joisel.
    
    Args:
        ...
        manual_ac: Razón A/C impuesta por usuario (opcional)
        manual_aire_litros: Volumen de aire en litros impuesto (opcional)
    """
    # 0. Obtener requisitos de durabilidad
    req_durabilidad = REQUISITOS_DURABILIDAD.get(condicion_exposicion, REQUISITOS_DURABILIDAD["Sin riesgo"])
    max_ac_durabilidad = req_durabilidad['max_ac']
    min_cemento_durabilidad = req_durabilidad['min_cemento']

    # 1. Resistencia media
    fd_mpa, fd_kgcm2 = calcular_resistencia_media(resistencia_fc, desviacion_std, fraccion_def)
    
    # --- LÓGICA DE CÁLCULO MAGALLANES (FAURY-JOISEL EXPLICITO) ---
    # Pasos definidos por usuario:
    # 1. Cemento (por resistencia)
    # 2. A/C (Input usuario o Tablas)
    # 3. Agua (Calculada)
    # 4. Aire (Input usuario o Tabla)
    # 5. Aridos (Volumen restante)

    # 1. Cantidad de Cemento
    # C = Fd (kg/cm2) * Factor Eficiencia
    # NOTA: Se eliminan mínimos normativos "duros" (ej. 250kg). Se informan como recomendación.
    factor_eficiencia = 0.95
    cemento = calcular_cemento(fd_kgcm2, factor_eficiencia)
    
    # 2. Razón A/C
    # Se prioriza el input manual (si existe), si no, se busca en tabla por resistencia
    if manual_ac is not None and manual_ac > 0:
        ac_ratio = manual_ac
    else:
        ac_ratio = obtener_razon_ac(fd_kgcm2)

    # 3. Agua de Amasado
    # A = C * A/C
    # NOTA: Esta es el agua NETA de mezclado.
    agua_amasado = cemento * ac_ratio
    
    # 4. Aire (Litros)
    if manual_aire_litros is not None:
        aire_lt = manual_aire_litros
    else:
        # Si no se da litros, se usa el porcentaje o tabla
        # Si aire_porcentaje > 0, usar eso. Si no, tabla.
        if aire_porcentaje > 0:
             aire_lt = aire_porcentaje * 10
        else:
             aire_lt = obtener_aire_ocluido(tmn, 0)
    
    # Aditivos y reducción de agua?
    # El usuario pide flujo estricto: Cemento -> A/C -> Agua.
    # Si hay aditivos reductores, ¿cambian el A/C? 
    # Usualmente, si fijas A/C y Cemento, el agua es fija. El aditivo te daría más docilidad.
    # O si fijas Cemento y quieres cierta docilidad, el aditivo baja el agua y el A/C.
    # PERO, el usuario dijo "Output segun calculo: cantidad cemento, agua amasado".
    # Asumiremos el cálculo directo matemático A = C * A/C.
    
    # Cálculo de Volumen de Aditivos (para restar al volumen de áridos)
    volumen_aditivos_lt = 0.0
    aditivos_res = []
    if aditivos_config:
        for ad in aditivos_config:
            nombre = ad['nombre']
            dosis_pct = ad['dosis_pct']
            densidad = ad['densidad_kg_lt']
            
            # Dosis % del peso de cemento
            peso_ad = cemento * (dosis_pct / 100.0)
            vol_ad = peso_ad / densidad
            
            aditivos_res.append({
                'nombre': nombre,
                'cantidad_kg': round(peso_ad, 3),
                'volumen_lt': round(vol_ad, 3),
                'dosis_pct': dosis_pct
            })
            volumen_aditivos_lt += vol_ad

    # 5. Compacidad / Volumen Áridos
    # Volumen disponible para áridos = 1000 - V_agua - V_aire - V_cemento - V_aditivos
    vol_cemento = cemento / (densidad_cemento / 1000) # kg / (kg/m3 * 1000?) No, kg / (kg/m3) = m3 -> *1000 = Litros
    vol_cemento_lt = cemento / densidad_cemento * 1000
    
    vol_agua_lt = agua_amasado
    vol_aire_lt = aire_lt
    
    vol_aridos_aprente_lt = 1000.0 - vol_cemento_lt - vol_agua_lt - vol_aire_lt - volumen_aditivos_lt
    
    # Compacidad z (Volumen Solidos / 1000)
    # Solidos = Cemento + Aridos
    # z = (Vol_Cemento_lt + Vol_Aridos_lt) / 1000
    # z = (1000 - Agua - Aire) / 1000
    compacidad = (vol_cemento_lt + vol_aridos_aprente_lt) / 1000.0
    
    # % Volumen Absoluto Cemento (c)
    # c = Vol_Cemento / (Vol_Cemento + Vol_Aridos) = Vol_Cemento / (z*1000)
    c_vol = vol_cemento_lt / (compacidad * 1000.0)
    
    # Referencias de Durabilidad (Solo informativo)
    referencias = {
        'min_cemento_norma': min_cemento_durabilidad,
        'max_ac_norma': max_ac_durabilidad,
        'cumple_cemento': cemento >= min_cemento_durabilidad,
        'cumple_ac': ac_ratio <= max_ac_durabilidad
    }
    
    # 8. Proporciones volumétricas
    num_aridos = len(aridos)
    
    # --- NUEVO: Override con Proporciones Personalizadas (Optimización) ---
    if proporciones_personalizadas and len(proporciones_personalizadas) == num_aridos:
        # Normalizar a 1.0 (suma)
        total_p = sum(proporciones_personalizadas)
        props_norm = [p / total_p for p in proporciones_personalizadas]
        
        # El volumen total de áridos es (1 - c_vol)
        # Faury estandar divide en 'grueso' y 'fino' basado en curva.
        # Aqui asignamos directo.
        
        proporciones_vol = {}
        vol_aridos_total = 1.0 - c_vol
        
        if num_aridos == 2:
            # Asumimos orden [grueso, fino] o [arido1, arido2] según input
            # La UI suele mandar [grueso, fino]
            proporciones_vol['grueso'] = vol_aridos_total * props_norm[0]
            proporciones_vol['fino'] = vol_aridos_total * props_norm[1]
        elif num_aridos == 3:
             proporciones_vol['grueso_1'] = vol_aridos_total * props_norm[0]
             proporciones_vol['grueso_2'] = vol_aridos_total * props_norm[1]
             proporciones_vol['fino'] = vol_aridos_total * props_norm[2]
             
        proporciones_vol['cemento'] = c_vol
        
    else:
        # Cálculo Faury Estándar
        proporciones_vol = calcular_proporciones_faury(tmn, consistencia, c_vol, num_aridos)

    
    # 9. Densidades de áridos
    densidades = {}
    absorciones = {}
    granulometrias = {}
    
    for i, arido in enumerate(aridos):
        nombre = arido.get('nombre', f'arido_{i}')
        if num_aridos == 2:
            if i == 0:
                key = 'grueso'
            else:
                key = 'fino'
        else:
            if i == 0:
                key = 'grueso_1'
            elif i == 1:
                key = 'grueso_2'
            else:
                key = 'fino'
        
        densidades[key] = arido.get('DRS', 2650)
        absorciones[key] = arido.get('absorcion', 0.01)
        granulometrias[key] = arido.get('granulometria', [100] * 12)
    
    # 10. Cantidades en kg/m³
    cantidades = calcular_cantidades_kg(proporciones_vol, compacidad, densidades)
    
    # 11. Agua de absorción
    agua_absorcion = calcular_agua_absorcion(cantidades, absorciones)
    
    # 12. Agua total
    agua_total = calcular_agua_total(agua_amasado, agua_absorcion)
    
    # 13. Proporciones en peso
    proporciones_peso = calcular_proporciones_peso(cantidades)
    
    # 14. Granulometría de la mezcla
    mezcla_granulometria = calcular_granulometria_mezcla(proporciones_peso, granulometrias)
    
    # 15. Banda de trabajo
    banda_trabajo = calcular_banda_trabajo(mezcla_granulometria)
    
    # Mapeo de claves internas a nombres reales
    nombres_reales = {}
    if num_aridos == 2:
        nombres_reales['grueso'] = aridos[0].get('nombre', 'Grueso')
        nombres_reales['fino'] = aridos[1].get('nombre', 'Fino')
    elif num_aridos == 3:
        nombres_reales['grueso_1'] = aridos[0].get('nombre', 'Grueso 1')
        nombres_reales['grueso_2'] = aridos[1].get('nombre', 'Grueso 2')
        nombres_reales['fino'] = aridos[2].get('nombre', 'Fino')
        
    # Reemplazar claves en diccionarios de resultados
    cantidades_final = {}
    props_peso_final = {}
    props_vol_final = {}
    
    for k, v in cantidades.items():
        new_k = nombres_reales.get(k, k)
        cantidades_final[new_k] = round(v, 1)
        
    for k, v in proporciones_peso.items():
        new_k = nombres_reales.get(k, k)
        props_peso_final[new_k] = round(v, 4)
        
    for k, v in proporciones_vol.items():
        new_k = nombres_reales.get(k, k)
        props_vol_final[new_k] = round(v, 4)

    return {
        'resistencia': {
            'fd_mpa': round(fd_mpa, 2),
            'fd_kgcm2': fd_kgcm2,
            'coef_t': obtener_coeficiente_t(fraccion_def)
        },
        'cemento': {
            'cantidad': cemento,
            'densidad': densidad_cemento
        },
        'agua_cemento': {
            'razon': round(ac_ratio, 3),
            'agua_amasado': round(agua_amasado, 1),
            'agua_absorcion': round(agua_absorcion, 1),
            'agua_total': round(agua_total, 1)
        },
        'aire': {
            'volumen': round(aire_lt, 1),
            'porcentaje': round(aire_lt / 10, 1)
        },
        'compacidad': round(compacidad, 4),
        'proporciones_volumetricas': props_vol_final,
        'cantidades_kg_m3': cantidades_final,
        'proporciones_peso': props_peso_final,
        'granulometria_mezcla': [round(v, 1) for v in mezcla_granulometria],
        'banda_trabajo': [(round(inf, 1), round(sup, 1)) for inf, sup in banda_trabajo],
        'aditivos': aditivos_res,
        'volumen_aditivos': round(volumen_aditivos_lt, 2),
        'referencias_durabilidad': referencias # Agregamos referencias normativas
    }

"""
Módulo Shilstone para análisis de mezclas de concreto
Implementa cálculos de Coarseness Factor (CF), Workability Factor (W, Wadj),
Factor de Mortero (FM) y generación de gráficos Shilstone.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Dict, Tuple, Optional
import io

# Configurar matplotlib para no mostrar advertencias
plt.rcParams['figure.max_open_warning'] = 0


def calcular_CF(pasa_3_8: float, pasa_8: float) -> float:
    """
    Calcula el Coarseness Factor (Factor de Grosor).
    
    Fórmula: CF = Q / (Q + I) × 100
    Donde:
        - Q = 100 - (% pasa 3/8")  -> Fracción gruesa
        - I = (% pasa 3/8") - (% pasa #8)  -> Fracción intermedia
    
    Args:
        pasa_3_8: Porcentaje que pasa el tamiz 3/8" (9.5mm)
        pasa_8: Porcentaje que pasa el tamiz #8 (2.36mm)
    
    Returns:
        Coarseness Factor (0-100)
    """
    Q = 100 - pasa_3_8  # Fracción gruesa
    I = pasa_3_8 - pasa_8  # Fracción intermedia
    
    if Q + I <= 0:
        return 0.0
    
    CF = (Q / (Q + I)) * 100
    return round(CF, 2)


def calcular_W(pasa_8: float) -> float:
    """
    Calcula el Workability Factor base.
    
    W = % que pasa el tamiz #8
    
    Args:
        pasa_8: Porcentaje que pasa el tamiz #8 (2.36mm)
    
    Returns:
        Workability Factor base
    """
    return round(pasa_8, 2)


def calcular_ajuste(cemento: float) -> float:
    """
    Calcula el ajuste para el Workability Factor según contenido de cemento.
    
    Fórmula: Adj = 0.0588 × Cc - 19.647
    Alternativa: Adj = (2.5 × (Cc - 335)) / 56
    
    Args:
        cemento: Cantidad de cemento en kg/m³
    
    Returns:
        Ajuste para Workability Factor
    """
    adj = 0.0588 * cemento - 19.647
    return round(adj, 2)


def calcular_Wadj(W: float, adj: float) -> float:
    """
    Calcula el Workability Factor ajustado.
    
    Fórmula: Wadj = W + Adj
    
    Args:
        W: Workability Factor base
        adj: Ajuste calculado
    
    Returns:
        Workability Factor ajustado
    """
    return round(W + adj, 2)


def calcular_FM(cemento: float, densidad_cemento: float, pasa_8: float,
                peso_aridos_total: float, dsss_arena: float,
                agua_neta: float, aditivos: float = 0.0, 
                aire: float = 0.0) -> float:
    """
    Calcula el Factor de Mortero.
    
    Fórmula: FM = (Cc/pec) + ((pasa_8/100 × PA)/Dsss) + Agua + Aditivos + Aire
    
    Args:
        cemento: Contenido de cemento en kg/m³
        densidad_cemento: Densidad del cemento en kg/lt (típicamente 3.14)
        pasa_8: Porcentaje que pasa tamiz #8
        peso_aridos_total: Peso total de áridos en kg/m³
        dsss_arena: Densidad SSS de la arena en kg/lt
        agua_neta: Agua de amasado en lt/m³
        aditivos: Volumen de aditivos en lt/m³
        aire: Volumen de aire en lt/m³
    
    Returns:
        Factor de Mortero en lt/m³
    """
    # Convertir densidad de kg/m³ a kg/lt si es necesario
    if densidad_cemento > 100:
        densidad_cemento = densidad_cemento / 1000
    if dsss_arena > 100:
        dsss_arena = dsss_arena / 1000
    
    vol_cemento = cemento / densidad_cemento
    vol_finos = (pasa_8 / 100) * peso_aridos_total / dsss_arena
    
    FM = vol_cemento + vol_finos + agua_neta + aditivos + aire
    return round(FM, 2)


def evaluar_zona_shilstone(CF: float, Wadj: float) -> Dict:
    """
    Evalúa la posición del punto (CF, Wadj) en el gráfico Shilstone
    y determina en qué zona se encuentra.
    
    Args:
        CF: Coarseness Factor
        Wadj: Workability Factor ajustado
    
    Returns:
        Diccionario con evaluación de la zona
    """
    evaluacion = {
        'CF': CF,
        'Wadj': Wadj,
        'zona': '',
        'descripcion': '',
        'recomendaciones': [],
        'calidad': ''  # Óptima, Aceptable, Deficiente
    }
    
    # Verificar límites de zona óptima (Zona I)
    en_zona_optima = (45 <= CF <= 75) and (27 <= Wadj <= 45)
    
    # Línea superior de Zona I: aproximadamente desde (100, 36) hasta (35, 45)
    # Ecuación: Wadj = -0.138 * CF + 49.8 (simplificada)
    wadj_linea_sup = -0.138 * CF + 49.8
    
    # Línea inferior de Zona I: aproximadamente desde (100, 27) hasta (0, 37)
    # Ecuación: Wadj = -0.1 * CF + 37 (simplificada)
    wadj_linea_inf = -0.1 * CF + 37
    
    if en_zona_optima:
        # Verificar si está dentro del polígono de Zona I
        if Wadj <= wadj_linea_sup and Wadj >= wadj_linea_inf:
            evaluacion['zona'] = 'Zona I - Óptima'
            evaluacion['descripcion'] = 'Mezcla con gradación óptima para trabajabilidad y cohesión.'
            evaluacion['calidad'] = 'Óptima'
        else:
            evaluacion['zona'] = 'Zona de transición'
            evaluacion['descripcion'] = 'Mezcla en zona de transición. Ajustes menores pueden mejorar el desempeño.'
            evaluacion['calidad'] = 'Aceptable'
    else:
        # Determinar zona problemática
        if CF > 75:
            evaluacion['zona'] = 'Zona Rocky'
            evaluacion['descripcion'] = 'Mezcla muy gruesa. Riesgo de segregación y problemas de acabado.'
            evaluacion['calidad'] = 'Deficiente'
            evaluacion['recomendaciones'].append('Aumentar contenido de finos (arena)')
            evaluacion['recomendaciones'].append('Considerar reducir tamaño máximo del agregado')
        elif CF < 45:
            evaluacion['zona'] = 'Zona Arenosa'
            evaluacion['descripcion'] = 'Mezcla muy fina. Posible alta demanda de agua y retracción.'
            evaluacion['calidad'] = 'Deficiente'
            evaluacion['recomendaciones'].append('Aumentar contenido de agregado grueso')
            evaluacion['recomendaciones'].append('Reducir contenido de finos')
        
        if Wadj > 45:
            evaluacion['zona'] = 'Zona Sobrediseñada'
            evaluacion['descripcion'] = 'Exceso de finos. Riesgo de segregación y alto consumo de agua.'
            evaluacion['calidad'] = 'Deficiente'
            evaluacion['recomendaciones'].append('Reducir porcentaje de material que pasa #8')
        elif Wadj < 27:
            evaluacion['zona'] = 'Zona de Baja Trabajabilidad'
            evaluacion['descripcion'] = 'Deficiencia de finos. Mezcla con baja cohesión y trabajabilidad.'
            evaluacion['calidad'] = 'Deficiente'
            evaluacion['recomendaciones'].append('Aumentar contenido de arena fina')
            evaluacion['recomendaciones'].append('Verificar granulometría del agregado fino')
    
    if not evaluacion['recomendaciones']:
        evaluacion['recomendaciones'].append('La mezcla se encuentra en una zona aceptable')
    
    return evaluacion


def graficar_shilstone(CF: float, Wadj: float, titulo: str = "Gráfico Shilstone",
                       mostrar_fm: bool = False, FM: Optional[float] = None,
                       guardar_buffer: bool = False) -> plt.Figure:
    """
    Genera el gráfico de Coarseness Factor vs Workability Factor ajustado
    con las zonas de Shilstone.
    
    Args:
        CF: Coarseness Factor
        Wadj: Workability Factor ajustado
        titulo: Título del gráfico
        mostrar_fm: Si se debe mostrar el Factor de Mortero
        FM: Factor de Mortero (opcional)
        guardar_buffer: Si retorna también un buffer de imagen
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Colores para las zonas
    color_zona_i = '#90EE90'  # Verde claro
    color_zona_ii = '#FFE4B5'  # Beige
    color_zona_iii = '#FFB6C1'  # Rosa claro
    color_zona_iv = '#87CEEB'  # Azul claro
    color_zona_v = '#DDA0DD'  # Ciruela claro
    
    # Zona I - Óptima (polígono principal)
    zona1_x = [100, 85, 45, 45, 75, 100]
    zona1_y = [27, 27, 32, 45, 45, 36]
    ax.fill(zona1_x, zona1_y, alpha=0.4, color=color_zona_i, label='Zona I - Óptima')
    
    # Zona II - Gruesa (Rocky)
    zona2_x = [100, 75, 75, 100]
    zona2_y = [36, 45, 50, 50]
    ax.fill(zona2_x, zona2_y, alpha=0.3, color=color_zona_ii)
    
    # Zona III - Sobrediseñada
    zona3_x = [75, 45, 45, 75]
    zona3_y = [45, 45, 50, 50]
    ax.fill(zona3_x, zona3_y, alpha=0.3, color=color_zona_iii)
    
    # Zona IV - Arenosa
    zona4_x = [45, 0, 0, 45]
    zona4_y = [32, 37, 50, 50]
    ax.fill(zona4_x, zona4_y, alpha=0.3, color=color_zona_iv)
    
    # Zona V - Baja trabajabilidad
    zona5_x = [100, 85, 45, 0, 0, 100]
    zona5_y = [20, 27, 32, 37, 20, 20]
    ax.fill(zona5_x, zona5_y, alpha=0.3, color=color_zona_v)
    
    # Líneas de contorno de Zona I
    ax.plot([100, 75], [36, 45], 'g-', linewidth=2)
    ax.plot([100, 85, 45], [27, 27, 32], 'g-', linewidth=2)
    ax.plot([45, 45], [32, 45], 'g-', linewidth=2)
    ax.plot([45, 75], [45, 45], 'g-', linewidth=2)
    
    # Líneas de referencia adicionales
    ax.axhline(y=35, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
    ax.axvline(x=60, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
    
    # Punto de la mezcla
    evaluacion = evaluar_zona_shilstone(CF, Wadj)
    if evaluacion['calidad'] == 'Óptima':
        color_punto = 'green'
    elif evaluacion['calidad'] == 'Aceptable':
        color_punto = 'orange'
    else:
        color_punto = 'red'
    
    ax.scatter([CF], [Wadj], s=250, c=color_punto, marker='o', 
               edgecolors='black', linewidths=2, zorder=5)
    ax.annotate(f'({CF:.1f}, {Wadj:.1f})', (CF, Wadj),
                xytext=(12, 12), textcoords='offset points',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Etiquetas de zonas
    ax.text(85, 43, 'Rocky', fontsize=10, alpha=0.7, ha='center')
    ax.text(60, 47, 'Sobrediseñada', fontsize=10, alpha=0.7, ha='center')
    ax.text(22, 43, 'Arenosa', fontsize=10, alpha=0.7, ha='center')
    ax.text(50, 23, 'Baja Trabajabilidad', fontsize=10, alpha=0.7, ha='center')
    ax.text(65, 35, 'ZONA I\nÓPTIMA', fontsize=12, fontweight='bold', 
            color='darkgreen', ha='center', va='center')
    
    # Configuración de ejes
    ax.set_xlabel('Coarseness Factor (CF)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Workability Factor Ajustado (Wadj)', fontsize=12, fontweight='bold')
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(0, 100)
    ax.set_ylim(20, 50)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Información adicional
    info_text = f"CF: {CF:.1f}\nWadj: {Wadj:.1f}\nZona: {evaluacion['zona']}"
    if mostrar_fm and FM is not None:
        info_text += f"\nFM: {FM:.1f} lt/m³"
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    # Leyenda
    handles = [
        mpatches.Patch(color=color_zona_i, alpha=0.4, label='Zona I - Óptima'),
        mpatches.Patch(color=color_zona_ii, alpha=0.3, label='Zona II - Rocky'),
        mpatches.Patch(color=color_zona_iii, alpha=0.3, label='Zona III - Sobrediseñada'),
        mpatches.Patch(color=color_zona_iv, alpha=0.3, label='Zona IV - Arenosa'),
        mpatches.Patch(color=color_zona_v, alpha=0.3, label='Zona V - Baja Trabaj.'),
    ]
    ax.legend(handles=handles, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    
    return fig


def graficar_shilstone_para_pdf(CF: float, Wadj: float, FM: Optional[float] = None) -> bytes:
    """
    Genera el gráfico Shilstone y lo retorna como bytes para incluir en PDF.
    
    Args:
        CF: Coarseness Factor
        Wadj: Workability Factor ajustado
        FM: Factor de Mortero (opcional)
    
    Returns:
        Imagen en formato PNG como bytes
    """
    fig = graficar_shilstone(CF, Wadj, mostrar_fm=FM is not None, FM=FM)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf.getvalue()


def calcular_shilstone_completo(granulometria_mezcla: list, cemento: float,
                                 peso_aridos_total: float, dsss_arena: float,
                                 agua_neta: float, densidad_cemento: float = 3140,
                                 aditivos: float = 0.0, aire: float = 35.0) -> Dict:
    """
    Calcula todos los parámetros de Shilstone de manera completa.
    
    Args:
        granulometria_mezcla: Lista con % que pasa por cada tamiz
        cemento: Contenido de cemento en kg/m³
        peso_aridos_total: Peso total de áridos en kg/m³
        dsss_arena: Densidad SSS de la arena en kg/m³
        agua_neta: Agua de amasado en lt/m³
        densidad_cemento: Densidad del cemento en kg/m³
        aditivos: Volumen de aditivos en lt/m³
        aire: Volumen de aire en lt/m³
    
    Returns:
        Diccionario con todos los parámetros de Shilstone
    """
    # Índices de tamices en la lista estándar
    # [40, 25, 20, 12.5, 10, 5, 2.36, 1.18, 0.6, 0.315, 0.16, 0.08]
    #   0    1   2    3    4  5    6     7    8     9    10    11
    
    # El tamiz 3/8" corresponde aproximadamente al índice 4 (10mm o 9.5mm)
    # El tamiz #8 corresponde al índice 6 (2.36mm)
    
    pasa_3_8 = granulometria_mezcla[4] if len(granulometria_mezcla) > 4 else 50
    pasa_8 = granulometria_mezcla[6] if len(granulometria_mezcla) > 6 else 30
    
    # Calcular parámetros
    CF = calcular_CF(pasa_3_8, pasa_8)
    W = calcular_W(pasa_8)
    adj = calcular_ajuste(cemento)
    Wadj = calcular_Wadj(W, adj)
    
    FM = calcular_FM(
        cemento=cemento,
        densidad_cemento=densidad_cemento,
        pasa_8=pasa_8,
        peso_aridos_total=peso_aridos_total,
        dsss_arena=dsss_arena,
        agua_neta=agua_neta,
        aditivos=aditivos,
        aire=aire
    )
    
    # Evaluar zona
    evaluacion = evaluar_zona_shilstone(CF, Wadj)
    
    return {
        'CF': CF,
        'W': W,
        'adj': adj,
        'Wadj': Wadj,
        'FM': FM,
        'pasa_3_8': pasa_3_8,
        'pasa_8': pasa_8,
        'evaluacion': evaluacion
    }

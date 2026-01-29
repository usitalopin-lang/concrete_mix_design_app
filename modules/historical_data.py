
import pandas as pd
import streamlit as st
import numpy as np
from streamlit_gsheets import GSheetsConnection
from modules.catalogs import limpiar_decimales

# Nombres de hojas (Deben coincidir con tu Google Sheet)
SHEET_DOSIFICACIONES = "Dosificaciones"
SHEET_RESISTENCIA = "Resistencia"
SHEET_CEMENTOS = "Cat_Cementos" # Ojo: validar nombre real si es distinto al catalogo
SHEET_ARIDOS = "Cat_Aridos"     # Ojo: validar nombre real si es distinto al catalogo

# Mapeo de columnas para normalizar (Header Excel -> Header Interno)
MAP_DOSIFICACIONES = {
    'Código': 'codigo',
    'Grado': 'grado',
    'Res.': 'resistencia',
    'FD': 'fraccion_defectuosa',
    'TMN': 'tmn',
    'Doc.': 'docilidad',
    'Cemento': 'cemento_kg',
    'Agua': 'agua_lt',
    'Ch. 1 1/2"': 'grava_40mm',
    'Chanc. 1': 'grava_25mm',
    'Rod 1': 'rodado_25mm',
    'Rod. 3/4': 'rodado_20mm',
    'Chanc. 3/8': 'gravilla_10mm',
    'Ar. Norm.': 'arena_norm',
    'Ch. 1/2"': 'gravilla_12mm',
    'Chanc. 3/4"': 'grava_20mm'
}

MAP_RESISTENCIA = {
    'N° Muestra': 'n_muestra',
    'Grado': 'grado',
    'FD': 'fraccion_defectuosa',
    'TMN': 'tmn',
    'Docilidad': 'docilidad',
    'Fecha Confección': 'fecha_confeccion',
    'Fecha de ensayo ': 'fecha_ensayo',
    'Fecha de ensayo': 'fecha_ensayo',
    'Fecha Ensayo': 'fecha_ensayo',
    'Res. Cil. (MPa)': 'resistencia_mpa',
    'Resistencia': 'resistencia_mpa',
    'Resistencia (MPa)': 'resistencia_mpa',
    'f\'c': 'resistencia_mpa',
    'Densidad C. (kg/m3)': 'densidad_kgm3',
    'Densidad': 'densidad_kgm3',
    'Edad': 'edad_dias', 
    'Edades': 'edad_dias'
}

MAP_CEMENTOS = {
    'N°': 'n_muestra',
    'Fecha de Muestreo': 'fecha_muestreo',
    'Peso especifico (Densidad T/m3)': 'densidad_t_m3',
    'Agua de const. Normal': 'agua_normal_pct',
    'Superficie especifica (Blaine cm²/g)': 'blaine',
    'Tiempo Fraguado Inicial': 'fraguado_inicial',
    'Tiempo Fraguado Final': 'fraguado_final',
    'Compresion 7D': 'compresion_7d',
    'Compresion 28D': 'compresion_28d',
    'Pérdida por calcinación %': 'perdida_calcinacion',
    'Informe': 'informe'
}

MAP_ARIDOS = {
    'N° Muestra': 'n_muestra',
    'Fecha Muestreo': 'fecha_muestreo',
    'Tipo de Material': 'tipo_material',
    'Procedencia Extracción': 'procedencia',
    'Identificación de Planta': 'planta',
    'Densidad Real Seca-DRS (Kg/m3)': 'drs',
    'Densidad Real SSS-DRSS (Kg/m3)': 'drsss',
    'Absorción de Agua (%)': 'absorcion',
    'Módulo Finura': 'modulo_finura',
    'Material Fino Menor que 0,08 mm %': 'finos_p200',
    # Tamices (Mapeo a nombres cortos)
    '1 1/2" (40mm)': 't_40mm',
    '1" (25mm)': 't_25mm',
    '3/4" (20mm)': 't_20mm',
    '1/2" (12.5mm)': 't_12mm',
    '3/8" (10mm)': 't_10mm',
    'N°4 (5mm)': 't_5mm',
    'N°8 (2.5mm)': 't_2_5mm',
    'N°16 (1.25mm)': 't_1_25mm',
    'N°30 (0.630mm)': 't_0_63mm',
    'N°50 (0.315mm)': 't_0_315mm',
    'N°100 (0.160mm)': 't_0_16mm'
}

def obtener_conexion():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_dosificaciones():
    """Carga y limpia la planilla de Dosificaciones."""
    try:
        conn = obtener_conexion()
        # Usamos usecols o simplemente leemos todo y filtramos
        df = conn.read(worksheet=SHEET_DOSIFICACIONES, ttl=0)
        
        # 1. Renombrar columnas
        df.rename(columns=MAP_DOSIFICACIONES, inplace=True)
        
        # 2. Convertir columnas numéricas (comma decimal)
        # Identificar columnas que deberían ser numéricas
        cols_num = ['cemento_kg', 'agua_lt', 'tmn'] + [v for k,v in MAP_DOSIFICACIONES.items() if 'grava' in v or 'arena' in v or 'rodado' in v]
        df = limpiar_decimales(df, cols_num)
        
        # 3. Limpieza de strings clave
        for col in ['grado', 'docilidad', 'codigo']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                
        return df
    except Exception as e:
        st.error(f"Error cargando Dosificaciones: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def cargar_resistencias():
    """Carga y limpia la planilla de Resistencias."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_RESISTENCIA, ttl=0)
        
        # 1. Renombrar
        df.rename(columns=MAP_RESISTENCIA, inplace=True)
        
        # 2. Limpieza numéricos
        cols_num = ['resistencia_mpa', 'densidad_kgm3', 'tmn']
        df = limpiar_decimales(df, cols_num)
        
        # 3. Fechas
        for col_fecha in ['fecha_confeccion', 'fecha_ensayo']:
            if col_fecha in df.columns:
                df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
                
        # 4. Limpieza strings clave
        for col in ['grado', 'docilidad']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                
        return df
    except Exception as e:
        st.error(f"Error cargando Resistencias: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def cargar_cementos_historico():
    """Carga y limpia la planilla de Cementos (Historial)."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_CEMENTOS, ttl=0)
        
        # 1. Renombrar
        df.rename(columns=MAP_CEMENTOS, inplace=True)
        
        # 2. Limpieza numéricos
        # Detectar columnas que mapeamos a algo numerico
        cols_num = ['densidad_t_m3', 'compresion_7d', 'compresion_28d', 
                   'blaine', 'agua_normal_pct', 'perdida_calcinacion']
         # (Asegurarnos que existen antes de limpiar)
        cols_limpiar = [c for c in cols_num if c in df.columns]
        df = limpiar_decimales(df, cols_limpiar)
        
        # 3. Fechas
        if 'fecha_muestreo' in df.columns:
            df['fecha_muestreo'] = pd.to_datetime(df['fecha_muestreo'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Error cargando Cementos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def cargar_aridos_historico():
    """Carga y limpia la planilla de Áridos (Historial)."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_ARIDOS, ttl=0)
        
        # 1. Renombrar
        df.rename(columns=MAP_ARIDOS, inplace=True)
        
        # 2. Limpieza numéricos
        cols_num = ['drs', 'drsss', 'absorcion', 'finos_p200', 'modulo_finura']
        # Agregar los tamices
        tamices = [v for k,v in MAP_ARIDOS.items() if k.startswith('1') or k.startswith('3') or 'mm' in k]
        cols_num.extend(tamices)
        
        cols_limpiar = [c for c in cols_num if c in df.columns]
        df = limpiar_decimales(df, cols_limpiar)
        
        # 3. Fechas
        if 'fecha_muestreo' in df.columns:
            df['fecha_muestreo'] = pd.to_datetime(df['fecha_muestreo'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Error cargando Áridos: {e}")
        return pd.DataFrame()

def unir_dosificacion_resistencia(df_dos, df_res, filtro_edad=None, fecha_inicio=None, fecha_fin=None):
    """
    Une Dosificaciones con su Historial de Resistencia.
    Estrategia de Cruce: Class Matching (Grado + TMN + Docilidad)
    
    Args:
        filtro_edad (list): Lista de edades (días) a considerar.
        fecha_inicio (date): Fecha inicial para filtrar ensayos.
        fecha_fin (date): Fecha final para filtrar ensayos.
    """
    if df_dos.empty or df_res.empty:
        return pd.DataFrame()
        
    # --- FILTRADO PREVIO (EDAD Y PERIODO) ---
    # Filtrar df_res antes de agrupar para que los promedios reflejen la selección
    
    # 1. Filtro de Edad
    if filtro_edad:
        # Aseguramos que edad_dias sea numérico para comparar
        if 'edad_dias' in df_res.columns:
            # Convertir a numeric, ignorar errores
            s_edad = pd.to_numeric(df_res['edad_dias'], errors='coerce')
            # Filtrar
            # Convertir filtro_edad a int por si vienen strings
            edades_validas = [int(e) for e in filtro_edad]
            df_res = df_res[s_edad.isin(edades_validas)]
            
    # 2. Filtro de Fechas (Periodo)
    if fecha_inicio and fecha_fin:
        if 'fecha_ensayo' in df_res.columns:
            df_res['fecha_ensayo'] = pd.to_datetime(df_res['fecha_ensayo'], errors='coerce')
            # Filtrar rango
            mask_fecha = (df_res['fecha_ensayo'].dt.date >= fecha_inicio) & \
                         (df_res['fecha_ensayo'].dt.date <= fecha_fin)
            df_res = df_res[mask_fecha]
            
    if df_res.empty:
         # Si el filtro dejó vacío el historial, retornamos las recetas solas (sin stats)
         # Ojo: si retornamos df_dos directo, no tendrá las columnas de stats y podría romper algo.
         # Mejor dejar que siga el flujo y stats saldrán NaN.
         pass

    
    # Crear claves de cruce
    # En este caso, queremos ver para cada RECETA (row de df_dos),
    # qué desempeño ha tenido históricamente esa CLASE de hormigón.
    
    # No es un Join fila a fila (porque una receta se usa muchas veces),
    # es más bien una agregación.
    
    # --- CORRECCIÓN DE CRUCE ---
    # Normalizamos ambas tablas para tener 'grado_join' = Letra + Numero (ej. G30)
    
    # 1. Preparar Dosificaciones
    # Limpiamos parte numérica de resistencia (ej 30.0 -> 30)
    res_str_dos = df_dos['resistencia'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    # Si el grado ya contiene el número (ej G30), lo dejamos. Si es solo G, concatenamos.
    # Heurística: Si grado termina en dígito, ya está listo.
    df_dos['grado_join'] = df_dos.apply(
        lambda x: str(x['grado']).strip().upper() if str(x['grado']).strip()[-1].isdigit() 
        else str(x['grado']).strip().upper() + str(x['resistencia']).replace('.0','').strip(), 
        axis=1
    )

    # 2. Preparar Resistencias
    # Misma lógica: Si Grado es 'G' y existe 'resistencia_mpa', concatenamos?
    # Usualmente en Historial de Resistencias, la columna 'Grado' suele ser el código completo 'G30'.
    # Pero por seguridad, aplicamos limpieza.
    df_res['grado_join'] = df_res['grado'].astype(str).str.strip().str.upper()
    
    # Normalización general
    for col in ['grado_join', 'docilidad']:
        if col in df_res.columns:
            df_res[col] = df_res[col].astype(str).str.strip().str.upper()
        if col in df_dos.columns:
            df_dos[col] = df_dos[col].astype(str).str.strip().str.upper()

    # Clave: GRADO_JOIN + FD + TMN + DOCILIDAD
    # Nota: FD y TMN son numéricos/float, los convertimos a string eliminando .0 si son enteros
    
    def clean_num(serie):
        return serie.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    df_res['clave_mix'] = (
        df_res['grado_join'] + "_" + 
        clean_num(df_res['fraccion_defectuosa']) + "_" + 
        clean_num(df_res['tmn']) + "_" + 
        clean_num(df_res['docilidad'])  # Clean docilidad also
    )
    
    # Clave en Dosificaciones
    df_dos['clave_mix'] = (
        df_dos['grado_join'] + "_" + 
        clean_num(df_dos['fraccion_defectuosa']) + "_" + 
        clean_num(df_dos['tmn']) + "_" + 
        clean_num(df_dos['docilidad'])  # Clean docilidad also
    )
    
    
    # Asegurar que resistencia_mpa sea numérica antes de agregar
    df_res['resistencia_mpa'] = pd.to_numeric(df_res['resistencia_mpa'], errors='coerce')
    
    # Asegurar que fecha_ensayo sea datetime
    df_res['fecha_ensayo'] = pd.to_datetime(df_res['fecha_ensayo'], errors='coerce')
    
    # Calculamos estadísticas por Clave (solo si hay datos válidos)
    stats = df_res.groupby('clave_mix').agg(
        n_muestras=('resistencia_mpa', 'count'),
        promedio_fc=('resistencia_mpa', lambda x: x.mean() if x.notna().any() else np.nan),
        desviacion_std=('resistencia_mpa', lambda x: x.std() if x.notna().any() else np.nan),
        ultimo_ensayo=('fecha_ensayo', lambda x: x.max() if x.notna().any() else pd.NaT)
    ).reset_index()
    
    # Unimos
    df_final = pd.merge(df_dos, stats, on='clave_mix', how='left')
    
    return df_final

def obtener_arido_promedio(tipo_material, fecha_desde, fecha_hasta):
    """
    Retorna las propiedades promedio de un árido en un período específico.
    
    Args:
        tipo_material: Nombre del tipo de árido (ej: "Rodado 1", "Arena Normal")
        fecha_desde: Fecha inicio del rango
        fecha_hasta: Fecha fin del rango
    
    Returns:
        dict con propiedades promediadas o None si no hay datos
    """
    df = cargar_aridos_historico()
    
    if df.empty:
        return None
    
    # Filtrar por tipo y rango de fechas
    mask = (df['tipo_material'].str.upper().str.contains(tipo_material.upper(), na=False)) & \
           (df['fecha_muestreo'] >= fecha_desde) & \
           (df['fecha_muestreo'] <= fecha_hasta)
    
    df_filtrado = df[mask]
    
    if df_filtrado.empty:
        return None
    
    # Lista de tamices en orden ASTM (12 tamices estándar)
    tamices_cols = ['t_40mm', 't_25mm', 't_20mm', 't_12mm', 't_10mm', 
                    't_5mm', 't_2_5mm', 't_1_25mm', 't_0_63mm', 
                    't_0_315mm', 't_0_16mm', 't_0_08mm']
    
    # --- FILTRADO ESTRICTO DE DATOS INVALIDOS (NAN / TEXTO) ---
    
    # 1. Convertir columnas críticas a numérico (Coerce errors to NaN)
    cols_claves_fisicas = ['drs', 'drsss', 'absorcion']
    for col in cols_claves_fisicas:
        if col in df_filtrado.columns:
            df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')

    # Convertir columnas de tamices a numérico
    tamices_presentes = []
    for tamiz in tamices_cols:
        if tamiz in df_filtrado.columns:
            df_filtrado[tamiz] = pd.to_numeric(df_filtrado[tamiz], errors='coerce')
            tamices_presentes.append(tamiz)
            
    # 2. Eliminar filas que tengan CUALQUIER dato faltante en las columnas claves
    # (Granulometría + Densidades + Absorción)
    cols_obligatorias = [c for c in cols_claves_fisicas if c in df_filtrado.columns] + tamices_presentes
    
    if cols_obligatorias:
        df_filtrado.dropna(subset=cols_obligatorias, inplace=True)
        
    if df_filtrado.empty:
        return None

    # --- CALCULO DE PROMEDIOS CON DATA LIMPIA ---
    
    # Calcular granulometría promedio (solo tamices que existan)
    gran_prom = []
    for tamiz in tamices_cols:
        if tamiz in df_filtrado.columns:
            gran_prom.append(df_filtrado[tamiz].mean())
        else:
            gran_prom.append(100.0)  # Default si no existe
    
    # Calcular promedios
    resultado = {
        'nombre': tipo_material,
        'tipo': 'Grueso' if 'CHANC' in tipo_material.upper() or 'ROD' in tipo_material.upper() else 'Fino',
        'DRS': df_filtrado['drs'].mean() if 'drs' in df_filtrado.columns else 2650.0,
        'DRSSS': df_filtrado['drsss'].mean() if 'drsss' in df_filtrado.columns else 2700.0,
        'absorcion': df_filtrado['absorcion'].mean() / 100.0 if 'absorcion' in df_filtrado.columns else 0.01,
        'granulometria': gran_prom,
        'n_muestras': len(df_filtrado),
        'fecha_ultimo': df_filtrado['fecha_muestreo'].max(),
        'fecha_primero': df_filtrado['fecha_muestreo'].min(),
        'muestras_detalle': df_filtrado[['n_muestra', 'fecha_muestreo', 'drs', 'absorcion']].to_dict('records') if len(df_filtrado) <= 50 else []
    }
    
    # Corrección porcentaje absorción si la media > 1 (ej. 1.5% vs 0.015)
    # Por si en la planilla excel esta como entero (1.5) y no decimal (0.015)
    # Asumimos que si es > 1, es porcentaje entero.
    if resultado['absorcion'] > 1.0:
        resultado['absorcion'] = resultado['absorcion'] / 100.0
        
    # Nota: En la línea de arriba ya dividimos por 100.0 (linea 339 del snippet), 
    # pero a veces la gente pone 0.015 en excel y a veces 1.5.
    # Si viene como 1.5 -> numeric -> 1.5 -> /100 -> 0.015 (Correcto)
    # Si viene como 0.015 -> numeric -> 0.015 -> /100 -> 0.00015 (Muy bajo)
    # Vamos a refinar esa lógica de absorción para ser robustos.
    
    val_abs_raw = df_filtrado['absorcion'].mean() if 'absorcion' in df_filtrado.columns else 1.0
    # Heurística: Si es > 0.1 (10%), probablemente es un error o está en porcentaje (ej 1.5)
    # Una absorción real de árido > 10% es rara (ligeros). Lo normal es 0.5% - 3%.
    # Si el valor raw es > 1.0, asumimos porcentaje entero y dividimos por 100.
    if val_abs_raw > 1.0:
        resultado['absorcion'] = val_abs_raw / 100.0
    else:
        resultado['absorcion'] = val_abs_raw # Asumimos que ya viene decimal (ej 0.015)

    return resultado

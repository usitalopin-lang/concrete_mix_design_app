
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
    'Fecha de ensayo ': 'fecha_ensayo', # Ojo con el espacio al final
    'Fecha de ensayo': 'fecha_ensayo',
    'Res. Cil. (MPa)': 'resistencia_mpa',
    'Densidad C. (kg/m3)': 'densidad_kgm3',
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

def unir_dosificacion_resistencia(df_dos, df_res):
    """
    Une Dosificaciones con su Historial de Resistencia.
    Estrategia de Cruce: Class Matching (Grado + TMN + Docilidad)
    """
    if df_dos.empty or df_res.empty:
        return pd.DataFrame()
    
    # Crear claves de cruce
    # En este caso, queremos ver para cada RECETA (row de df_dos),
    # qué desempeño ha tenido históricamente esa CLASE de hormigón.
    
    # No es un Join fila a fila (porque una receta se usa muchas veces),
    # es más bien una agregación.
    
    # --- CORRECCIÓN DE CRUCE ---
    # En Dosificaciones: Grado='GB', Res='20' -> Necesitamos 'GB20'
    # En Resistencia: Grado='GB20'
    
    # Crear 'grado_join' en Dosificaciones concatenando columnas
    # Aseguramos que resistencia no tenga decimales (.0) si es string
    res_str = df_dos['resistencia'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_dos['grado_join'] = df_dos['grado'] + res_str
    
    # En Resistencia el grado ya viene listo
    df_res['grado_join'] = df_res['grado']
    
    # Clave: GRADO_JOIN + FD + TMN + DOCILIDAD
    df_res['clave_mix'] = (
        df_res['grado_join'] + "_" + 
        df_res['fraccion_defectuosa'].astype(str) + "_" + 
        df_res['tmn'].astype(str) + "_" + 
        df_res['docilidad']
    )
    
    # Clave en Dosificaciones
    df_dos['clave_mix'] = (
        df_dos['grado_join'] + "_" + 
        df_dos['fraccion_defectuosa'].astype(str) + "_" + 
        df_dos['tmn'].astype(str) + "_" + 
        df_dos['docilidad']
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
        'absorcion': df_filtrado['absorcion'].mean() / 100 if 'absorcion' in df_filtrado.columns else 0.01,
        'granulometria': gran_prom,
        'n_muestras': len(df_filtrado),
        'fecha_ultimo': df_filtrado['fecha_muestreo'].max(),
        'fecha_primero': df_filtrado['fecha_muestreo'].min(),
        'muestras_detalle': df_filtrado[['n_muestra', 'fecha_muestreo', 'drs', 'absorcion']].to_dict('records') if len(df_filtrado) <= 20 else []
    }
    
    return resultado

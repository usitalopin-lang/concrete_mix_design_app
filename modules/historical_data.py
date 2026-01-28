
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
    
    # Unimos
    df_final = pd.merge(df_dos, stats, on='clave_mix', how='left')
    
    return df_final

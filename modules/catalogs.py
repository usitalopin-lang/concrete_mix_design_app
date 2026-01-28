"""
Módulo de gestión de catálogos (Materiales).
Se encarga de leer la configuración de materiales desde Google Sheets.
Incluye datos por defecto (fallback) por si la conexión falla o las hojas no existen.
Maneja conversión de decimales con coma (localización Chile).
"""

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Nombres de las hojas en Google Sheets
SHEET_CEMENTOS = 'Cat_Cementos'
SHEET_ARIDOS = 'Cat_Aridos'
SHEET_ADITIVOS = 'Cat_Aditivos'

# Datos por defecto (Fallback)
FALLBACK_CEMENTOS = [
    {"Marca": "Genérico", "Tipo": "Grado Alta Resistencia", "Densidad": 3100, "Clase": "AR", "Activo": True},
    {"Marca": "Genérico", "Tipo": "Grado Corriente", "Densidad": 3000, "Clase": "Corriente", "Activo": True},
]

FALLBACK_ARIDOS = [
    {"Nombre": "Grava Chancada 25mm", "Tipo": "Grueso", "Densidad_Real": 2730, "Absorcion": 0.9, "Activo": True},
    {"Nombre": "Grava Rodada 25mm", "Tipo": "Intermedio", "Densidad_Real": 2655, "Absorcion": 1.1, "Activo": True},
    {"Nombre": "Arena 10mm", "Tipo": "Fino", "Densidad_Real": 2610, "Absorcion": 1.6, "Activo": True},
]

FALLBACK_ADITIVOS = [
    {"Nombre": "Plastificante", "Funcion": "Plastificante", "Densidad": 1.2, "Dosis_Min": 0.2, "Dosis_Max": 1.0, "Activo": True},
    {"Nombre": "Superplastificante", "Funcion": "Superplastificante", "Densidad": 1.2, "Dosis_Min": 0.5, "Dosis_Max": 2.0, "Activo": True},
    {"Nombre": "Incorporador de Aire", "Funcion": "Incorporador de Aire", "Densidad": 1.05, "Dosis_Min": 0.05, "Dosis_Max": 0.2, "Activo": True},
]

def obtener_conexion():
    """Obtiene o crea la conexión con Google Sheets."""
    return st.connection("gsheets", type=GSheetsConnection)

def limpiar_decimales(df, columnas):
    """Convierte columnas numéricas con coma a float."""
    for col in columnas:
        if col in df.columns:
            # Convertir a string, reemplazar coma por punto, luego a float
            try:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            except Exception:
                pass # Mantener como está si falla
    return df

@st.cache_data(ttl=600)  # Cache de 10 minutos
def obtener_cementos():
    """Obtiene la lista de cementos disponibles."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_CEMENTOS, ttl=0)
        
        # Limpiar decimales
        df = limpiar_decimales(df, ['Densidad'])

        # Filtrar activos y columnas requeridas
        if not df.empty and 'Marca' in df.columns:
             df = df[df['Activo'] == True] if 'Activo' in df.columns else df
             return df.to_dict('records')
        return FALLBACK_CEMENTOS
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar Cat_Cementos desde Sheets: {e}. Usando datos de ejemplo.")
        return FALLBACK_CEMENTOS

@st.cache_data(ttl=600)
def obtener_aridos():
    """Obtiene la lista de áridos disponibles."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_ARIDOS, ttl=0)
        
        # Limpiar decimales
        df = limpiar_decimales(df, ['Densidad_Real', 'Densidad_SSS', 'Absorcion'])

        if not df.empty and 'Nombre' in df.columns:
             df = df[df['Activo'] == True] if 'Activo' in df.columns else df
             return df.to_dict('records')
        return FALLBACK_ARIDOS
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar Cat_Aridos desde Sheets: {e}. Usando datos de ejemplo.")
        return FALLBACK_ARIDOS

@st.cache_data(ttl=600)
def obtener_aditivos():
    """Obtiene la lista de aditivos disponibles."""
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=SHEET_ADITIVOS, ttl=0)
        
        # Limpiar decimales
        df = limpiar_decimales(df, ['Densidad', 'Dosis_Min', 'Dosis_Max'])

        if not df.empty and 'Nombre' in df.columns:
             df = df[df['Activo'] == True] if 'Activo' in df.columns else df
             return df.to_dict('records')
        return FALLBACK_ADITIVOS
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar Cat_Aditivos desde Sheets: {e}. Usando datos de ejemplo.")
        return FALLBACK_ADITIVOS

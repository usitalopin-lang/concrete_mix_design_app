import pandas as pd
import streamlit as st
from config.config import TAMICES_ASTM, MAPEO_COLUMNAS_EXCEL

SHEET_ID = "1nSnoJ1rN6U9WJo7IIC23L9MD74dV0XyaYPb_D64bmmg"
GID_ARIDOS = "67864589"
# Corrected URL format (fixed user markdown typo)
URL_ARIDOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_ARIDOS}"

@st.cache_data(ttl=300)
def cargar_catalogo_aridos():
    try:
        df = pd.read_csv(URL_ARIDOS)
        df = df.dropna(subset=['Nombre del Árido'])
        
        # Renombrar solo las columnas de tamices (granulometría)
        # Las columnas de propiedades mantienen sus nombres originales
        df = df.rename(columns=MAPEO_COLUMNAS_EXCEL)
        
        # Convertir columnas numéricas
        cols_numericas = ['Densidad Real Seca-DRS', 'Absorción de Agua (%)']
        # Agregar tamices ASTM que existan en el DataFrame
        for tamiz in TAMICES_ASTM:
            if tamiz in df.columns:
                cols_numericas.append(tamiz)
        
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        return df
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        return pd.DataFrame()

def obtener_arido_por_nombre(nombre_arido, df_catalogo):
    row = df_catalogo[df_catalogo['Nombre del Árido'] == nombre_arido].iloc[0]
    granulometria = [float(row.get(t, 0.0)) for t in TAMICES_ASTM]
    return {
        'nombre': row['Nombre del Árido'],
        'tipo': row.get('Tipo', 'Desconocido'),
        'DRS': float(row.get('Densidad Real Seca-DRS', 2650)),
        'absorcion': float(row.get('Absorción de Agua (%)', 1.0)) / 100.0,
        'granulometria': granulometria,
        'origen': row.get('Origen', '-')
    }

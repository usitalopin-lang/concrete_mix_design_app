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
        
        # Debug: mostrar columnas originales
        st.info(f"📋 Columnas encontradas en Google Sheets: {list(df.columns)}")
        
        # Verificar que exista al menos una columna identificadora
        posibles_nombres = ['Nombre del Árido', 'Nombre', 'nombre', 'Identificación de Planta', 'Material']
        columna_nombre = None
        for col in posibles_nombres:
            if col in df.columns:
                columna_nombre = col
                break
        
        if columna_nombre is None:
            st.error(f"❌ No se encontró columna de nombre. Columnas disponibles: {list(df.columns)}")
            return pd.DataFrame()
        
        # Limpiar filas vacías
        df = df.dropna(subset=[columna_nombre])
        
        # Si la columna no se llama 'Nombre del Árido', renombrarla
        if columna_nombre != 'Nombre del Árido':
            df = df.rename(columns={columna_nombre: 'Nombre del Árido'})
        
        # Renombrar columnas de tamices
        df = df.rename(columns=MAPEO_COLUMNAS_EXCEL)
        
        # Convertir columnas numéricas
        cols_numericas = []
        # Buscar columnas de densidad y absorción con nombres flexibles
        for col in df.columns:
            if 'densidad' in col.lower() or 'drs' in col.lower():
                cols_numericas.append(col)
            elif 'absorc' in col.lower() or 'abs' in col.lower():
                cols_numericas.append(col)
        
        # Agregar tamices ASTM
        for tamiz in TAMICES_ASTM:
            if tamiz in df.columns:
                cols_numericas.append(tamiz)
        
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        st.success(f"✅ Catálogo cargado: {len(df)} áridos")
        return df
        
    except Exception as e:
        st.error(f"❌ Error cargando base de datos: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def obtener_arido_por_nombre(nombre_arido, df_catalogo):
    if df_catalogo.empty:
        return None
    
    row = df_catalogo[df_catalogo['Nombre del Árido'] == nombre_arido].iloc[0]
    granulometria = [float(row.get(t, 0.0)) for t in TAMICES_ASTM]
    
    # Buscar columnas de densidad y absorción de forma flexible
    drs = 2650.0
    absorcion = 1.0
    
    for col in df_catalogo.columns:
        if 'densidad' in col.lower() and 'seca' in col.lower():
            drs = float(row.get(col, 2650))
        elif 'absorc' in col.lower():
            absorcion = float(row.get(col, 1.0))
    
    return {
        'nombre': row['Nombre del Árido'],
        'tipo': row.get('Tipo', row.get('tipo_material', 'Desconocido')),
        'DRS': drs,
        'DRSSS': drs * (1 + absorcion/100),
        'absorcion': absorcion / 100.0,
        'granulometria': granulometria,
        'origen': row.get('Origen', row.get('Identificación de Planta', '-'))
    }

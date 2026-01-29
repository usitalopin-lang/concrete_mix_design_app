import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from config import TAMICES_ASTM, MAPEO_COLUMNAS_EXCEL

# Nombre de la hoja en Google Sheets
SHEET_ARIDOS = "Cat_Aridos"

@st.cache_data(ttl=300)
def cargar_catalogo_aridos():
    try:
        # Usar st-gsheets-connection como el resto de la app
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=SHEET_ARIDOS, ttl=0)
        
        # La columna se llama simplemente 'Nombre' en este sheet
        if 'Nombre' not in df.columns:
            st.error(f"❌ No se encontró columna 'Nombre'. Columnas disponibles: {list(df.columns)}")
            return pd.DataFrame()
        
        # Limpiar filas vacías
        df = df.dropna(subset=['Nombre'])
        
        # Renombrar 'Nombre' a 'Nombre del Árido' para consistencia interna
        df = df.rename(columns={'Nombre': 'Nombre del Árido'})
        
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

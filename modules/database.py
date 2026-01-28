"""
Módulo de conexión con Google Sheets para almacenamiento de datos.
Utiliza st-gsheets-connection para gestionar usuarios y proyectos.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Nombres de las hojas
HOJA_USUARIOS = 'Users'
HOJA_PROYECTOS = 'Projects'


def obtener_conexion():
    """Obtiene o crea la conexión con Google Sheets."""
    return st.connection("gsheets", type=GSheetsConnection)


def obtener_usuario(email: str) -> dict:
    """
    Busca un usuario por email en la hoja 'Users'.
    
    Args:
        email: Correo del usuario
    
    Returns:
        Diccionario con datos del usuario o None si no existe
    """
    try:
        conn = obtener_conexion()
        # Leer hoja completa con cache de 10 minutos (TTL)
        # Para login, queremos datos frescos, usamos ttl=0 o bajo
        df = conn.read(worksheet=HOJA_USUARIOS, ttl=0)
        
        if df.empty:
            return None
        
        # Buscar usuario
        usuario = df[df['email'] == email]
        
        if usuario.empty:
            return None
        
        return usuario.iloc[0].to_dict()
        
    except Exception as e:
        st.error(f"Error al conectar con base de datos: {e}")
        return None


def guardar_proyecto(datos_proyecto: dict, usuario_email: str) -> bool:
    """
    Guarda un proyecto en la hoja 'Projects'.
    
    Args:
        datos_proyecto: Diccionario con todos los datos del diseño
        usuario_email: Email del usuario que guarda
    
    Returns:
        True si se guardó correctamente
    """
    try:
        conn = obtener_conexion()
        
        # Preparar fila
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nombre_proyecto = f"{datos_proyecto.get('numero_informe', 'S/N')} - {datos_proyecto.get('obra', 'Sin nombre')}"
        
        # Serializar datos complejos a JSON
        datos_json = json.dumps(datos_proyecto, default=str)
        
        nueva_fila = pd.DataFrame([{
            'timestamp': timestamp,
            'usuario': usuario_email,
            'nombre_proyecto': nombre_proyecto,
            'datos_json': datos_json
        }])
        
        # Leer datos actuales
        try:
            df_actual = conn.read(worksheet=HOJA_PROYECTOS, ttl=0)
            df_actualizado = pd.concat([df_actual, nueva_fila], ignore_index=True)
        except:
            # Si la hoja está vacía o no existe
            df_actualizado = nueva_fila
            
        # Escribir de vuelta
        conn.update(worksheet=HOJA_PROYECTOS, data=df_actualizado)
        return True
        
    except Exception as e:
        st.error(f"Error al guardar en la nube: {e}")
        return False


def cargar_proyectos_usuario(usuario_email: str) -> list:
    """
    Carga la lista de proyectos de un usuario.
    
    Args:
        usuario_email: Email del usuario
        
    Returns:
        Lista de diccionarios con metadatos de proyectos
    """
    try:
        conn = obtener_conexion()
        df = conn.read(worksheet=HOJA_PROYECTOS, ttl=0)
        
        if df.empty:
            return []
            
        # Filtrar por usuario y ordenar por fecha (más reciente primero)
        # Asegurar que timestamp se lea bien
        if 'usuario' in df.columns:
             proyectos = df[df['usuario'] == usuario_email].sort_values(by='timestamp', ascending=False)
             return proyectos[['timestamp', 'nombre_proyecto', 'datos_json']].to_dict('records')
        
        return []
        
    except Exception as e:
        # st.error(f"Error al leer proyectos: {e}") # Silencioso si falla lectura inicial
        return []

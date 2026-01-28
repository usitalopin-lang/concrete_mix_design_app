"""
Módulo de integración con Google Gemini API
Proporciona análisis inteligente y sugerencias de optimización
para el diseño de mezclas de concreto.

INSTRUCCIONES PARA OBTENER API KEY:
1. Visita https://aistudio.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Copia la API key generada
5. En Streamlit Cloud, configúrala en Secrets:
   - Ve a Settings > Secrets
   - Agrega: GOOGLE_API_KEY = "tu-api-key-aqui"
   
   O usa variable de entorno local:
   - export GOOGLE_API_KEY="tu-api-key-aqui"
"""

import os
from typing import Dict, Optional, List
import json

# Intentar importar la librería de Google AI
try:
    import google.generativeai as genai
    GEMINI_DISPONIBLE = True
except ImportError:
    GEMINI_DISPONIBLE = False
    genai = None


def obtener_api_key() -> Optional[str]:
    """
    Obtiene la API key de Gemini desde diferentes fuentes.
    
    Prioridad:
    1. Variable de entorno GOOGLE_API_KEY
    2. Streamlit secrets (si está disponible)
    
    Returns:
        API key o None si no está configurada
    """
    # 1. Variable de entorno
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key:
        return api_key
    
    # 2. Streamlit secrets (solo si streamlit está importado)
    try:
        import streamlit as st
        # Verificar session_state primero (ingreso manual)
        if hasattr(st, 'session_state') and 'gemini_api_key' in st.session_state:
            return st.session_state['gemini_api_key']
        
        # Verificar secrets
        if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
            return st.secrets['GOOGLE_API_KEY']
    except:
        pass
    
    return None


def configurar_gemini(api_key: Optional[str] = None) -> bool:
    """
    Configura la API de Gemini.
    
    Args:
        api_key: API key (opcional, se busca automáticamente si no se proporciona)
    
    Returns:
        True si se configuró correctamente
    """
    if not GEMINI_DISPONIBLE:
        return False
    
    if api_key is None:
        api_key = obtener_api_key()
    
    if api_key is None:
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        return False


def crear_prompt_analisis(datos_mezcla: Dict) -> str:
    """
    Crea el prompt para análisis de la mezcla de concreto.
    
    Args:
        datos_mezcla: Diccionario con los datos de la mezcla
    
    Returns:
        Prompt formateado para Gemini
    """
    prompt = """Eres un experto en tecnología del concreto y diseño de mezclas.
Analiza los siguientes datos de una mezcla de concreto diseñada con el método Faury-Joisel
para un laboratorio en la Región de Magallanes, Chile (zona de clima frío y ciclos de hielo-deshielo).
Proporciona un análisis técnico detallado en español.

DATOS DE LA MEZCLA:
"""
    
    # Agregar datos relevantes
    if 'resistencia' in datos_mezcla.get('faury_joisel', {}):
        res = datos_mezcla['faury_joisel']['resistencia']
        prompt += f"\n- Resistencia de diseño (fd): {res.get('fd_mpa', 0):.1f} MPa"
    
    if 'cemento' in datos_mezcla.get('faury_joisel', {}):
        cem = datos_mezcla['faury_joisel']['cemento']
        prompt += f"\n- Cantidad de cemento: {cem.get('cantidad', 0):.0f} kg/m³"
    
    if 'agua_cemento' in datos_mezcla.get('faury_joisel', {}):
        ac = datos_mezcla['faury_joisel']['agua_cemento']
        prompt += f"\n- Razón agua/cemento: {ac.get('razon', 0):.3f}"
        prompt += f"\n- Agua total: {ac.get('agua_total', 0):.1f} lt/m³"
    
    if 'compacidad' in datos_mezcla.get('faury_joisel', {}):
        prompt += f"\n- Compacidad: {datos_mezcla['faury_joisel']['compacidad']:.4f}"
    
    # Datos Aditivos
    if 'aditivos' in datos_mezcla.get('faury_joisel', {}):
        aditivos = datos_mezcla['faury_joisel']['aditivos']
        if aditivos:
            prompt += f"\n- Aditivos:"
            for ad in aditivos:
                prompt += f"\n  * {ad['nombre']}: {ad['dosis_pct']}% ({ad['cantidad_kg']} kg/m³)"
    
    # Datos Shilstone
    if 'shilstone' in datos_mezcla:
        shil = datos_mezcla['shilstone']
        prompt += f"\n\nANÁLISIS SHILSTONE:"
        prompt += f"\n- Coarseness Factor (CF): {shil.get('CF', 0):.1f}"
        prompt += f"\n- Workability Factor ajustado (Wadj): {shil.get('Wadj', 0):.1f}"
        prompt += f"\n- Factor de Mortero (FM): {shil.get('FM', 0):.1f} lt/m³"
        if 'evaluacion' in shil:
            prompt += f"\n- Zona: {shil['evaluacion'].get('zona', '-')}"
            prompt += f"\n- Calidad: {shil['evaluacion'].get('calidad', '-')}"
    
    prompt += """

Por favor proporciona:
1. EVALUACIÓN GENERAL: ¿La mezcla cumple con los estándares típicos?
2. ANÁLISIS DE TRABAJABILIDAD: Basado en los factores Shilstone
3. DURABILIDAD POTENCIAL: Considerando la razón a/c y contenido de cemento
4. PUNTOS FUERTES: Aspectos positivos del diseño
5. ÁREAS DE MEJORA: Aspectos que podrían optimizarse
6. RECOMENDACIONES: Sugerencias específicas para mejorar la mezcla

Responde de forma técnica pero clara, estructurando tu análisis con los puntos anteriores."""

    return prompt


def crear_prompt_sugerencias(datos_mezcla: Dict, problema: str = None) -> str:
    """
    Crea el prompt para solicitar sugerencias de optimización.
    
    Args:
        datos_mezcla: Diccionario con los datos de la mezcla
        problema: Descripción del problema específico (opcional)
    
    Returns:
        Prompt formateado
    """
    prompt = """Eres un experto en diseño de mezclas de concreto.
Proporciona sugerencias específicas para optimizar la siguiente mezcla.

DATOS ACTUALES:
"""
    
    # Agregar datos relevantes
    faury = datos_mezcla.get('faury_joisel', {})
    
    if 'cantidades_kg_m3' in faury:
        prompt += "\nCantidades de áridos (kg/m³):"
        for material, cantidad in faury['cantidades_kg_m3'].items():
            prompt += f"\n  - {material}: {cantidad:.1f} kg"
    
    if 'proporciones_peso' in faury:
        prompt += "\n\nProporciones en peso:"
        for material, prop in faury['proporciones_peso'].items():
            prompt += f"\n  - {material}: {prop*100:.1f}%"

    if 'aditivos' in faury:
        aditivos = faury['aditivos']
        if aditivos:
            prompt += "\n\nAditivos:"
            for ad in aditivos:
                prompt += f"\n  - {ad['nombre']}: {ad['dosis_pct']}%"
    
    shil = datos_mezcla.get('shilstone', {})
    if shil:
        prompt += f"\n\nParámetros Shilstone:"
        prompt += f"\n  - CF: {shil.get('CF', 0):.1f}"
        prompt += f"\n  - Wadj: {shil.get('Wadj', 0):.1f}"
        prompt += f"\n  - Zona: {shil.get('evaluacion', {}).get('zona', 'No definida')}"
    
    if problema:
        prompt += f"\n\nPROBLEMA ESPECÍFICO A RESOLVER:\n{problema}"
    
    prompt += """

Proporciona sugerencias específicas y prácticas para:
1. Mejorar la trabajabilidad
2. Optimizar la resistencia
3. Reducir costos sin comprometer calidad
4. Ajustar proporciones de agregados

Incluye valores numéricos cuando sea posible."""

    return prompt


def analizar_mezcla(datos_mezcla: Dict, api_key: Optional[str] = None) -> Dict:
    """
    Analiza la mezcla de concreto usando Gemini AI.
    
    Args:
        datos_mezcla: Diccionario con los datos de la mezcla
        api_key: API key de Gemini (opcional)
    
    Returns:
        Diccionario con el análisis
    """
    resultado = {
        'exito': False,
        'analisis': '',
        'error': None
    }
    
    if not GEMINI_DISPONIBLE:
        resultado['error'] = "La librería google-generativeai no está instalada"
        return resultado
    
    if not configurar_gemini(api_key):
        resultado['error'] = "No se pudo configurar la API de Gemini. Verifica tu API key."
        return resultado
    
    try:
        # Crear el modelo
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Crear el prompt
        prompt = crear_prompt_analisis(datos_mezcla)
        
        # Generar respuesta
        response = model.generate_content(prompt)
        
        if response and response.text:
            resultado['exito'] = True
            resultado['analisis'] = response.text
        else:
            resultado['error'] = "No se recibió respuesta de Gemini"
    
    except Exception as e:
        resultado['error'] = f"Error al comunicarse con Gemini: {str(e)}"
    
    return resultado


def obtener_sugerencias(datos_mezcla: Dict, problema: str = None,
                        api_key: Optional[str] = None) -> Dict:
    """
    Obtiene sugerencias de optimización usando Gemini AI.
    
    Args:
        datos_mezcla: Diccionario con los datos de la mezcla
        problema: Descripción del problema específico (opcional)
        api_key: API key de Gemini (opcional)
    
    Returns:
        Diccionario con las sugerencias
    """
    resultado = {
        'exito': False,
        'sugerencias': '',
        'error': None
    }
    
    if not GEMINI_DISPONIBLE:
        resultado['error'] = "La librería google-generativeai no está instalada"
        return resultado
    
    if not configurar_gemini(api_key):
        resultado['error'] = "No se pudo configurar la API de Gemini. Verifica tu API key."
        return resultado
    
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = crear_prompt_sugerencias(datos_mezcla, problema)
        response = model.generate_content(prompt)
        
        if response and response.text:
            resultado['exito'] = True
            resultado['sugerencias'] = response.text
        else:
            resultado['error'] = "No se recibió respuesta de Gemini"
    
    except Exception as e:
        resultado['error'] = f"Error al comunicarse con Gemini: {str(e)}"
    
    return resultado


def responder_pregunta(datos_mezcla: Dict, pregunta: str,
                       api_key: Optional[str] = None) -> Dict:
    """
    Responde una pregunta específica sobre la mezcla usando Gemini.
    
    Args:
        datos_mezcla: Diccionario con los datos de la mezcla
        pregunta: Pregunta del usuario
        api_key: API key de Gemini (opcional)
    
    Returns:
        Diccionario con la respuesta
    """
    resultado = {
        'exito': False,
        'respuesta': '',
        'error': None
    }
    
    if not GEMINI_DISPONIBLE:
        resultado['error'] = "La librería google-generativeai no está instalada"
        return resultado
    
    if not configurar_gemini(api_key):
        resultado['error'] = "No se pudo configurar la API de Gemini. Verifica tu API key."
        return resultado
    
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Crear contexto con los datos de la mezcla
        contexto = json.dumps(datos_mezcla, indent=2, default=str)
        
        prompt = f"""Eres un experto en tecnología del concreto.
Tienes los siguientes datos de una mezcla de concreto:

{contexto}

PREGUNTA DEL USUARIO:
{pregunta}

Responde de forma clara, técnica y en español. Si la pregunta no está relacionada
con el concreto o la mezcla, indica amablemente que solo puedes ayudar con temas
de diseño de mezclas de concreto."""

        response = model.generate_content(prompt)
        
        if response and response.text:
            resultado['exito'] = True
            resultado['respuesta'] = response.text
        else:
            resultado['error'] = "No se recibió respuesta de Gemini"
    
    except Exception as e:
        resultado['error'] = f"Error al comunicarse con Gemini: {str(e)}"
    
    return resultado


def verificar_conexion(api_key: Optional[str] = None) -> Dict:
    """
    Verifica si la conexión con Gemini está funcionando.
    
    Args:
        api_key: API key de Gemini (opcional)
    
    Returns:
        Diccionario con el estado de la conexión
    """
    resultado = {
        'disponible': False,
        'configurado': False,
        'funcionando': False,
        'mensaje': ''
    }
    
    if not GEMINI_DISPONIBLE:
        resultado['mensaje'] = "La librería google-generativeai no está instalada"
        return resultado
    
    resultado['disponible'] = True
    
    if not configurar_gemini(api_key):
        resultado['mensaje'] = "API key no configurada o inválida"
        return resultado
    
    resultado['configurado'] = True
    
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content("Responde solo 'OK' si puedes leer este mensaje.")
        
        if response and response.text:
            resultado['funcionando'] = True
            resultado['mensaje'] = "Conexión exitosa con Gemini API"
        else:
            resultado['mensaje'] = "No se recibió respuesta de Gemini"
    
    except Exception as e:
        # Intentar listar modelos para ver qué está pasando
        try:
             modelos = []
             for m in genai.list_models():
                 if 'generateContent' in m.supported_generation_methods:
                     modelos.append(m.name)
             
             if modelos:
                 resultado['mensaje'] = f"Error con el modelo seleccionado. Modelos disponibles: {', '.join(modelos)}"
             else:
                 resultado['mensaje'] = f"Error de conexión: {str(e)}. No se encontraron modelos disponibles."
        except Exception as e2:
             resultado['mensaje'] = f"Error de conexión: {str(e)}"
    
    return resultado


# Funciones auxiliares para la interfaz de usuario

def obtener_instrucciones_configuracion() -> str:
    """
    Retorna instrucciones para configurar la API key de Gemini.
    """
    return """
### Configuración de Gemini API

Para habilitar el análisis con IA, necesitas configurar una API key de Google Gemini:

1. **Obtener API Key:**
   - Visita [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Inicia sesión con tu cuenta de Google
   - Haz clic en "Create API Key"
   - Copia la clave generada

2. **Configurar en Streamlit Cloud:**
   - Ve a Settings > Secrets en tu app
   - Agrega: `GOOGLE_API_KEY = "tu-api-key-aqui"`

3. **Configurar localmente:**
   - Exporta la variable de entorno:
   ```bash
   export GOOGLE_API_KEY="tu-api-key-aqui"
   ```

**Nota:** La API de Gemini tiene una capa gratuita generosa para uso personal.
"""


def formatear_analisis_para_ui(analisis: str) -> str:
    """
    Formatea el análisis de Gemini para mejor visualización en Streamlit.
    
    Args:
        analisis: Texto del análisis de Gemini
    
    Returns:
        Texto formateado
    """
    # El texto ya viene formateado de Gemini, pero podemos hacer ajustes menores
    # si es necesario
    
    # Asegurar que los encabezados tengan formato correcto
    lineas = analisis.split('\n')
    lineas_formateadas = []
    
    for linea in lineas:
        # Convertir numeración a encabezados si es necesario
        if linea.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
            linea = f"**{linea.strip()}**"
        lineas_formateadas.append(linea)
    
    return '\n'.join(lineas_formateadas)

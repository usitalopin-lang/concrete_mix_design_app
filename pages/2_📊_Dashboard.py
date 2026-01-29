import streamlit as st
from modules.utils_ui import inicializar_estado, sidebar_user_info
from modules.dashboard import render_dashboard

st.set_page_config(
    page_title="Dashboard | Inteligencia",
    page_icon="📊",
    layout="wide"
)

inicializar_estado()

# Gatekeeper
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Debes [iniciar sesión](/) en la página principal.")
    st.stop()

sidebar_user_info()

# --- GUÍA DE EXPERTO (Consultoría Técnica) ---
with st.expander("🎓 Guía de Experto: ¿Qué curva debo usar?", expanded=True):
    st.markdown("""
    ### 🏗️ Selección de Estrategia según Aplicación
    
    Esta aplicación incluye los motores de optimización más avanzados del mundo. Elige tu herramienta según el hormigón que vas a fabricar:

    #### 1. 🏭 Prefabricados Secos (Adoquines, Soleras, Bloques)
    *   **Herramienta:** **Power 45**
    *   **Meta:** Máxima Densidad / Empaquetamiento.
    *   **Por qué:** Estas máquinas "vibran y prensan" mezclas muy secas. Necesitas que los áridos encajen perfectamente (como un tetris) para que el bloque tenga resistencia verde inmediata y no se desmorone.
    *   **Shilstone:** Busca la frontera **Zona II (Rocky)** con poco mortero.

    #### 2. 🛣️ Pavimentos Urbanos e Interurbanos (Slipform)
    *   **Herramienta:** **Illinois Tollway** y **NSW (New South Wales)**
    *   **Meta:** Estabilidad de Borde y Trabajabilidad Baja.
    *   **Por qué:** Para pavimentadoras de moldaje deslizante, el hormigón debe ser "tixotrópico": fluido al vibrar, pero sólido al instante para que el borde no se caiga (slump edge).
    *   **Ideal:** Si tu curva entra en la banda roja de **Illinois**, estás cumpliendo la norma más exigente de USA para autopistas.

    #### 3. 🏗️ Hormigón Bombeable y Edificación (Docilidad > 16cm)
    *   **Herramienta:** **Shilstone (Carta Coarseness Factor)**
    *   **Meta:** Reología y Bombeabilidad.
    *   **Por qué:** Para bombear, necesitas "mortero lubricante". 
    *   **Objetivo:** Apunta al **Centro-Superior de la ZONA I**. 
        *   Si caes en Zona II (Abajo/Derecha), bloquearás la tubería (demasiada piedra, poca crema).
        *   Si caes en Zona IV (Arriba), será pegajoso y demandará mucha agua.

    #### 4. 🏠 Hormigón Convencional / Pisos Industriales
    *   **Herramienta:** **Tarantula (Tyler Ley)**
    *   **Meta:** Acabado superficial y economía.
    *   **Por qué:** La curva Tarantula asegura que tengas suficiente "fino" para fratachar y pulir, pero sin pasarte (ahorrando cemento).
    """)
    st.markdown("---")

render_dashboard()

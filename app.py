import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 1. Configuración de la Página ---
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

# Simulación de base de datos (reemplaza esto con tu conexión real)
def obtener_datos():
    # Aquí iría tu código: df = pd.read_csv('repuestos.csv') o SQL query
    data = {
        'Repuesto': ['Filtro Aceite', 'Pastillas Freno', 'Bujías', 'Amortiguador'],
        'Cantidad': [50, 20, 100, 15],
        'Categoria': ['Motor', 'Frenos', 'Motor', 'Suspensión']
    }
    return pd.DataFrame(data)

# --- 2. Gestión de Estado (Memoria) ---
# Inicializamos el conteo anterior si no existe
if 'conteo_anterior' not in st.session_state:
    st.session_state.conteo_anterior = 0

# Cargamos los datos actuales
df = obtener_datos()
conteo_actual = len(df) # O suma de stock, dependiendo de qué quieras monitorear

# --- 3. Lógica de Notificación y Header ---
# Creamos columnas para poner el título a la izq y la notificación a la derecha
col_titulo, col_notif = st.columns([10, 1])

with col_titulo:
    st.title("📦 Inventario de Repuestos")

with col_notif:
    # Icono estático de notificación arriba a la derecha
    st.markdown("### 🔔")

# VERIFICACIÓN: ¿Hay algo nuevo?
if conteo_actual > st.session_state.conteo_anterior:
    # Solo mostramos la alerta si no es la primera carga de la app
    if st.session_state.conteo_anterior > 0:
        st.toast('Se agregó un nuevo repuesto', icon='✅')
    
    # Actualizamos el estado para la próxima vez
    st.session_state.conteo_anterior = conteo_actual

# --- 4. Visualización (Gráfico de Torta) ---
st.divider()

# Preparar datos para el gráfico (agrupados por categoría, por ejemplo)
if not df.empty:
    fig = px.pie(
        df, 
        values='Cantidad', 
        names='Categoria', 
        title='Distribución de Stock por Categoría',
        hole=0.4 # Opcional: lo hace tipo "Donut" que es más moderno
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos para mostrar en el gráfico.")

# --- 5. Tabla de Datos ---
st.subheader("Listado Detallado")
st.dataframe(df, use_container_width=True)

# --- 6. Auto-refresco (Opcional) ---
# Si necesitas que se actualice solo sin tocar nada, descomenta la línea de abajo:
# time.sleep(5) 
# st.rerun()



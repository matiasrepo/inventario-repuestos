import streamlit as st
import pandas as pd     # <--- Esta es la línea que te faltaba
import requests         # Necesario para "engañar" a SharePoint
import io               # Necesario para leer el archivo descargado

# Configuración básica de la página
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- FUNCION DE CARGA DE DATOS ---
@st.cache_data  # Esto guarda los datos en memoria para no descargar el Excel a cada clic
def cargar_datos():
    # 1. Tu enlace original
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA?e=znye9A"

    # 2. Modificamos el link para que sea de descarga directa
    # Reemplazamos lo que está después del '?' por 'download=1'
    download_url = original_url.split('?')[0] + '?download=1'

    try:
        # 3. Leemos el excel
        df = pd.read_excel(download_url)
        return df
        
    except Exception as e:
        # Mostramos el error en la pantalla de la app
        st.error(f"⚠️ Error al cargar el archivo: {e}")
        st.info("Asegúrate de que el enlace sea público y no requiera inicio de sesión corporativo.")
        return None

# --- INICIO DE LA APP ---

st.title("📊 Monitor de Stock/Repuestos")

# Llamamos a la función
df = cargar_datos()

if df is not None:
    # Limpieza básica: Quitamos espacios en los nombres de columnas por si acaso
    df.columns = df.columns.str.strip()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")

    # Filtro TIPO
    # Verificamos si existe la columna 'Tipo'
    if 'Tipo' in df.columns:
        tipos_disponibles = sorted(df['Tipo'].astype(str).unique())
        tipos_seleccionados = st.sidebar.multiselect(
            "Filtrar por Tipo:",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    else:
        st.error(f"No se encontró la columna 'Tipo'. Las columnas disponibles son: {list(df.columns)}")
        st.stop()

    # Filtro ESTADO
    if 'Estado' in df.columns:
        estados_disponibles = sorted(df['Estado'].astype(str).unique())
        estados_seleccionados = st.sidebar.multiselect(
            "Filtrar por Estado:",
            options=estados_disponibles,
            default=estados_disponibles
        )
    else:
        st.warning("No se encontró la columna 'Estado'.")
        estados_seleccionados = [] # Para evitar error abajo

    # APLICAR FILTROS
    # Si no hay columna Estado, filtramos solo por Tipo
    if 'Estado' in df.columns:
        df_filtrado = df[
            (df['Tipo'].isin(tipos_seleccionados)) &
            (df['Estado'].isin(estados_seleccionados))
        ]
    else:
        df_filtrado = df[df['Tipo'].isin(tipos_seleccionados)]

    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filtrados", len(df_filtrado))
    
    if 'Tipo' in df_filtrado.columns:
        col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))

    if 'Estado' in df_filtrado.columns:
        # Ejemplo: Contar cuántos 'A' hay visibles (ajusta 'A' según tus datos reales)
        conteo_a = len(df_filtrado[df_filtrado['Estado'] == 'A'])
        col3.metric("En Estado 'A'", conteo_a)

    st.divider()

    # --- VISTA PRINCIPAL ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    with tab1:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            # Tabla dinámica: Filas=Tipo, Columnas=Estado, Valor=Cantidad
            resumen = df_filtrado.groupby(['Tipo', 'Estado']).size().unstack(fill_value=0)
            
            st.write("### Cantidad de repuestos por Estado y Tipo")
            st.dataframe(resumen, use_container_width=True)
            
            st.write("### Gráfico de Barras")
            st.bar_chart(resumen)
        elif df_filtrado.empty:
            st.warning("No hay datos para mostrar con estos filtros.")
        else:
            st.info("Se necesitan columnas 'Tipo' y 'Estado' para generar el gráfico.")

else:
    st.warning("Esperando datos...")







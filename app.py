import streamlit as st
import pandas as pd     # <--- Esta es la línea que te faltaba
import requests         # Necesario para "engañar" a SharePoint
import io               # Necesario para leer el archivo descargado

# Configuración básica de la página
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- FUNCION DE CARGA DE DATOS (CON CORRECCIÓN ERROR 403) ---
@st.cache_data
def cargar_datos():
    # 1. Tu enlace original
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA?e=CcuD0i"

    # 2. Preparamos el link de descarga
    # Quitamos cualquier parámetro extra después del '?' y agregamos download=1
    base_url = original_url.split('?')[0]
    download_url = base_url + '?download=1'

    # 3. EL TRUCO: Headers para parecer un navegador (Chrome) y evitar el Error 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    try:
        # Hacemos la petición con requests usando los headers falsos
        response = requests.get(download_url, headers=headers, timeout=10)
        
        # Verificamos si hubo error (lanza excepción si es 403, 404, etc.)
        response.raise_for_status()

        # Convertimos los bytes descargados en un archivo virtual para pandas
        archivo_virtual = io.BytesIO(response.content)
        
        df = pd.read_excel(archivo_virtual)
        return df

    except requests.exceptions.HTTPError as err:
        st.error(f"⚠️ Error de red (Código {err.response.status_code}): SharePoint bloqueó la conexión.")
        st.info("Intenta regenerar el enlace público en SharePoint si el error persiste.")
        return None
    except Exception as e:
        st.error(f"⚠️ Error inesperado: {e}")
        return None

# --- INICIO DE LA APP ---

st.title("📊 Monitor de Stock/Repuestos")

# Llamamos a la función
df = cargar_datos()

if df is not None:
    # Limpieza básica: Quitamos espacios en los nombres de columnas
    df.columns = df.columns.str.strip()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")

    # Filtro TIPO
    if 'Tipo' in df.columns:
        # Convertimos a string para evitar errores si hay números mezclados
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
        estados_seleccionados = []

    # APLICAR FILTROS
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
        # Ejemplo: Contar cuántos 'A' hay visibles
        conteo_a = len(df_filtrado[df_filtrado['Estado'] == 'A'])
        col3.metric("En Estado 'A'", conteo_a)

    st.divider()

    # --- VISTA PRINCIPAL ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    with tab1:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            # Tabla dinámica
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









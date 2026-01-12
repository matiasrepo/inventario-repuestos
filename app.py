import streamlit as st
import pandas as pd
import requests
import io

# Configuración básica de la página
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- FUNCION DE CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # 1. Tu enlace original
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA"

    # 2. Preparamos el link de descarga
    base_url = original_url.split('?')[0]
    download_url = base_url + '?download=1'

    # 3. Headers para evitar error 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    try:
        response = requests.get(download_url, headers=headers, timeout=10)
        response.raise_for_status()
        archivo_virtual = io.BytesIO(response.content)
        df = pd.read_excel(archivo_virtual)
        return df

    except requests.exceptions.HTTPError as err:
        st.error(f"⚠️ Error de red: {err}")
        return None
    except Exception as e:
        st.error(f"⚠️ Error inesperado: {e}")
        return None

# --- INICIO DE LA APP ---

st.title("📊 Monitor de Stock/Repuestos")

df = cargar_datos()

if df is not None:
    # --- CORRECCIÓN DE COLUMNAS (AQUÍ ESTÁ LA SOLUCIÓN) ---
    # 1. Limpiamos los nombres (quitamos espacios extra)
    df.columns = df.columns.str.strip()
    
    # 2. Mapa de renombre basado en los nombres reales de tu Excel
    columnas_renombrar = {
        'Pieza\n/Parte': 'Tipo',       # Nombre en Excel -> Nombre en App
        'Estado\nCondición': 'Estado', # Nombre en Excel -> Nombre en App
        'Pieza /Parte': 'Tipo',        # (Opción por si pandas ya quitó el salto de línea)
        'Estado Condición': 'Estado'
    }
    
    # 3. Aplicamos el renombre
    df.rename(columns=columnas_renombrar, inplace=True)

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")

    # Filtro TIPO
    if 'Tipo' in df.columns:
        # Convertimos a string y ordenamos
        tipos_disponibles = sorted(df['Tipo'].astype(str).unique())
        tipos_seleccionados = st.sidebar.multiselect(
            "Filtrar por Tipo (Pieza/Parte):",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    else:
        st.error(f"⚠️ No se encontró la columna 'Pieza/Parte' o 'Tipo'. Columnas actuales: {list(df.columns)}")
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
        st.warning("No se encontró la columna 'Estado/Condición'.")
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
        # Aquí puedes ajustar 'A' por el valor real que signifique "Buen estado" en tu Excel
        conteo_ok = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
        col3.metric("En Buen Estado (Est.)", conteo_ok)

    st.divider()

    # --- VISTA PRINCIPAL ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    with tab1:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            resumen = df_filtrado.groupby(['Tipo', 'Estado']).size().unstack(fill_value=0)
            
            st.write("### Cantidad por Estado y Tipo")
            st.bar_chart(resumen)
            st.write(resumen)
        else:
            st.info("No hay datos suficientes para graficar.")

else:
    st.warning("Esperando datos...")









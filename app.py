import streamlit as st
import pandas as pd
import requests
import io
import time  # <--- NUEVO: Para generar el timestamp único

# Configuración básica de la página
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- FUNCION DE CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA"
    
    # 1. Limpiamos la URL base
    base_url = original_url.split('?')[0]
    
    # 2. TRUCO ANTI-CACHÉ: Agregamos un parámetro 't' con la hora actual
    # Esto fuerza a SharePoint a entregarnos el archivo nuevo sí o sí.
    timestamp = int(time.time())
    download_url = f"{base_url}?download=1&t={timestamp}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    try:
        response = requests.get(download_url, headers=headers, timeout=15)
        response.raise_for_status()
        archivo_virtual = io.BytesIO(response.content)
        df = pd.read_excel(archivo_virtual)
        return df
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        return None

# --- INICIO DE LA APP ---

st.title("📊 Monitor de Stock/Repuestos")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración")

if st.sidebar.button("🔄 Actualizar Datos Ahora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🔍 Filtros")

# Carga de datos
df = cargar_datos()

if df is not None:
    # --- DIAGNÓSTICO (Para ver si la fila nueva llegó) ---
    # Mostramos esto pequeño arriba para confirmar que Python leyó la fila nueva
    st.caption(f"ℹ️ Filas totales leídas del Excel (sin filtros): **{len(df)}**")

    # --- CORRECCIÓN DE COLUMNAS ---
    df.columns = df.columns.str.strip()
    
    columnas_renombrar = {
        'Pieza\n/Parte': 'Tipo',
        'Estado\nCondición': 'Estado',
        'Pieza /Parte': 'Tipo',
        'Estado Condición': 'Estado'
    }
    df.rename(columns=columnas_renombrar, inplace=True)

    # --- FILTROS ---
    
    # IMPORTANTE: Manejo de valores vacíos (NaN)
    # Rellenamos los vacíos con "Sin Dato" para que no desaparezcan del filtro
    if 'Tipo' in df.columns:
        df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
        tipos_disponibles = sorted(df['Tipo'].astype(str).unique())
        
        tipos_seleccionados = st.sidebar.multiselect(
            "Filtrar por Tipo:",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    else:
        st.error("Error: No se encontró la columna 'Tipo'.")
        st.stop()

    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].fillna('Sin Estado')
        estados_disponibles = sorted(df['Estado'].astype(str).unique())
        
        estados_seleccionados = st.sidebar.multiselect(
            "Filtrar por Estado:",
            options=estados_disponibles,
            default=estados_disponibles
        )
    else:
        estados_seleccionados = []

    # APLICAR LÓGICA DE FILTRADO
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
        conteo_ok = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
        col3.metric("En Buen Estado", conteo_ok)

    st.divider()

    # --- PESTAÑAS ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    with tab1:
        st.write(f"### Mostrando {len(df_filtrado)} registros")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            resumen = df_filtrado.groupby(['Tipo', 'Estado']).size().unstack(fill_value=0)
            
            col_graf, col_tabla = st.columns([2, 1])
            with col_graf:
                st.bar_chart(resumen)
            with col_tabla:
                st.dataframe(resumen, use_container_width=True)
        else:
            st.info("No hay datos para graficar.")

else:
    st.warning("Cargando datos...")











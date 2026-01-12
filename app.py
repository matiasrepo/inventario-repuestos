import streamlit as st
import pandas as pd
import requests
import io
import time
import plotly.express as px

# --- Configuración básica (Debe ir al principio) ---
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- 1. GESTIÓN DE ESTADO (MEMORIA) ---
if 'total_filas_anterior' not in st.session_state:
    st.session_state.total_filas_anterior = 0

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA"
    
    base_url = original_url.split('?')[0]
    timestamp = int(time.time())
    download_url = f"{base_url}?download=1&t={timestamp}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(download_url, headers=headers, timeout=15)
        response.raise_for_status()
        archivo_virtual = io.BytesIO(response.content)
        df = pd.read_excel(archivo_virtual)
        return df
    except Exception as e:
        st.error(f"⚠️ Error al conectar con SharePoint: {e}")
        return None

# --- APP PRINCIPAL ---

# Carga inicial
df = cargar_datos()

# Encabezado y Notificación
col_header, col_bell = st.columns([10, 1])
with col_header:
    st.title("📊 Inventario de repuestos RMA")
with col_bell:
    st.markdown("## 🔔")

if df is not None:
    # --- Detección de Cambios ---
    filas_actuales = len(df)
    if filas_actuales > st.session_state.total_filas_anterior:
        if st.session_state.total_filas_anterior > 0:
            st.toast('Se agregó un nuevo repuesto', icon='✅')
        st.session_state.total_filas_anterior = filas_actuales

    # --- Limpieza de Datos ---
    df.columns = df.columns.str.strip()
    columnas_renombrar = {
        'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
        'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
    }
    df.rename(columns=columnas_renombrar, inplace=True)
    
    if 'Tipo' in df.columns: df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
    if 'Estado' in df.columns: df['Estado'] = df['Estado'].fillna('Sin Estado')

    # --- SIDEBAR: Filtros ---
    st.sidebar.header("⚙️ Configuración")
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros")
    st.sidebar.caption(f"ℹ️ Filas totales en Excel: **{len(df)}**")

    # Filtro TIPO
    tipos_disponibles = sorted(df['Tipo'].astype(str).unique())
    tipos_seleccionados = st.sidebar.multiselect(
        "Filtrar por Tipo:",
        options=tipos_disponibles,
        default=[]
    )

    # Filtro ESTADO
    if 'Estado' in df.columns:
        estados_disponibles = sorted(df['Estado'].astype(str).unique())
        estados_seleccionados = st.sidebar.multiselect(
            "Filtrar por Estado:",
            options=estados_disponibles,
            default=[]
        )
    else:
        estados_seleccionados = []

    # Aplicar lógica de filtrado
    df_filtrado = df.copy()
    if tipos_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos_seleccionados)]
    if estados_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_seleccionados)]

    # --- RESULTADOS Y MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filtrados", len(df_filtrado))
    
    if 'Tipo' in df_filtrado.columns:
        col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))

    if 'Estado' in df_filtrado.columns:
        conteo_ok = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
        col3.metric("En Buen Estado", conteo_ok)

    st.divider()

    # --- PESTAÑAS (Aquí estaba el error de indentación) ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    # Pestaña 1: Tabla con columnas específicas
    # --- PESTAÑA 1: TABLA ---
    with tab1:
        st.write(f"### Listado ({len(df_filtrado)} registros)")
        
        # --- MODIFICAR ESTA LÍNEA ---
        # Agrega 'Descripción' y 'Serial' (Asegúrate que se llamen así en tu Excel)
        columnas_a_mostrar = ['Tipo', 'Estado', 'Marca', 'Modelo', 'Descripción', 'Serial']
        
        # Verificamos cuáles existen realmente para no dar error
        cols_finales = [c for c in columnas_a_mostrar if c in df_filtrado.columns]
        
        if cols_finales:
            st.dataframe(df_filtrado[cols_finales], use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No se encontraron las columnas. Verifica que en el Excel se llamen exactamente: Descripción, Serial, Marca, Modelo.")
            # Mostramos todo por si acaso fallan los nombres
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # Pestaña 2: Gráfico de Torta
    with tab2:
        if not df_filtrado.empty:
            col_graf, col_tabla = st.columns([2, 1])
            
            with col_graf:
                if 'Tipo' in df_filtrado.columns:
                    fig = px.pie(
                        df_filtrado, 
                        names='Tipo', 
                        title='Distribución de Stock por Tipo',
                        hole=0.4 
                    )
                    fig.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_tabla:
                st.write("**Desglose Numérico:**")
                if 'Tipo' in df_filtrado.columns:
                    resumen = df_filtrado['Tipo'].value_counts().reset_index()
                    resumen.columns = ['Tipo', 'Cantidad']
                    st.dataframe(resumen, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos para graficar con la selección actual.")

else:
    # Este else cierra el 'if df is not None' del principio
    st.warning("Esperando datos o error en la carga...")



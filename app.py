import streamlit as st
import pandas as pd
import requests
import io
import time
import plotly.express as px  # <--- NECESARIO PARA EL GRÁFICO DE TORTA

# Configuración básica
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- 1. GESTIÓN DE ESTADO (MEMORIA PARA NOTIFICACIONES) ---
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

# Carga inicial de datos
df = cargar_datos()

# --- 3. LOGICA DE NOTIFICACIÓN Y ENCABEZADO ---
# Creamos columnas para el Título (Izquierda) y la Campana (Derecha)
col_header, col_bell = st.columns([10, 1])

with col_header:
    st.title("📊 Inventario de repuestos RMA")

with col_bell:
    st.markdown("## 🔔") # Icono estático

if df is not None:
    # Lógica de detección de cambios
    filas_actuales = len(df)
    
    if filas_actuales > st.session_state.total_filas_anterior:
        # Solo mostramos el toast si ya teníamos datos antes (evita alerta al abrir la app)
        if st.session_state.total_filas_anterior > 0:
            st.toast('Se agregó un nuevo repuesto', icon='✅')
        
        # Actualizamos la memoria
        st.session_state.total_filas_anterior = filas_actuales

    # Limpieza de datos (Tu código original)
    df.columns = df.columns.str.strip()
    columnas_renombrar = {
        'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
        'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
    }
    df.rename(columns=columnas_renombrar, inplace=True)
    
    if 'Tipo' in df.columns: df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
    if 'Estado' in df.columns: df['Estado'] = df['Estado'].fillna('Sin Estado')

# --- SIDEBAR (CONFIG Y FILTROS) ---
st.sidebar.header("⚙️ Configuración")
if st.sidebar.button("🔄 Actualizar Datos Ahora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🔍 Filtros")

if df is not None:
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

    # Aplicar Filtros
    df_filtrado = df.copy()
    if tipos_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos_seleccionados)]
    if estados_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_seleccionados)]

    # --- RESULTADOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filtrados", len(df_filtrado))
    
    if 'Tipo' in df_filtrado.columns:
        col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))

    if 'Estado' in df_filtrado.columns:
        conteo_ok = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
        col3.metric("En Buen Estado", conteo_ok)

  # ... (esto va justo después de las métricas col1, col2, col3) ...

    st.divider()

    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    # Pestaña 1: Listado (Con selector de columnas)
with tab1:
        st.write(f"### Listado ({len(df_filtrado)} registros)")
        
        # --- MODIFICACIÓN AQUÍ ---
        # 1. Define la lista exacta de nombres de columnas que quieres ver
        # Nota: Usa los nombres YA RENOMBRADOS ('Tipo', 'Estado', etc.)
        columnas_a_mostrar = ['Tipo', 'Estado', 'Marca', 'Modelo'] 
        
        # 2. Filtramos para que no de error si alguna columna no existe en el Excel
        cols_finales = [c for c in columnas_a_mostrar if c in df_filtrado.columns]
        
        # 3. Mostramos solo esas columnas
        st.dataframe(df_filtrado[cols_finales], use_container_width=True, hide_index=True)

    # Pestaña 2: Gráfico de Torta
    with tab2:
        if not df_filtrado.empty:
            col_graf, col_tabla = st.columns([2, 1])
            
            with col_graf:
                # Usamos la columna 'Tipo' para el gráfico
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
    # Esto debe estar alineado al mismo nivel que 'if df is not None:'
    st.warning("Esperando datos o error en la carga...")


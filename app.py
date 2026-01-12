import streamlit as st
import pandas as pd
import requests
import io
import time

# Configuración de la página
st.set_page_config(page_title="Dashboard CompraGamer", layout="wide")

# --- ESTADO DE SESIÓN (MEMORIA) ---
# Inicializamos variables para recordar el estado anterior del Excel
if 'filas_anteriores' not in st.session_state:
    st.session_state['filas_anteriores'] = 0
if 'ultima_actualizacion' not in st.session_state:
    st.session_state['ultima_actualizacion'] = time.strftime("%H:%M:%S")

# --- FUNCION DE CARGA ---
# Quitamos el TTL del caché porque controlaremos la recarga manualmente o por loop
@st.cache_data(ttl=0) 
def cargar_datos(timestamp_trigger):
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA"
    
    base_url = original_url.split('?')[0]
    # Usamos el timestamp para obligar a SharePoint a darnos datos nuevos
    download_url = f"{base_url}?download=1&t={timestamp_trigger}"

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
        st.error(f"⚠️ Error: {e}")
        return None

# --- APP PRINCIPAL ---
st.title("📊 Monitor de Stock/Repuestos")

st.sidebar.header("⚙️ Panel de Control")

# 1. BOTÓN MANUAL
if st.sidebar.button("🔄 Actualizar Ahora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.write(f"🕒 Última carga: {st.session_state['ultima_actualizacion']}")

# 2. MODO MONITOR (AUTO-REFRESH)
st.sidebar.divider()
activar_monitor = st.sidebar.toggle("📡 Activar Modo Monitor (Auto-refresh)")

if activar_monitor:
    st.sidebar.caption("🔄 El sistema buscará cambios cada 60 seg.")
    # NOTA: time.sleep bloquea un poco la UI, es la forma simple sin plugins externos.
    time.sleep(60) 
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🔍 Filtros")

# Generamos un trigger único para esta ejecución
timestamp_actual = int(time.time())
df = cargar_datos(timestamp_actual)

if df is not None:
    # Actualizamos la hora de visualización
    st.session_state['ultima_actualizacion'] = time.strftime("%H:%M:%S")

    # --- SISTEMA DE NOTIFICACIÓN DE CAMBIOS ---
    filas_actuales = len(df)
    diferencia = filas_actuales - st.session_state['filas_anteriores']

    # Si es la primera carga (filas_anteriores es 0), no notificamos.
    # Si hay diferencia y NO es la primera carga, notificamos.
    if st.session_state['filas_anteriores'] > 0 and diferencia != 0:
        if diferencia > 0:
            st.toast(f'🔔 ¡Actualización! Se detectaron {diferencia} registros nuevos.', icon='📈')
        else:
            st.toast(f'🔔 ¡Actualización! Se eliminaron {abs(diferencia)} registros.', icon='🗑️')
    
    # Guardamos el nuevo conteo para la próxima vez
    st.session_state['filas_anteriores'] = filas_actuales

    # --- PROCESAMIENTO DE DATOS ---
    df.columns = df.columns.str.strip()
    col_map = {
        'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
        'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
    }
    df.rename(columns=col_map, inplace=True)
    
    if 'Tipo' in df.columns: df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
    if 'Estado' in df.columns: df['Estado'] = df['Estado'].fillna('Sin Estado')

    # --- FILTROS INTELIGENTES (VACÍO = TODOS) ---
    tipos_disp = sorted(df['Tipo'].astype(str).unique())
    tipos_sel = st.sidebar.multiselect("Filtrar por Tipo:", options=tipos_disp, default=[])

    if 'Estado' in df.columns:
        estados_disp = sorted(df['Estado'].astype(str).unique())
        estados_sel = st.sidebar.multiselect("Filtrar por Estado:", options=estados_disp, default=[])
    else:
        estados_sel = []

    # Aplicar filtros
    df_filtrado = df.copy()
    if tipos_sel:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos_sel)]
    if estados_sel:
        df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_sel)]

    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Visible", len(df_filtrado))
    
    if 'Tipo' in df_filtrado.columns:
        col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))

    if 'Estado' in df_filtrado.columns:
        # Busca "OK", "A" o "Nuevo"
        ok_count = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
        col3.metric("En Buen Estado", ok_count)

    st.divider()

    # --- VISUALIZACIÓN ---
    tab1, tab2 = st.tabs(["📋 Listado", "📊 Gráficos"])

    with tab1:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty and 'Estado' in df_filtrado.columns:
            resumen = df_filtrado.groupby(['Tipo', 'Estado']).size().unstack(fill_value=0)
            c1, c2 = st.columns([2, 1])
            with c1: st.bar_chart(resumen)
            with c2: st.dataframe(resumen, use_container_width=True)
        else:
            st.info("Sin datos para graficar.")
else:
    st.warning("Conectando con SharePoint...")



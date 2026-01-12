import streamlit as st
import pandas as pd
import requests
import io
import time
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="Gestión Stock & Solicitudes", layout="wide")

# --- 1. GESTIÓN DE ESTADO ---
if 'solicitudes' not in st.session_state:
    st.session_state.solicitudes = []
if 'stock_reservado' not in st.session_state:
    st.session_state.stock_reservado = []
if 'total_filas_anterior' not in st.session_state:
    st.session_state.total_filas_anterior = 0

# --- 2. CARGA DE DATOS Y ESTANDARIZACIÓN ---
@st.cache_data(ttl=60)
def cargar_datos():
    original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA"
    base_url = original_url.split('?')[0]
    timestamp = int(time.time())
    download_url = f"{base_url}?download=1&t={timestamp}"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(download_url, headers=headers, timeout=15)
        response.raise_for_status()
        archivo_virtual = io.BytesIO(response.content)
        df = pd.read_excel(archivo_virtual)
        
        # Limpieza básica de espacios en nombres de columnas
        df.columns = df.columns.str.strip()
        
        # --- MAPEO DE COLUMNAS (AJUSTAR SEGÚN TU EXCEL REAL) ---
        # Izquierda: Nombre en tu Excel -> Derecha: Nombre deseado en la App
        mapa_columnas = {
            'Pieza\n/Parte': 'Tipo de repuesto',
            'Pieza /Parte': 'Tipo de repuesto',
            'Tipo': 'Tipo de repuesto',
            
            'Estado\nCondición': 'Estado de repuesto',
            'Estado Condición': 'Estado de repuesto',
            'Estado': 'Estado de repuesto',
            
            'Serial': 'SN Repuesto',
            'SN': 'SN Repuesto',
            'S/N': 'SN Repuesto',
            
            'Producto': 'ID de producto',
            'ID Producto': 'ID de producto',
            
            'Descripcion': 'Descripcion',
            'Descripción': 'Descripcion',
            
            'Observaciones': 'Observación',
            'Observacion': 'Observación',
            'Notas': 'Observación'
        }
        
        # Renombramos
        df.rename(columns=mapa_columnas, inplace=True)
        
        # Generamos ID Único para el sistema
        df['SYS_ID'] = df.index 

        # Aseguramos que existan las columnas clave (relleno si faltan)
        columnas_requeridas = ['SN Repuesto', 'ID de producto', 'Descripcion', 'Tipo de repuesto', 'Estado de repuesto', 'Observación']
        for col in columnas_requeridas:
            if col not in df.columns:
                df[col] = '-' # Rellenar con guion si no existe en el excel original
        
        # Relleno de nulos visuales
        df.fillna('', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"⚠️ Error al procesar datos: {e}")
        return None

df_raw = cargar_datos()

# Filtro de items ya entregados (no mostrar en lista)
if df_raw is not None:
    df_disponible = df_raw[~df_raw['SYS_ID'].isin(st.session_state.stock_reservado)].copy()
else:
    df_disponible = pd.DataFrame()

# --- NAVEGACIÓN ---
st.sidebar.title("🔧 Panel de Control")
rol = st.sidebar.radio("Seleccione Perfil:", ["👤 Usuario (Solicitante)", "🛡️ Admin (Encargado)"])
st.sidebar.divider()

# ==========================================
#  VISTA 1: USUARIO (COLUMNAS LIMITADAS)
# ==========================================
if rol == "👤 Usuario (Solicitante)":
    st.title("📦 Catálogo de Repuestos")
    st.caption("Seleccione un ítem para solicitarlo.")

    if df_disponible.empty:
        st.warning("No hay datos disponibles.")
    else:
        # Filtros
        tipos = df_disponible['Tipo de repuesto'].unique()
        filtro_tipo = st.multiselect("Filtrar por Tipo", tipos)
        
        df_filtrado = df_disponible if not filtro_tipo else df_disponible[df_disponible['Tipo de repuesto'].isin(filtro_tipo)]
        
        # --- DEFINICIÓN DE VISTA USUARIO ---
        # Solo mostramos las columnas que pediste
        cols_usuario = ['SN Repuesto', 'ID de producto', 'Descripcion', 'Tipo de repuesto', 'Estado de repuesto', 'Observación']
        
        # Creamos un dataframe SOLO con esas columnas para mostrar
        df_vista_usuario = df_filtrado[cols_usuario]

        selection = st.dataframe(
            df_vista_usuario, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        if selection["selection"]["rows"]:
            idx_visual = selection["selection"]["rows"][0]
            
            # TRUCO: Recuperamos la fila COMPLETA del dataframe original usando el índice
            # Esto es vital para pasarle toda la info oculta al Admin
            fila_completa = df_filtrado.iloc[idx_visual]
            
            st.divider()
            with st.container(border=True):
                st.subheader("📝 Confirmar Solicitud")
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Componente:** {fila_completa['Tipo de repuesto']}")
                c2.markdown(


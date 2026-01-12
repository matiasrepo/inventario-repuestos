import streamlit as st
import pandas as pd
import requests
import io
import time
import plotly.express as px

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
col_header, col_bell = st.columns([10, 1])

with col_header:
    st.title("📊 Monitor de Stock/Repuestos")

with col_bell:
    st.markdown("## 🔔")

if df is not None:
    # Lógica de detección de cambios
    filas_actuales = len(df)
    
    if filas_actuales > st.session_state.total_filas_anterior:
        if st.session_state.total_filas_anterior > 0:
            st.toast('Se agregó un nuevo repuesto', icon='✅')
        st.session_state.total_filas_anterior = filas_actuales

    # Limpieza de datos
    df.columns = df.columns.str.strip()
    columnas_renombrar = {
        'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
        'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
    }
    df.rename(columns=columnas_renombrar, inplace=True)
    
    # Aseguramos que las columnas clave existan para evitar errores posteriores
    if 'Tipo' not in df.columns: df['Tipo'] = 'Desconocido'
    if 'Estado' not in df.columns: df['Estado'] = 'Desconocido'
    
    df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
    df['Estado'] = df['Estado'].fillna('Sin Estado')

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
    estados_disponibles = sorted(df['Estado'].astype(str).unique())
    estados_seleccionados = st.sidebar.multiselect(
        "Filtrar por Estado:",
        options=estados_disponibles,
        default=[]
    )

    # Aplicar Filtros
    df_filtrado = df.copy()
    if tipos_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos_seleccionados)]
    if estados_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados_seleccionados)]

    # --- RESULTADOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filtrados", len(df_filtrado))
    col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))
    conteo_ok = len(df_filtrado[df_filtrado['Estado'].astype(str).str.contains('OK|A|Nuevo', case=False, na=False)])
    col3.metric("En Buen Estado", conteo_ok)

    st.divider()

    tab1, tab2 = st.tabs(["📋 Listado y Solicitud", "📊 Resumen Gráfico"])

    with tab1:
        st.write(f"### Seleccione un repuesto para solicitar ({len(df_filtrado)} registros)")
        
        # --- NUEVA FUNCIONALIDAD DE SELECCIÓN ---
        # Usamos on_select="rerun" para que la app se actualice al hacer clic
        selection = st.dataframe(
            df_filtrado, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",   # <--- Habilita la interactividad
            selection_mode="single-row" # Solo permite seleccionar una fila a la vez
        )

        # --- ZONA DE SOLICITUD (MOCKUP) ---
        # Verificamos si el usuario seleccionó alguna fila
        if selection["selection"]["rows"]:
            st.divider()
            # Obtenemos el índice de la fila seleccionada en la vista actual
            selected_index_visual = selection["selection"]["rows"][0]
            
            # Accedemos a los datos reales usando .iloc sobre el dataframe filtrado
            datos_repuesto = df_filtrado.iloc[selected_index_visual]

            st.markdown(f"""
            ### 📝 Formulario de Solicitud
            Usted está por solicitar el siguiente ítem:
            
            * **Tipo/Pieza:** `{datos_repuesto['Tipo']}`
            * **Estado:** `{datos_repuesto['Estado']}`
            """)
            
            # Campo opcional para simular interacción
            notas = st.text_area("Notas adicionales para la solicitud (Opcional):", placeholder="Ej: Prioridad alta...")

            col_btn_izq, col_btn_der = st.columns([1,4])
            with col_btn_izq:
                # El Botón Mockup
                if st.button("🚀 Enviar Solicitud", type="primary"):
                    # --- Aquí iría la lógica real de backend (guardar en DB, enviar mail) ---
                    
                    # Feedback visual de "éxito"
                    st.toast(f"Solicitud enviada: {datos_repuesto['Tipo']}", icon="🎉")
                    st.success(f"""
                        ✅ **¡Solicitud Registrada con Éxito!**
                        
                        Se ha generado un ticket para el repuesto: **{datos_repuesto['Tipo']}**.
                    """)
                    st.balloons() 
        else:
            # Mensaje cuando no hay nada seleccionado
            st.info("👆 Haga clic en una fila de la tabla de arriba para habilitar el menú de solicitud.")

    with tab2:
        # --- GRÁFICO DE TORTA ---
        if not df_filtrado.empty:
            col_graf, col_tabla = st.columns([2, 1])
            
            with col_graf:
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
                resumen = df_filtrado['Tipo'].value_counts().reset_index()
                resumen.columns = ['Tipo', 'Cantidad']
                st.dataframe(resumen, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos para graficar con la selección actual.")

else:
    st.warning("Esperando datos o error en la carga...")


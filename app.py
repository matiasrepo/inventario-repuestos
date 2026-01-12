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
                c2.markdown(f"**SN:** `{fila_completa['SN Repuesto']}`")
                c3.markdown(f"**Estado:** {fila_completa['Estado de repuesto']}")
                
                st.markdown(f"**Descripción:** {fila_completa['Descripcion']}")
                
                nombre = st.text_input("Tu Nombre:")
                notas = st.text_area("Notas adicionales:")
                
                if st.button("Enviar Solicitud 🚀", type="primary"):
                    if not nombre:
                        st.error("Falta tu nombre.")
                    else:
                        # Guardamos TODOS los datos de la fila en 'datos_full'
                        nueva_solicitud = {
                            "id_solicitud": len(st.session_state.solicitudes) + 1,
                            "fecha": datetime.now().strftime("%d/%m %H:%M"),
                            "solicitante": nombre,
                            "sys_id": fila_completa['SYS_ID'], # ID único del sistema
                            "resumen": f"{fila_completa['Tipo de repuesto']} (SN: {fila_completa['SN Repuesto']})",
                            "notas_usuario": notas,
                            "datos_full": fila_completa.to_dict(), # <--- AQUÍ VA LA DATA COMPLETA PARA EL ADMIN
                            "status": "Pendiente"
                        }
                        st.session_state.solicitudes.append(nueva_solicitud)
                        st.toast("Solicitud enviada exitosamente", icon="✅")
                        st.balloons()

# ==========================================
#  VISTA 2: ADMIN (INFO COMPLETA)
# ==========================================
elif rol == "🛡️ Admin (Encargado)":
    st.title("🛡️ Centro de Aprobaciones")
    
    pendientes = [s for s in st.session_state.solicitudes if s['status'] == 'Pendiente']
    st.metric("Pendientes de Revisión", len(pendientes))
    st.divider()

    if not pendientes:
        st.info("🎉 Todo limpio. No hay solicitudes pendientes.")
    else:
        for i, sol in enumerate(pendientes):
            data_item = sol['datos_full'] # Recuperamos la data completa
            
            with st.container(border=True):
                # Encabezado: Quién pide y Qué pide (Resumido)
                st.markdown(f"#### 📌 Solicitud #{sol['id_solicitud']} | {sol['resumen']}")
                st.caption(f"Solicitado por: **{sol['solicitante']}** el {sol['fecha']}")
                
                if sol['notas_usuario']:
                    st.info(f"🗣️ Nota del usuario: {sol['notas_usuario']}")

                # --- SECCIÓN: FICHA TÉCNICA COMPLETA ---
                with st.expander("🔍 Ver DETALLES COMPLETOS del Ítem (Ubicación, Precios, etc.)", expanded=True):
                    # Convertimos el diccionario de datos en un DataFrame transpuesto para leerlo verticalmente
                    df_detalle = pd.DataFrame.from_dict(data_item, orient='index', columns=['Valor'])
                    st.dataframe(df_detalle, use_container_width=True)

                # Botones de Acción
                col_btn_ok, col_btn_no = st.columns([1, 1])
                with col_btn_ok:
                    if st.button("✅ Aprobar y Descontar", key=f"ok_{i}", type="primary", use_container_width=True):
                        sol['status'] = 'Aprobada'
                        st.session_state.stock_reservado.append(sol['sys_id'])
                        st.rerun()
                with col_btn_no:
                    if st.button("❌ Rechazar", key=f"no_{i}", use_container_width=True):
                        sol['status'] = 'Rechazada'
                        st.rerun()

    # Historial
    if st.checkbox("Ver Historial de decisiones"):
        st.dataframe(pd.DataFrame(st.session_state.solicitudes))

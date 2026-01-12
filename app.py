import streamlit as st
import pandas as pd
import requests
import io
import time
import plotly.express as px
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="Gestión Stock & Solicitudes", layout="wide")

# --- 1. GESTIÓN DE ESTADO (MEMORIA COMPARTIDA) ---
# Aquí simulamos la "Base de Datos" temporal
if 'solicitudes' not in st.session_state:
    st.session_state.solicitudes = [] # Lista para guardar los pedidos

if 'stock_reservado' not in st.session_state:
    st.session_state.stock_reservado = [] # Lista de IDs de items ya aceptados/entregados

if 'total_filas_anterior' not in st.session_state:
    st.session_state.total_filas_anterior = 0

# --- 2. CARGA DE DATOS ---
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
        
        # Limpieza básica
        df.columns = df.columns.str.strip()
        mapa_cols = {
            'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
            'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
        }
        df.rename(columns=mapa_cols, inplace=True)
        
        # Crear un ID único ficticio si no existe (usamos el índice)
        df['ID_Ref'] = df.index 
        
        if 'Tipo' not in df.columns: df['Tipo'] = 'Desconocido'
        if 'Estado' not in df.columns: df['Estado'] = 'Desconocido'
        df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
        
        return df
    except Exception as e:
        st.error(f"⚠️ Error SharePoint: {e}")
        return None

# Carga inicial
df_raw = cargar_datos()

# --- FILTRO DE STOCK REAL ---
# Si el admin ya "Aceptó" un item, lo quitamos de la vista del usuario
if df_raw is not None:
    df_disponible = df_raw[~df_raw['ID_Ref'].isin(st.session_state.stock_reservado)].copy()
else:
    df_disponible = pd.DataFrame()

# --- NAVEGACIÓN (SIDEBAR) ---
st.sidebar.title("🔧 Panel de Control")
rol = st.sidebar.radio("Seleccione Perfil:", ["👤 Usuario (Solicitante)", "🛡️ Admin (Encargado)"])
st.sidebar.divider()

# ==========================================
#  VISTA 1: USUARIO (SOLICITAR)
# ==========================================
if rol == "👤 Usuario (Solicitante)":
    st.title("📦 Catálogo de Repuestos")
    st.caption("Seleccione un ítem para solicitarlo al encargado.")

    if df_disponible.empty:
        st.warning("No hay datos disponibles o conexión fallida.")
    else:
        # Filtros básicos
        filtro_tipo = st.multiselect("Filtrar por Tipo", df_disponible['Tipo'].unique())
        df_view = df_disponible if not filtro_tipo else df_disponible[df_disponible['Tipo'].isin(filtro_tipo)]
        
        # Tabla Interactiva
        selection = st.dataframe(
            df_view, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        if selection["selection"]["rows"]:
            idx_visual = selection["selection"]["rows"][0]
            item_data = df_view.iloc[idx_visual]
            
            st.divider()
            with st.container(border=True):
                st.subheader("📝 Nueva Solicitud")
                c1, c2 = st.columns(2)
                c1.info(f"**Item:** {item_data['Tipo']}")
                c2.info(f"**Estado:** {item_data['Estado']}")
                
                solicitante = st.text_input("Tu Nombre:", placeholder="Ej. Juan Pérez")
                notas = st.text_area("Motivo / Notas:", placeholder="Para reparación de...")
                
                if st.button("Enviar Solicitud 🚀", type="primary"):
                    if not solicitante:
                        st.error("Por favor ingresa tu nombre.")
                    else:
                        # --- GUARDAR EN "BASE DE DATOS" TEMPORAL ---
                        nueva_solicitud = {
                            "id_solicitud": len(st.session_state.solicitudes) + 1,
                            "fecha": datetime.now().strftime("%H:%M:%S"),
                            "solicitante": solicitante,
                            "item_id": item_data['ID_Ref'], # ID clave para vincular
                            "item_tipo": item_data['Tipo'],
                            "item_estado": item_data['Estado'],
                            "notas": notas,
                            "status": "Pendiente"
                        }
                        st.session_state.solicitudes.append(nueva_solicitud)
                        st.toast("Solicitud enviada al administrador", icon="✅")
                        st.balloons()

# ==========================================
#  VISTA 2: ADMIN (APROBAR/RECHAZAR)
# ==========================================
elif rol == "🛡️ Admin (Encargado)":
    st.title("🛡️ Centro de Aprobaciones")
    
    # Filtramos solo las pendientes
    pendientes = [s for s in st.session_state.solicitudes if s['status'] == 'Pendiente']
    
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("Solicitudes Pendientes", len(pendientes))
    col_metric2.metric("Items Entregados (Sesión)", len(st.session_state.stock_reservado))
    
    st.divider()

    if not pendientes:
        st.info("🎉 No hay solicitudes pendientes. Todo al día.")
    else:
        st.write("### Bandeja de Entrada")
        
        # Iteramos sobre las solicitudes para crear "Tarjetas" de acción
        for i, sol in enumerate(pendientes):
            with st.container(border=True):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"**#{sol['id_solicitud']} | {sol['item_tipo']}**")
                    st.text(f"Solicitante: {sol['solicitante']} | Hora: {sol['fecha']}")
                    st.caption(f"Nota: {sol['notas']}")
                
                with col_actions:
                    # BOTÓN ACEPTAR
                    if st.button("✅ Aceptar", key=f"btn_acc_{i}"):
                        # 1. Marcar solicitud como aprobada
                        sol['status'] = 'Aprobada'
                        # 2. "Quitar" del stock disponible (Agregando a lista negra)
                        st.session_state.stock_reservado.append(sol['item_id'])
                        st.rerun()
                    
                    # BOTÓN RECHAZAR
                    if st.button("❌ Rechazar", key=f"btn_rej_{i}"):
                        sol['status'] = 'Rechazada'
                        st.rerun()

    # Historial (Opcional)
    st.divider()
    with st.expander("Ver Historial de Decisiones"):
        historial = pd.DataFrame(st.session_state.solicitudes)
        if not historial.empty:
            st.dataframe(historial, use_container_width=True)
        else:
            st.text("Sin historial.")


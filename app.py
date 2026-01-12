import streamlit as st
import pandas as pd
import requests
import io
import time
import plotly.express as px
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
        
        df.columns = df.columns.str.strip()
        mapa_cols = {
            'Pieza\n/Parte': 'Tipo', 'Estado\nCondición': 'Estado',
            'Pieza /Parte': 'Tipo', 'Estado Condición': 'Estado'
        }
        df.rename(columns=mapa_cols, inplace=True)
        df['ID_Ref'] = df.index 
        
        if 'Tipo' not in df.columns: df['Tipo'] = 'Desconocido'
        if 'Estado' not in df.columns: df['Estado'] = 'Desconocido'
        df['Tipo'] = df['Tipo'].fillna('Sin Tipo')
        
        return df
    except Exception as e:
        st.error(f"⚠️ Error SharePoint: {e}")
        return None

df_raw = cargar_datos()

if df_raw is not None:
    df_disponible = df_raw[~df_raw['ID_Ref'].isin(st.session_state.stock_reservado)].copy()
else:
    df_disponible = pd.DataFrame()

# --- NAVEGACIÓN ---
st.sidebar.title("🔧 Panel de Control")
rol = st.sidebar.radio("Seleccione Perfil:", ["👤 Usuario (Solicitante)", "🛡️ Admin (Encargado)"])
st.sidebar.divider()

# ==========================================
#  VISTA 1: USUARIO
# ==========================================
if rol == "👤 Usuario (Solicitante)":
    st.title("📦 Catálogo de Repuestos")
    st.caption("Seleccione un ítem para solicitarlo al encargado.")

    if df_disponible.empty:
        st.warning("No hay datos disponibles.")
    else:
        filtro_tipo = st.multiselect("Filtrar por Tipo", df_disponible['Tipo'].unique())
        df_view = df_disponible if not filtro_tipo else df_disponible[df_disponible['Tipo'].isin(filtro_tipo)]
        
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
                        nueva_solicitud = {
                            "id_solicitud": len(st.session_state.solicitudes) + 1,
                            "fecha": datetime.now().strftime("%H:%M:%S"),
                            "solicitante": solicitante,
                            "item_id": item_data['ID_Ref'],
                            "item_tipo": item_data['Tipo'],
                            "item_estado": item_data['Estado'],
                            "notas": notas,
                            "status": "Pendiente"
                        }
                        st.session_state.solicitudes.append(nueva_solicitud)
                        st.toast("Solicitud enviada al administrador", icon="✅")
                        st.balloons()

# ==========================================
#  VISTA 2: ADMIN (MEJORADA)
# ==========================================
elif rol == "🛡️ Admin (Encargado)":
    st.title("🛡️ Centro de Aprobaciones")
    
    pendientes = [s for s in st.session_state.solicitudes if s['status'] == 'Pendiente']
    
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("Solicitudes Pendientes", len(pendientes))
    col_metric2.metric("Items Entregados (Sesión)", len(st.session_state.stock_reservado))
    
    st.divider()

    if not pendientes:
        st.info("🎉 No hay solicitudes pendientes. Todo al día.")
    else:
        st.write("### Bandeja de Entrada")
        
        for i, sol in enumerate(pendientes):
            # Usamos un container para agrupar visualmente la tarjeta
            with st.container(border=True):
                # Encabezado de la tarjeta
                st.markdown(f"#### 📌 Solicitud #{sol['id_solicitud']} | {sol['item_tipo']}")
                
                # División en 3 columnas para mostrar la info detallada
                col_datos, col_notas, col_botones = st.columns([2, 2, 1])
                
                with col_datos:
                    st.caption("👤 DATOS DEL SOLICITANTE")
                    st.write(f"**Nombre:** {sol['solicitante']}")
                    st.write(f"**Hora:** {sol['fecha']}")
                    st.divider()
                    st.caption("📦 DATOS DEL REPUESTO")
                    # Usamos markdown para resaltar el estado
                    st.markdown(f"Estado: **:orange[{sol['item_estado']}]**")
                    st.markdown(f"ID Interno: `{sol['item_id']}`")

                with col_notas:
                    st.caption("📝 MOTIVO / NOTAS")
                    # Mostramos la nota en un recuadro de info para que destaque
                    nota_texto = sol['notas'] if sol['notas'] else "Sin notas adicionales."
                    st.info(nota_texto)

                with col_botones:
                    st.write("") # Espacio vertical para alinear
                    st.write("") 
                    # Botones grandes
                    if st.button("✅ Aprobar", key=f"btn_acc_{i}", use_container_width=True, type="primary"):
                        sol['status'] = 'Aprobada'
                        st.session_state.stock_reservado.append(sol['item_id'])
                        st.rerun()
                    
                    if st.button("❌ Rechazar", key=f"btn_rej_{i}", use_container_width=True):
                        sol['status'] = 'Rechazada'
                        st.rerun()

    # Historial de decisiones
    st.divider()
    with st.expander("Ver Historial Completo"):
        historial = pd.DataFrame(st.session_state.solicitudes)
        if not historial.empty:
            # Reordenamos columnas para que sea más legible
            columnas_orden = ['id_solicitud', 'status', 'solicitante', 'item_tipo', 'item_estado', 'notas', 'fecha']
            # Filtramos solo las columnas que existen en el DF (por si acaso)
            cols_existentes = [c for c in columnas_orden if c in historial.columns]
            st.dataframe(historial[cols_existentes], use_container_width=True, hide_index=True)
        else:
            st.text("Sin historial.")


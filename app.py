import streamlit as st
import pandas as pd
import requests
import io
import time
from datetime import datetime

# Configuración básica de la página
st.set_page_config(page_title="Gestión Stock & Solicitudes", layout="wide")

# --- 1. GESTIÓN DE ESTADO (MEMORIA) ---
if 'solicitudes' not in st.session_state:
    st.session_state.solicitudes = []
if 'stock_reservado' not in st.session_state:
    st.session_state.stock_reservado = []
if 'total_filas_anterior' not in st.session_state:
    st.session_state.total_filas_anterior = 0

# --- 2. CARGA DE DATOS Y NORMALIZACIÓN DE COLUMNAS ---
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
        
        # Eliminamos espacios en blanco al principio/final de los nombres de columna del Excel
        df.columns = df.columns.str.strip()
        
        # --- MAPEO DE COLUMNAS EXACTO ---
        # Izquierda: Posibles nombres en el Excel -> Derecha: Tu nombre estandarizado
        mapa_columnas = {
            # Serial
            'SN Repuesto': 'SN Repuesto',
            'Serial': 'SN Repuesto',
            'S/N': 'SN Repuesto',
            'SN': 'SN Repuesto',
            
            # ID
            'ID Producto': 'ID Producto',
            'Producto': 'ID Producto',
            'ID': 'ID Producto',
            
            # Descripción
            'Descripción de Producto': 'Descripción de Producto',
            'Descripcion': 'Descripción de Producto',
            'Descripción': 'Descripción de Producto',
            
            # Tipo
            'Tipo': 'Tipo',
            'Pieza': 'Tipo',
            'Parte': 'Tipo',
            'Pieza/Parte': 'Tipo',
            
            # Estado
            'Estado': 'Estado',
            'Condición': 'Estado',
            'Condicion': 'Estado',
            
            # Observación
            'Observación del estado': 'Observación del estado',
            'Observación': 'Observación del estado',
            'Observaciones': 'Observación del estado',
            'Notas': 'Observación del estado'
        }
        
        # Aplicamos el renombre
        df.rename(columns=mapa_columnas, inplace=True)
        
        # Creamos un ID Único de Sistema para identificar la fila (independiente del ID Producto)
        df['SYS_ID'] = df.index 

        # Aseguramos que existan las columnas clave (rellenamos con guion si faltan)
        cols_clave = ['SN Repuesto', 'ID Producto', 'Descripción de Producto', 'Tipo', 'Estado', 'Observación del estado']
        for col in cols_clave:
            if col not in df.columns:
                df[col] = '-' 
        
        # Limpieza visual de nulos
        df.fillna('', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"⚠️ Error al procesar datos: {e}")
        return None

df_raw = cargar_datos()

# Filtro: Ocultar items que ya han sido aprobados por el Admin
if df_raw is not None:
    df_disponible = df_raw[~df_raw['SYS_ID'].isin(st.session_state.stock_reservado)].copy()
else:
    df_disponible = pd.DataFrame()

# --- PANEL LATERAL DE NAVEGACIÓN ---
st.sidebar.title("🔧 Panel de Control")
rol = st.sidebar.radio("Seleccione Perfil:", ["👤 Usuario (Solicitante)", "🛡️ Admin (Encargado)"])
st.sidebar.divider()

# ==========================================
#  VISTA 1: USUARIO (SOLO COLUMNAS CLAVE)
# ==========================================
if rol == "👤 Usuario (Solicitante)":
    st.title("📦 Catálogo de Repuestos")
    st.caption("Seleccione un ítem para solicitarlo.")

    if df_disponible.empty:
        st.warning("No hay datos disponibles.")
    else:
        # Filtro por Tipo
        tipos_disponibles = df_disponible['Tipo'].unique()
        filtro_tipo = st.multiselect("Filtrar por Tipo", tipos_disponibles)
        
        df_filtrado = df_disponible if not filtro_tipo else df_disponible[df_disponible['Tipo'].isin(filtro_tipo)]
        
        # --- DEFINICIÓN DE COLUMNAS A MOSTRAR ---
        # Solo las 6 que pediste
        cols_usuario = ['SN Repuesto', 'ID Producto', 'Descripción de Producto', 'Tipo', 'Estado', 'Observación del estado']
        
        # Creamos una "vista" recortada para la tabla
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
            
            # RECUPERAMOS LA FILA COMPLETA (Con columnas ocultas) usando el índice original
            fila_completa = df_filtrado.iloc[idx_visual]
            
            st.divider()
            with st.container(border=True):
                st.subheader("📝 Confirmar Solicitud")
                
                # Resumen visual de lo seleccionado
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Tipo:** {fila_completa['Tipo']}")
                c2.markdown(f"**SN:** `{fila_completa['SN Repuesto']}`")
                c3.markdown(f"**Estado:** {fila_completa['Estado']}")
                
                st.markdown(f"**Producto:** {fila_completa['Descripción de Producto']} (ID: {fila_completa['ID Producto']})")
                
                # Formulario
                nombre = st.text_input("Tu Nombre:", placeholder="Ej. Juan Pérez")
                notas = st.text_area("Notas adicionales (Opcional):")
                
                if st.button("Enviar Solicitud 🚀", type="primary"):
                    if not nombre:
                        st.error("⚠️ Falta tu nombre.")
                    else:
                        # Guardamos la solicitud
                        nueva_solicitud = {
                            "id_solicitud": len(st.session_state.solicitudes) + 1,
                            "fecha": datetime.now().strftime("%d/%m %H:%M"),
                            "solicitante": nombre,
                            "sys_id": fila_completa['SYS_ID'], 
                            # Resumen rápido para la tarjeta
                            "resumen": f"{fila_completa['Tipo']} - {fila_completa['Descripción de Producto']}",
                            "estado_item": fila_completa['Estado'],
                            "notas_usuario": notas,
                            # GUARDAMOS TODO EL REGISTRO ORIGINAL PARA EL ADMIN
                            "datos_full": fila_completa.to_dict(), 
                            "status": "Pendiente"
                        }
                        st.session_state.solicitudes.append(nueva_solicitud)
                        st.toast("Solicitud enviada exitosamente", icon="✅")
                        st.balloons()
                        # Opcional: limpiar selección tras enviar (requiere rerun)
                        time.sleep(1)
                        st.rerun()

# ==========================================
#  VISTA 2: ADMIN (ACCESO TOTAL)
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
            data_item = sol['datos_full'] # Aquí está el diccionario con TODAS las columnas
            
            with st.container(border=True):
                # Encabezado de la Tarjeta
                st.markdown(f"#### 📌 Solicitud #{sol['id_solicitud']} | {sol['resumen']}")
                
                col_info, col_notes, col_btns = st.columns([2, 2, 1])
                
                with col_info:
                    st.caption("DATOS BASICOS")
                    st.write(f"👤 **Solicitante:** {sol['solicitante']}")
                    st.write(f"🕒 **Fecha:** {sol['fecha']}")
                    st.markdown(f"📦 **Estado Item:** :orange[{sol['estado_item']}]")

                with col_notes:
                    st.caption("NOTAS DEL USUARIO")
                    if sol['notas_usuario']:
                        st.info(sol['notas_usuario'])
                    else:
                        st.text("Sin notas.")

                with col_btns:
                    st.write("") # Espaciador
                    if st.button("✅ Aprobar", key=f"ok_{i}", type="primary", use_container_width=True):
                        sol['status'] = 'Aprobada'
                        st.session_state.stock_reservado.append(sol['sys_id'])
                        st.rerun()
                    
                    if st.button("❌ Rechazar", key=f"no_{i}", use_container_width=True):
                        sol['status'] = 'Rechazada'
                        st.rerun()
                
                # --- FICHA TÉCNICA COMPLETA ---
                # Aquí mostramos TODOS los campos del Excel original
                with st.expander("🔍 Ver Ficha Técnica Completa (Ubicación, Precios, etc.)"):
                    # Convertimos el diccionario a DataFrame para mostrarlo verticalmente
                    df_detalle = pd.DataFrame.from_dict(data_item, orient='index', columns=['Valor Detallado'])
                    st.dataframe(df_detalle, use_container_width=True)

    # Historial
    if st.checkbox("Ver Historial de Decisiones"):
        st.write("Historial de la sesión actual:")
        st.dataframe(pd.DataFrame(st.session_state.solicitudes))


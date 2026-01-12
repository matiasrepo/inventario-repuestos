import streamlit as st
import pandas as pd


@st.cache_data
def cargar_datos():
    # Enlace modificado para descarga directa
    url_sharepoint = "https://compragamer-my.sharepoint.com/personal/mnunez_compragamer_net/_layouts/15/download.aspx?sourcedoc={39bca3d7-c1a4-4137-b73c-9a50cc5ee654}"

    try:
        # Intentamos leer directamente desde SharePoint
        df = pd.read_excel(url_sharepoint)

        # --- (Aquí va el resto de tu limpieza de datos igual que antes) ---
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        mapa_columnas = {
            'Pieza /Parte': 'Tipo',
            'Estado Condición': 'Estado',
            'Descripción De Producto': 'Descripcion',
            'ID Repuesto': 'ID',
            'SN Repuesto': 'Serial',
            'Disponible': 'Disponible'
        }
        df = df.rename(columns={k: v for k, v in mapa_columnas.items() if k in df.columns})
        df = df.fillna("-")
        return df

    except Exception as e:
        st.error(f"⚠️ Error de acceso: {e}")
        st.info("Es muy probable que SharePoint esté bloqueando a Python porque requiere usuario y contraseña.")
        return None


# ... resto del código ...


df = cargar_datos()

if df is not None:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")

    # Filtro TIPO
    if 'Tipo' in df.columns:
        tipos_disponibles = sorted(df['Tipo'].astype(str).unique())
        tipos_seleccionados = st.sidebar.multiselect(
            "Filtrar por Tipo:",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    else:
        st.error("No se encontró la columna 'Pieza /Parte' o 'Tipo'. Revisa el Excel.")
        st.stop()

    # Filtro ESTADO
    if 'Estado' in df.columns:
        estados_disponibles = sorted(df['Estado'].astype(str).unique())
        estados_seleccionados = st.sidebar.multiselect(
            "Filtrar por Estado:",
            options=estados_disponibles,
            default=estados_disponibles
        )

    # APLICAR FILTROS
    df_filtrado = df[
        (df['Tipo'].isin(tipos_seleccionados)) &
        (df['Estado'].isin(estados_seleccionados))
        ]

    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filtrados", len(df_filtrado))
    col2.metric("Variedad de Partes", len(df_filtrado['Tipo'].unique()))

    # Ejemplo: Contar cuántos 'A' hay visibles
    conteo_a = len(df_filtrado[df_filtrado['Estado'] == 'A'])
    col3.metric("En Estado 'A'", conteo_a)

    st.divider()

    # --- VISTA PRINCIPAL ---
    tab1, tab2 = st.tabs(["📋 Listado Detallado", "📊 Resumen Gráfico"])

    with tab1:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        if not df_filtrado.empty:
            # Tabla dinámica: Filas=Tipo, Columnas=Estado, Valor=Cantidad
            resumen = df_filtrado.groupby(['Tipo', 'Estado']).size().unstack(fill_value=0)
            st.write("Cantidad de repuestos por Estado y Tipo:")
            st.dataframe(resumen, use_container_width=True)
            st.bar_chart(resumen)
        else:
            st.warning("No hay datos para mostrar con estos filtros.")
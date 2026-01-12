import streamlit as st
import pandas as pd

# 1. Tu enlace original
original_url = "https://compragamer-my.sharepoint.com/:x:/g/personal/mnunez_compragamer_net/IQDXo7w5pME3Qbc8mlDMXuZUAeYwlVbk5qJnCM3NB3oM6qA?e=TSeVya"

# 2. Modificamos el link para que sea de descarga directa
# Reemplazamos lo que está después del '?' por 'download=1'
download_url = original_url.split('?')[0] + '?download=1'

try:
    # 3. Leemos el excel
    df = pd.read_excel(download_url)
    
    # Mostrar las primeras filas para verificar
    print("Archivo cargado exitosamente:")
    print(df.head())

except Exception as e:
    print(f"Hubo un error al leer el archivo: {e}")
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

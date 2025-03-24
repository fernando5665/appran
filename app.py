import streamlit as st
import pandas as pd
import re

# Función para extraer el site_id del site_name
def extraer_site_id(site_name):
    match = re.search(r"SF(\d+)[A-Z]+\d+", site_name)
    return match.group(1) if match else None

# Función para cargar bases de datos
@st.cache_data
def cargar_datos(archivo, tipo):
    try:
        df = pd.read_excel(archivo, engine="openpyxl")
        
        if tipo == "base":
            if "site_id" not in df.columns or "region" not in df.columns:
                st.error("⚠️ El archivo base no contiene las columnas necesarias ('site_id', 'region').")
                return None
            df["site_id"] = df["site_id"].astype(str)

        elif tipo == "afectados":
            if "site_name" not in df.columns:
                st.error("⚠️ El archivo no contiene la columna 'site_name'.")
                return None
            df["site_name"] = df["site_name"].astype(str).str.replace('"', '')
            df["site_id"] = df["site_name"].apply(extraer_site_id)
            df["site_id"] = df["site_id"].astype(str)

        elif tipo == "rectificadores":
            if "site_id" not in df.columns:
                st.error("⚠️ El archivo de rectificadores no contiene 'site_id'.")
                return None
            df["site_id"] = df["site_id"].astype(str)

        return df
    except Exception as e:
        st.error(f"❌ Error al leer el archivo ({tipo}): {e}")
        return None

# Función para buscar sitios manualmente
def buscar_sites_por_id(df, site_ids):
    site_ids = [site.strip() for site in re.split(r"[,\s]+", site_ids) if site.strip()]
    df_result = df[df["site_id"].isin(site_ids)]
    return df_result.sort_values(by="region") if "region" in df_result.columns else df_result

# Configurar la aplicación
st.set_page_config(page_title="Análisis de Energía", layout="wide")

# Inicializar session_state para almacenar los DataFrames
if "df_base" not in st.session_state:
    st.session_state.df_base = None
if "df_afectados" not in st.session_state:
    st.session_state.df_afectados = None
if "df_rectificadores" not in st.session_state:
    st.session_state.df_rectificadores = None

# Menú de navegación
menu = st.sidebar.radio("🔍 Navegación", ["Análisis de Masivas", "Búsqueda Manual", "Rectificadores"])

# -------------------------- VISTA: Análisis de Masivas --------------------------
if menu == "Análisis de Masivas":
    st.title("📊 Análisis de Sitios Afectados por Energía")
    
    archivo_base = st.file_uploader("📂 Sube el archivo base (Excel)", type="xlsx", key="base_masiva")
    archivo_afectados_1 = st.file_uploader("📂 Sube el primer archivo con sitios afectados (Excel)", type="xlsx")
    archivo_afectados_2 = st.file_uploader("📂 Sube el segundo archivo con sitios afectados (Opcional) (Excel)", type="xlsx")

    # Cargar archivos en session_state
    if archivo_base:
        st.session_state.df_base = cargar_datos(archivo_base, "base")
    if archivo_afectados_1:
        st.session_state.df_afectados = cargar_datos(archivo_afectados_1, "afectados")
    if archivo_afectados_2:
        df_afectados_2 = cargar_datos(archivo_afectados_2, "afectados")
        if df_afectados_2 is not None:
            st.session_state.df_afectados = pd.concat([st.session_state.df_afectados, df_afectados_2], ignore_index=True)

    if st.session_state.df_base is not None and st.session_state.df_afectados is not None:
        st.success("✅ Archivos cargados correctamente.")

        # Unir con la base de datos
        df_merged = st.session_state.df_afectados.merge(st.session_state.df_base, on="site_id", how="left")

        # Verificar si hay coincidencias
        if df_merged["region"].isna().all():
            st.warning("⚠️ No se encontraron coincidencias en la base de datos.")
        else:
            df_merged = df_merged.sort_values(by="region")
            resumen = df_merged.groupby("region").size().reset_index(name="cantidad_sitios")

            st.write("### 📌 Resumen de sitios afectados por región")
            st.dataframe(resumen)
            st.bar_chart(resumen.set_index("region"))

            st.write("### 📋 Información Detallada de Sitios Afectados")
            st.dataframe(df_merged)

# -------------------------- VISTA: Búsqueda Manual --------------------------
elif menu == "Búsqueda Manual":
    st.title("🔍 Buscar Sitios Manualmente")

    archivo_base = st.file_uploader("📂 Sube el archivo base (Excel)", type="xlsx", key="base_busqueda")

    if archivo_base:
        st.session_state.df_base = cargar_datos(archivo_base, "base")

    if st.session_state.df_base is not None:
        st.success("✅ Base de datos cargada correctamente.")
        site_ids_input = st.text_input("✍️ Ingresa los Site IDs separados por coma o espacio:")

        if st.button("🔎 Buscar"):
            if site_ids_input:
                df_result = buscar_sites_por_id(st.session_state.df_base, site_ids_input)
                if not df_result.empty:
                    st.write("### 📋 Información de Sitios Encontrados")
                    st.dataframe(df_result)
                else:
                    st.warning("⚠️ No se encontraron sitios con esos IDs.")
            else:
                st.error("⚠️ Ingresa al menos un Site ID.")

# -------------------------- VISTA: Rectificadores --------------------------
elif menu == "Rectificadores":
    st.title("🔌 Verificar Respaldo de Sitios (Rectificadores)")

    archivo_rectificadores = st.file_uploader("📂 Sube el archivo de rectificadores (Excel)", type="xlsx")

    if archivo_rectificadores:
        st.session_state.df_rectificadores = cargar_datos(archivo_rectificadores, "rectificadores")

    if st.session_state.df_rectificadores is not None:
        st.success("✅ Base de rectificadores cargada correctamente.")

        site_ids_input = st.text_input("✍️ Ingresa los Site IDs separados por coma o espacio:")

        if st.button("🔎 Buscar"):
            if site_ids_input:
                df_result = buscar_sites_por_id(st.session_state.df_rectificadores, site_ids_input)
                if not df_result.empty:
                    st.write("### 🔋 Información de Respaldo de Sitios")
                    st.dataframe(df_result)
                else:
                    st.warning("⚠️ No se encontraron sitios con esos IDs.")
            else:
                st.error("⚠️ Ingresa al menos un Site ID.")

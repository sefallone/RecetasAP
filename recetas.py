import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import hashlib
import time

# Configuración de la página
st.set_page_config(
    page_title="📚 RECETAS ARTE PARÍS",
    page_icon="🍞",
    layout="wide"
)

# --- Sistema de Autenticación ---
# Sistema de autenticación mejorado
def check_password():
    """Verificación de credenciales con hash SHA-256"""
    
    # Mostrar advertencia si no hay secrets configurados
    if "password" not in st.secrets:
        st.error("⚠️ Error de configuración: No se encontró contraseña en secrets.toml")
        st.info("Por favor configura el archivo .streamlit/secrets.toml")
        return False
    
    def password_entered():
        # Convertir ambas contraseñas a hash para comparación segura
        input_hash = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
        correct_hash = hashlib.sha256(st.secrets["password"].encode()).hexdigest()
        
        if input_hash == correct_hash:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Limpiar contraseña de memoria
        else:
            st.session_state["password_correct"] = False
            time.sleep(1)  # Retraso para prevenir ataques de fuerza bruta

    # Mostrar input de contraseña
    if "password_correct" not in st.session_state:
        st.text_input(
            "Contraseña de acceso",
            type="password",
            on_change=password_entered,
            key="password",
            help="Contacta al administrador si no conoces la contraseña"
        )
        return False
    
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Contraseña de acceso",
            type="password",
            on_change=password_entered,
            key="password",
            help="Intenta nuevamente o contacta al administrador"
        )
        st.error("Acceso denegado. Contraseña incorrecta.")
        return False
    
    return True  # Autenticación exitosa
# Verificar autenticación antes de mostrar la app
if not check_password():
    st.stop()  # No continuar si no está autenticado

# --- Título principal (solo visible si está autenticado) ---
st.title("📚 Recetas Arte París")
st.write(f"Bienvenido, {st.secrets.get('user', 'Usuario')}")

# --- URL del archivo Excel en GitHub (formato RAW) ---
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/sefallone/RecetasAP/main/Recetario_AP_app.xlsx"

# --- Descargar el archivo desde GitHub ---
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_excel_from_github():
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()  # Verifica errores HTTP
        return BytesIO(response.content)  # Convierte a BytesIO para pandas
    except Exception as e:
        st.error(f"❌ Error al descargar el archivo: {str(e)}")
        return None

excel_file = get_excel_from_github()

if excel_file is None:
    st.stop()

# --- Obtener nombres de hojas (recetas) ---
@st.cache_data
def get_recipe_names(file):
    try:
        xls = pd.ExcelFile(file)
        return xls.sheet_names
    except Exception as e:
        st.error(f"Error al leer el archivo: {str(e)}")
        return []

recipe_names = get_recipe_names(excel_file)

if not recipe_names:
    st.error("El archivo no contiene hojas válidas")
    st.stop()

# --- Sidebar: Selección de receta ---
st.sidebar.title("📑 Índice de Recetas")
selected_recipe = st.sidebar.selectbox(
    "Selecciona una receta:",
    options=recipe_names
)

# --- Cargar la receta seleccionada ---
@st.cache_data
def load_recipe(file, sheet_name):
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        df = df.dropna(how='all')  # Limpieza básica
        return df
    except Exception as e:
        st.error(f"Error al cargar la hoja '{sheet_name}': {str(e)}")
        return None

recipe_df = load_recipe(excel_file, selected_recipe)

if recipe_df is None:
    st.stop()

# --- Mostrar la receta ---
st.header(f"📋 {selected_recipe}")

# Verificación del formato
required_columns = {'Nombre Producto', 'Gramos por Producto', 'Cantidad', 'Materia Prima', 'GRAMOS'}
if not required_columns.issubset(recipe_df.columns):
    st.warning("""
    ⚠️ El formato de la hoja no coincide con lo esperado.
    Asegúrate de que tenga estas columnas:
    - Nombre Producto
    - Gramos por Producto
    - Cantidad
    - Materia Prima
    - GRAMOS
    """)
    st.write("Vista previa de los datos cargados:")
    st.dataframe(recipe_df)
else:
    # Extraer metadatos
    metadata = recipe_df.iloc[0]
    
    # Mostrar métricas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Peso por unidad (g)", metadata["Gramos por Producto"])
    with col2:
        st.metric("Unidades por lote", metadata["Cantidad"])
    
    # --- Tabla de ingredientes ---
    st.subheader("🧾 Formulación")
    
    ingredientes_df = recipe_df[['Materia Prima', 'GRAMOS']].dropna()
    total_gramos = ingredientes_df['GRAMOS'].sum()
    ingredientes_df['% Composición'] = (ingredientes_df['GRAMOS'] / total_gramos) * 100
    
    st.dataframe(
        ingredientes_df.style.format({'% Composición': '{:.2f}%'}),
        use_container_width=True,
        hide_index=True
    )
    
    # --- Gráfico de composición ---
    st.subheader("📊 Distribución de Ingredientes")
    st.bar_chart(ingredientes_df.set_index('Materia Prima')['% Composición'])
    
    # --- Calculadora de producción ---
    st.subheader("🧮 Escalar Receta")
    unidades_deseadas = st.number_input(
        "Unidades a producir:",
        min_value=1,
        value=int(metadata["Cantidad"])
    )
    
    factor = unidades_deseadas / metadata["Cantidad"]
    ingredientes_df['Gramos necesarios'] = ingredientes_df['GRAMOS'] * factor
    
    st.dataframe(
        ingredientes_df[['Materia Prima', 'Gramos necesarios']],
        hide_index=True
    )

# --- Exportar receta ---
st.sidebar.markdown("---")
if st.sidebar.button("💾 Exportar esta receta"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        recipe_df.to_excel(writer, sheet_name=selected_recipe, index=False)
    
    st.sidebar.download_button(
        label="Descargar como Excel",
        data=output.getvalue(),
        file_name=f"receta_{selected_recipe}.xlsx",
        mime="application/vnd.ms-excel"
    )

# Créditos
st.sidebar.markdown("---")
st.sidebar.caption("© Arte París - Sistema de Gestión de Recetas")

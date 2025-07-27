import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="📚 Libro de Recetas por Hojas",
    page_icon="🍞",
    layout="wide"
)

# Título principal
st.title("📚 Libro de Recetas Industriales")

# --- Cargar archivo Excel ---
uploaded_file = st.file_uploader("Sube tu libro de recetas (Excel)", type=["xlsx"])

if not uploaded_file:
    st.info("Por favor, sube tu archivo Excel donde cada hoja es una receta")
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

recipe_names = get_recipe_names(uploaded_file)

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
        
        # Limpieza básica (eliminar filas totalmente vacías)
        df = df.dropna(how='all')
        
        return df
    except Exception as e:
        st.error(f"Error al cargar la hoja '{sheet_name}': {str(e)}")
        return None

recipe_df = load_recipe(uploaded_file, selected_recipe)

if recipe_df is None:
    st.stop()

# --- Mostrar la receta ---
st.header(f"📋 {selected_recipe}")

# Verificamos si el DataFrame tiene el formato esperado
if not {'Nombre Producto', 'Gramos por Producto', 'Cantidad de producto', 'Materia Prima', 'GRAMOS'}.issubset(recipe_df.columns):
    st.warning("""
    ⚠️ El formato de la hoja no coincide con lo esperado.
    Asegúrate de que tenga estas columnas:
    - Nombre Producto
    - Gramos por Producto
    - Cantidad de Producto
    - Materia Prima
    - GRAMOS
    """)
    st.write("Vista previa de los datos cargados:")
    st.dataframe(recipe_df)
else:
    # Extraemos metadatos (primera fila válida)
    metadata = recipe_df.iloc[0]
    
    # Columnas de especificaciones
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Peso por unidad (g)", metadata["Gramos por cachito"])
    with col2:
        st.metric("Unidades por lote", metadata["Cantidad de Cachitos"])
    
    # --- Tabla de ingredientes ---
    st.subheader("🧾 Formulación")
    
    # Filtramos solo las filas con ingredientes (omitimos metadatos si existen)
    ingredientes_df = recipe_df[['Materia Prima', 'GRAMOS']].dropna()
    
    # Calculamos porcentajes
    total_gramos = ingredientes_df['GRAMOS'].sum()
    ingredientes_df['% Composición'] = (ingredientes_df['GRAMOS'] / total_gramos) * 100
    
    # Mostramos tabla
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
        value=int(metadata["Cantidad de Cachitos"])
    )
    
    factor = unidades_deseadas / metadata["Cantidad de Cachitos"]
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


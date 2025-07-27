import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="📊 Gestor de Recetas",
    page_icon="🍽️",
    layout="wide"
)

# Título principal
st.title("🍽️ Libro de Recetas Industriales")

# --- Cargar datos (Ejemplo con DataFrame) ---
@st.cache_data
def load_recipes():
    # Ejemplo con TU formato (simula tus datos)
    data = {
        "Nombre Producto": ["Pan Integral", "Galletas de Avena"],
        "Gramos por producto": [500, 200],
        "Unidades del producto": [1, 12],
        "Materia Prima": [
            ["Harina integral", "Agua", "Levadura", "Sal"],
            ["Avena", "Mantequilla", "Huevos", "Azúcar"]
        ],
        "Gramos": [
            [300, 150, 10, 5],
            [100, 50, 2, 30]
        ]
    }
    return pd.DataFrame(data)

df_recetas = load_recipes()

# --- Sidebar: Selección de producto ---
st.sidebar.title("Índice de Productos")
selected_product = st.sidebar.selectbox(
    "Selecciona un producto:",
    options=df_recetas["Nombre Producto"]
)

# --- Filtramos los datos del producto seleccionado ---
product_data = df_recetas[df_recetas["Nombre Producto"] == selected_product].iloc[0]

# --- Mostrar detalles de la receta ---
st.header(f"📋 {selected_product}")
st.subheader("📊 Especificaciones Técnicas")

# Columnas para metadata
col1, col2 = st.columns(2)
with col1:
    st.metric("Peso unitario (g)", product_data["Gramos por producto"])
with col2:
    st.metric("Unidades por lote", product_data["Unidades del producto"])

# --- Tabla de ingredientes ---
st.subheader("🧾 Formulación")
df_ingredientes = pd.DataFrame({
    "Materia Prima": product_data["Materia Prima"],
    "Gramos": product_data["Gramos"]
})
st.dataframe(df_ingredientes, hide_index=True)

# --- Cálculo de porcentajes ---
st.subheader("📈 Composición (%)")
df_ingredientes["Porcentaje"] = (df_ingredientes["Gramos"] / df_ingredientes["Gramos"].sum()) * 100
st.bar_chart(df_ingredientes.set_index("Materia Prima")["Porcentaje"])

# --- Exportar receta ---
st.sidebar.markdown("---")
if st.sidebar.button("📤 Exportar Receta"):
    csv = df_ingredientes.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"receta_{selected_product}.csv",
        mime="text/csv"
    )

# --- Cómo cargar tus archivos REALES ---
st.sidebar.markdown("""
### 🛠️ Cómo usar tus datos
1. Prepara un Excel con estas columnas:
   - `Nombre Producto`
   - `Gramos por producto`
   - `Unidades del producto`
   - `Materia Prima` (lista de ingredientes)
   - `Gramos` (lista de pesos)
2. Reemplaza `load_recipes()` con:
```python""")
def load_recipes():
    return pd.read_excel("tus_recetas.xlsx")

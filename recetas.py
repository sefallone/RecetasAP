import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="🧀 Sistema de Recetas - Cachitos",
    page_icon="🥐",
    layout="wide"
)

# Título principal
st.title("🧀 Libro de Recetas - Formulación de Cachitos")

# --- Cargar datos DESDE TU ARCHIVO ---
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        
        # Procesamiento especial para tu formato
        df['Nombre Producto'] = df['Nombre Producto'].ffill()  # Rellena los valores vacíos
        df = df.dropna(subset=['Materia Prima'])  # Elimina filas vacías
        
        # Agrupar por producto
        grouped = df.groupby('Nombre Producto').agg({
            'Gramos por cachito': 'first',
            'Cantidad de Cachitos': 'first',
            'Materia Prima': list,
            'GRAMOS': list
        }).reset_index()
        
        return grouped
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

# --- Interfaz para subir archivo ---
uploaded_file = st.file_uploader("📤 Sube tu archivo de recetas (Excel)", type=["xlsx"])

if not uploaded_file:
    st.info("Por favor, sube tu archivo Excel con el formato de recetas")
    st.stop()

df_recetas = load_data(uploaded_file)

if df_recetas is None:
    st.error("El archivo no tiene el formato correcto. Verifica las columnas.")
    st.stop()

# --- Sidebar: Selección de producto ---
st.sidebar.title("🥐 Productos Disponibles")
selected_product = st.sidebar.selectbox(
    "Selecciona un producto:",
    options=df_recetas["Nombre Producto"]
)

# --- Obtener datos del producto seleccionado ---
product_data = df_recetas[df_recetas["Nombre Producto"] == selected_product].iloc[0]

# --- Mostrar ficha técnica ---
st.header(f"📋 Formulación: {selected_product}")

# Columnas de especificaciones
col1, col2 = st.columns(2)
with col1:
    st.metric("Peso por unidad (g)", product_data["Gramos por cachito"])
with col2:
    st.metric("Unidades por lote", product_data["Cantidad de Cachitos"])

# --- Tabla de formulación ---
st.subheader("🧾 Ingredientes por Lote")
df_formulacion = pd.DataFrame({
    'Materia Prima': product_data["Materia Prima"],
    'Gramos': product_data["GRAMOS"],
    '% Composición': [round(g/sum(product_data["GRAMOS"])*100, 2) for g in product_data["GRAMOS"]]
})

# Formatear la tabla
st.dataframe(
    df_formulacion.style.format({'% Composición': '{:.2f}%'}),
    use_container_width=True,
    hide_index=True
)

# --- Gráfico de composición ---
st.subheader("📊 Distribución de Ingredientes")
st.bar_chart(df_formulacion.set_index('Materia Prima')['% Composición'])

# --- Cálculo de costos (opcional) ---
if st.checkbox("🧮 Calcular cantidades para producción"):
    unidades_deseadas = st.number_input(
        f"Unidades de {selected_product} a producir",
        min_value=1,
        value=product_data["Cantidad de Cachitos"]
    )
    
    factor = unidades_deseadas / product_data["Cantidad de Cachitos"]
    
    df_calculo = df_formulacion.copy()
    df_calculo['Gramos necesarios'] = df_calculo['Gramos'] * factor
    
    st.write(f"### 📝 Ingredientes para {unidades_deseadas} unidades")
    st.dataframe(
        df_calculo[['Materia Prima', 'Gramos necesarios']],
        hide_index=True
    )

# --- Exportar receta ---
st.sidebar.markdown("---")
if st.sidebar.button("💾 Exportar esta receta"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_formulacion.to_excel(writer, sheet_name=selected_product, index=False)
    
    st.sidebar.download_button(
        label="Descargar Excel",
        data=output.getvalue(),
        file_name=f"receta_{selected_product}.xlsx",
        mime="application/vnd.ms-excel"
    )

# --- Instrucciones ---
st.sidebar.markdown("""
### 📌 Instrucciones:
1. Sube tu archivo Excel con el formato:
   - Columnas: `Nombre Producto`, `Gramos por cachito`, `Cantidad de Cachitos`, `Materia Prima`, `GRAMOS`
2. Los productos se agruparán automáticamente
3. Selecciona un producto para ver su formulación
""")

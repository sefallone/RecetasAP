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

# --- Sistema de Autenticación Multi-Usuario ---
import streamlit as st
import hashlib
import time

def check_multi_user_auth():
    """
    Sistema de autenticación multi-usuario que verifica credenciales contra secrets.toml
    Devuelve True si la autenticación es exitosa, False en caso contrario
    """
    
    # Cargar usuarios válidos desde secrets.toml
    try:
        VALID_USERS = st.secrets["users"]
    except (KeyError, AttributeError):
        st.error("Error de configuración: No se encontraron usuarios en secrets.toml")
        st.stop()
    
    # Función para verificar credenciales
    def authenticate():
        username = st.session_state.get("auth_username", "").strip()
        password_attempt = st.session_state.get("auth_password", "")
        
        if username in VALID_USERS:
            # Comparación segura con hash SHA-256
            input_hash = hashlib.sha256(password_attempt.encode()).hexdigest()
            stored_hash = hashlib.sha256(VALID_USERS[username].encode()).hexdigest()
            
            if input_hash == stored_hash:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                del st.session_state["auth_password"]  # Limpiar contraseña de memoria
                return True
        
        st.session_state["authenticated"] = False
        time.sleep(1)  # Pequeño delay para seguridad
        return False

    # Mostrar formulario de login si no está autenticado
    if not st.session_state.get("authenticated", False):
        st.subheader("Acceso al Sistema de Recetas")
        
        with st.form("auth_form", clear_on_submit=True):
            st.text_input("Usuario", key="auth_username", help="Ingrese su nombre de usuario")
            st.text_input("Contraseña", type="password", key="auth_password", help="Ingrese su contraseña")
            
            if st.form_submit_button("Iniciar Sesión"):
                if authenticate():
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no válido")
        
        # Mensaje para usuarios nuevos
        st.markdown("""
        <div style="margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;">
            <small>¿Problemas para acceder? Contacte al administrador del sistema.</small>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    # Mostrar interfaz de usuario autenticado
    st.sidebar.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <small>Sesión iniciada como:</small><br>
        <strong>{st.session_state.current_user}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🔒 Cerrar sesión", type="primary"):
        st.session_state.clear()
        st.rerun()
    
    return True

# Verificar autenticación antes de continuar
if not check_multi_user_auth():
    st.stop()

# --- Título principal (visible solo para autenticados) ---
st.title("📚 Recetas Arte París")
st.write(f"Bienvenido/a, {st.session_state.current_user}")

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

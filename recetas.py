import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import hashlib
import time
import base64

# Configuración de la página
st.set_page_config(
    page_title="📚 Sistema de Recetas Arte París",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS personalizados ---
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .recipe-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .favorite-btn {
        background-color: #ffd700 !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Sistema de Autenticación Mejorado ---
def check_multi_user_auth():
    """Verifica las credenciales del usuario contra secrets.toml"""
    
    # Cargar usuarios válidos
    try:
        VALID_USERS = st.secrets["users"]
    except (KeyError, AttributeError):
        st.error("Error de configuración: No se encontraron usuarios en secrets.toml")
        st.stop()
    
    def authenticate():
        """Compara credenciales usando hash seguro"""
        username = st.session_state.get("auth_username", "").strip()
        password_attempt = st.session_state.get("auth_password", "")
        
        if username in VALID_USERS:
            input_hash = hashlib.sha256(password_attempt.encode()).hexdigest()
            stored_hash = hashlib.sha256(VALID_USERS[username].encode()).hexdigest()
            
            if input_hash == stored_hash:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                # Inicializar favoritos si no existen
                if "favorites" not in st.session_state:
                    st.session_state.favorites = []
                del st.session_state["auth_password"]
                return True
        
        time.sleep(1)  # Prevención básica contra fuerza bruta
        return False

    # Mostrar formulario de login si no está autenticado
    if not st.session_state.get("authenticated", False):
        st.title("🔐 Acceso al Sistema")
        
        with st.form("auth_form", clear_on_submit=True):
            st.text_input("👤 Usuario", key="auth_username")
            st.text_input("🔒 Contraseña", type="password", key="auth_password")
            
            if st.form_submit_button("🚀 Ingresar", use_container_width=True):
                if authenticate():
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        
        st.markdown("""
        <div style="margin-top:2em; padding:1em; background:#f8f9fa; border-radius:0.5em;">
            <small>¿Problemas para acceder? Contacte al administrador</small>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    # Barra lateral para usuario autenticado
    st.sidebar.markdown(f"""
    <div style="margin-bottom:1em; padding:1em; background:#f0f2f6; border-radius:0.5em;">
        <small>Usuario conectado:</small><br>
        <strong>👤 {st.session_state.current_user}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🔒 Cerrar sesión", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    return True

# --- Verificar autenticación antes de continuar ---
if not check_multi_user_auth():
    st.stop()

# --- URL del archivo Excel en GitHub (formato RAW) ---
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/sefallone/RecetasAP/main/Recetario_AP_app.xlsx"

# --- Descargar el archivo desde GitHub ---
@st.cache_data(ttl=3600, show_spinner="Descargando recetario...")  # Cache por 1 hora
def get_excel_from_github():
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()  # Verifica errores HTTP
        return BytesIO(response.content)  # Convierte a BytesIO para pandas
    except Exception as e:
        st.error(f"❌ Error al descargar el archivo: {str(e)}")
        st.info("ℹ️ Verifique su conexión a Internet y que la URL sea correcta")
        return None

# --- Obtener nombres de hojas (recetas) ---
@st.cache_data(show_spinner="Cargando lista de recetas...")
def get_recipe_names(file):
    try:
        xls = pd.ExcelFile(file)
        return xls.sheet_names
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {str(e)}")
        return []

# --- Cargar la receta seleccionada ---
@st.cache_data(show_spinner="Cargando receta...")
def load_recipe(file, sheet_name):
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        df = df.dropna(how='all')  # Limpieza básica
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar la hoja '{sheet_name}': {str(e)}")
        return None

# --- Descargar y procesar archivo ---
with st.spinner("🔄 Cargando sistema de recetas..."):
    excel_file = get_excel_from_github()

if excel_file is None:
    st.stop()

recipe_names = get_recipe_names(excel_file)

if not recipe_names:
    st.error("❌ El archivo no contiene hojas válidas o no pudo leerse correctamente")
    st.stop()

# --- Sidebar: Selección de receta ---
st.sidebar.title("📑 Índice de Recetas")

# Búsqueda de recetas
search_term = st.sidebar.text_input("🔍 Buscar receta:", "").lower()

# Filtrado de recetas según búsqueda
filtered_recipes = [r for r in recipe_names if search_term in r.lower()] if search_term else recipe_names

# Gestión de favoritos
if "favorites" not in st.session_state:
    st.session_state.favorites = []

favorite_recipes = [r for r in filtered_recipes if r in st.session_state.favorites]
other_recipes = [r for r in filtered_recipes if r not in st.session_state.favorites]

# Mostrar recetas favoritas primero si existen
if favorite_recipes:
    st.sidebar.markdown("**⭐ Favoritos**")
    for recipe in favorite_recipes:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            if st.button(recipe, key=f"fav_{recipe}", use_container_width=True):
                st.session_state.selected_recipe = recipe
                st.rerun()
        with col2:
            if st.button("❌", key=f"remove_{recipe}"):
                st.session_state.favorites.remove(recipe)
                st.rerun()

# Mostrar otras recetas
if other_recipes:
    if favorite_recipes:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📋 Todas las recetas**")
    
    for recipe in other_recipes:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            if st.button(recipe, key=f"rec_{recipe}", use_container_width=True):
                st.session_state.selected_recipe = recipe
                st.rerun()
        with col2:
            if st.button("⭐", key=f"add_{recipe}"):
                st.session_state.favorites.append(recipe)
                st.rerun()

# Si no hay recetas que coincidan con la búsqueda
if not filtered_recipes:
    st.sidebar.warning("No se encontraron recetas que coincidan con la búsqueda")

# Usar la receta seleccionada o la primera por defecto
if "selected_recipe" not in st.session_state:
    st.session_state.selected_recipe = filtered_recipes[0] if filtered_recipes else ""

selected_recipe = st.session_state.selected_recipe

# Cargar la receta seleccionada
recipe_df = load_recipe(excel_file, selected_recipe)

if recipe_df is None:
    st.error(f"❌ No se pudo cargar la receta: {selected_recipe}")
    st.stop()

# --- Título principal (visible solo para autenticados) ---
st.markdown(f'<h1 class="main-header">📚 Recetas Arte París</h1>', unsafe_allow_html=True)
st.write(f"Bienvenido/a, **{st.session_state.current_user}**")

# --- Mostrar la receta ---
st.header(f"📋 {selected_recipe}")

# Botones de acción en la parte superior
col1, col2, col3 = st.columns([2, 2, 1])
with col3:
    if selected_recipe not in st.session_state.favorites:
        if st.button("⭐ Agregar a favoritos", use_container_width=True):
            st.session_state.favorites.append(selected_recipe)
            st.rerun()
    else:
        if st.button("❌ Quitar de favoritos", use_container_width=True):
            st.session_state.favorites.remove(selected_recipe)
            st.rerun()

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
    st.dataframe(recipe_df, use_container_width=True)
else:
    # Extraer metadatos
    metadata = recipe_df.iloc[0]
    
    # Mostrar métricas en tarjetas
    st.subheader("📊 Métricas de la Receta")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card">Peso por unidad<br><h3>{metadata["Gramos por Producto"]} g</h3></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card">Unidades por lote<br><h3>{int(metadata["Cantidad"])}</h3></div>', unsafe_allow_html=True)
    with col3:
        total_gramos = recipe_df['GRAMOS'].sum()
        st.markdown(f'<div class="metric-card">Peso total del lote<br><h3>{total_gramos:.0f} g</h3></div>', unsafe_allow_html=True)
    
    # Crear pestañas para organizar la información
    tab1, tab2, tab3 = st.tabs(["🧾 Formulación", "📊 Composición", "🧮 Calculadora"])
    
    with tab1:
        # Tabla de ingredientes
        st.subheader("🧾 Formulación")
        
        ingredientes_df = recipe_df[['Materia Prima', 'GRAMOS']].dropna()
        total_gramos = ingredientes_df['GRAMOS'].sum()
        ingredientes_df['% Composición'] = (ingredientes_df['GRAMOS'] / total_gramos) * 100
        
        st.dataframe(
            ingredientes_df.style.format({'% Composición': '{:.2f}%', 'GRAMOS': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        # Gráfico de composición
        st.subheader("📊 Distribución de Ingredientes")
        
        # Gráfico de barras
        st.bar_chart(ingredientes_df.set_index('Materia Prima')['% Composición'])
        
        # Tabla de porcentajes como alternativa al gráfico de torta
        st.subheader("🥧 Porcentajes en el Total")
        
        # Ordenar por porcentaje descendente
        porcentajes_df = ingredientes_df[['Materia Prima', '% Composición']].sort_values('% Composición', ascending=False)
        
        # Mostrar tabla con barras de progreso
        for _, row in porcentajes_df.iterrows():
            porcentaje = row['% Composición']
            st.write(f"**{row['Materia Prima']}**: {porcentaje:.1f}%")
            st.progress(min(porcentaje / 100, 1.0))
    
    with tab3:
        # Calculadora de producción
        st.subheader("🧮 Escalar Receta")
        
        col1, col2 = st.columns(2)
        with col1:
            unidades_deseadas = st.number_input(
                "Unidades a producir:",
                min_value=1,
                value=int(metadata["Cantidad"]),
                help="Cantidad de unidades que desea producir"
            )
        
        factor = unidades_deseadas / metadata["Cantidad"]
        ingredientes_df['Gramos necesarios'] = ingredientes_df['GRAMOS'] * factor
        
        # Mostrar el factor de escala
        with col2:
            st.metric("Factor de escala", f"{factor:.2f}x")
        
        st.dataframe(
            ingredientes_df[['Materia Prima', 'GRAMOS', 'Gramos necesarios']].style.format({
                'GRAMOS': '{:.2f} g',
                'Gramos necesarios': '{:.2f} g'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar el total de ingredientes necesarios
        total_gramos_necesarios = ingredientes_df['Gramos necesarios'].sum()
        st.metric("Total de ingredientes necesarios", f"{total_gramos_necesarios:.2f} g")

# --- Exportar receta ---
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Exportar Receta")

def get_table_download_link(df, filename):
    """Genera un enlace para descargar un dataframe como archivo Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=selected_recipe, index=False)
    processed_data = output.getvalue()
    b64 = base64.b64encode(processed_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">📥 Descargar como Excel</a>'

st.sidebar.markdown(get_table_download_link(recipe_df, f"receta_{selected_recipe}"), unsafe_allow_html=True)

# Créditos
st.sidebar.markdown("---")
st.sidebar.caption("© Arte París - Sistema de Gestión de Recetas v2.0")

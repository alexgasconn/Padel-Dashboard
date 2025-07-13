# dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Importar funciones de nuestros módulos
from utils import load_data, create_performance_df
from tabs import (
    jugadores,
    lugares,
    temporal,
    graficos,
    datos,
    estadisticas,
    nuevos_analisis,
    dataframes_tab
)

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard Padel Avanzado", layout="wide", page_icon="🎾")
st.markdown(
    """
    <style>
    .main {background-color: #f5f5f5;}
    .stMetric {border: 1px solid #e6e6e6; border-radius: 5px; padding: 10px;}
    .stTabs {background-color: #ffffff; padding: 10px; border-radius: 5px;}
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🎾 Dashboard Padel Avanzado")
st.markdown("Explora tu rendimiento en pádel con estadísticas detalladas y visualizaciones interactivas.")

# --- CARGA DE DATOS ---
with st.spinner("Cargando datos de pádel..."):
    df = load_data()

if df.empty:
    st.error("No se pudieron cargar los datos. Por favor, verifica la URL o los datos.")
    st.stop()

# --- FILTROS EN LA BARRA LATERAL ---
with st.sidebar:
    st.header("🎯 Filtros")

    def create_multiselect_with_all(label, options, key):
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.multiselect(label, options, default=options, key=key)
        with col2:
            if st.button("Todo", key=f"all_{key}", use_container_width=True):
                st.session_state[key] = options
                st.rerun()
        return selected

    with st.expander("Opciones de filtrado", expanded=False):
        year = create_multiselect_with_all("Año", sorted(df["Year"].dropna().unique()), "year_filter")
        month = create_multiselect_with_all("Mes", sorted(df["Month"].dropna().unique(), key=lambda m: list(pd.to_datetime(df['Date']).dt.month_name().unique()).index(m)), "month_filter")
        weekday = create_multiselect_with_all("Día de la semana", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "weekday_filter")
        location = create_multiselect_with_all("Lugar", sorted(df["Location"].dropna().unique()), "location_filter")
        teammate = create_multiselect_with_all("Compañero", sorted(df["Teammate"].dropna().unique()), "teammate_filter")

        opponent = []
        if "Opponent" in df.columns:
            opponent = create_multiselect_with_all("Rival", sorted(df["Opponent"].dropna().unique()), "opponent_filter")

        result = create_multiselect_with_all("Resultado", ["W", "L", "N"], "result_filter")
        date_range = st.date_input("Rango de fechas", [df["Date"].min(), df["Date"].max()])

        if st.button("Restablecer filtros"):
            for key in st.session_state.keys():
                if key.endswith('_filter'):
                    del st.session_state[key]
            st.rerun()

# --- APLICAR FILTROS ---
filtered_df = df[
    (df["Year"].isin(year)) &
    (df["Month"].isin(month)) &
    (df["Weekday"].isin(weekday)) &
    (df["Location"].isin(location)) &
    (df["Teammate"].isin(teammate)) &
    (df["Result"].isin(result)) &
    (df["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]
if "Opponent" in df.columns and opponent:
    filtered_df = filtered_df[filtered_df["Opponent"].isin(opponent)]

# --- MÉTRICAS GLOBALES ---
st.subheader("📊 Resumen Global")
if not filtered_df.empty:
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    total_games = len(filtered_df)
    wins = (filtered_df['Result'] == 'W').sum()
    losses = (filtered_df['Result'] == 'L').sum()
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    win_rate_no_draws = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    col1.metric("Partidos", total_games)
    col2.metric("Victorias", wins)
    col3.metric("Derrotas", losses)
    col4.metric("% Victorias", f"{win_rate:.1f}%")
    col5.metric("% Victorias (s/ emp)", f"{win_rate_no_draws:.1f}%")
    col6.metric("Merit Avg", f"{filtered_df['Merit'].mean():.2f}")
    col7.metric("Química Avg", f"{filtered_df['Quimica'].mean():.2f}")
    col8.metric("Rendim. Avg", f"{filtered_df['Rendiment'].mean():.2f}")
    col9.metric("Dif. Juegos Avg", f"{filtered_df['Game-Diff'].mean():.2f}")
else:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
    st.stop()


# --- PRE-CÁLCULO DE DATAFRAMES DE RENDIMIENTO ---
st.subheader("🎯 Análisis de Rendimiento Detallado")
teammates_df = create_performance_df(filtered_df, 'Teammate', 'Compañero')
locations_df = create_performance_df(filtered_df, 'Location', 'Lugar')

filtered_copy = filtered_df.copy()
filtered_copy['Hour_Category'] = filtered_copy['Hour'].apply(lambda x: f"{x.hour:02d}:00" if pd.notna(x) else "N/A")
hours_df = create_performance_df(filtered_copy, 'Hour_Category', 'Hora')

opponents_df = pd.DataFrame()
if "Opponent" in df.columns:
    opponents_df = create_performance_df(filtered_df, 'Opponent', 'Rival')

# --- CREACIÓN DE TABS ---
tab_titles = ["🎾 Jugadores", "📍 Lugares", "🕒 Temporal", "📊 Gráficos", "📋 Datos", "🔍 Estadísticas Avanzadas", "🎯 Nuevos Análisis", "📈 Dataframes"]
tabs = st.tabs(tab_titles)

with tabs[0]:
    jugadores.render(filtered_df, teammates_df)

with tabs[1]:
    lugares.render(filtered_df, locations_df)

with tabs[2]:
    temporal.render(filtered_df)

with tabs[3]:
    graficos.render(filtered_df)

with tabs[4]:
    datos.render(filtered_df, teammates_df, locations_df, hours_df, opponents_df)

with tabs[5]:
    estadisticas.render(filtered_df)

with tabs[6]:
    nuevos_analisis.render(df, filtered_df, teammates_df, locations_df, hours_df)

with tabs[7]:
    dataframes_tab.render(df, teammates_df, locations_df, hours_df, opponents_df)


# --- FOOTER ---
st.markdown("---")
st.markdown("*Dashboard creado para análisis avanzado de rendimiento en pádel* 🎾")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
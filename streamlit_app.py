import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
import io
import base64

# --- CONFIG ---
st.set_page_config(page_title="Dashboard Pádel Avanzado", layout="wide", page_icon="🎾")
st.markdown(
    """
    <style>
    .main {background-color: #f5f5f5;}
    .stMetric {border: 1px solid #e6e6e6; border-radius: 5px; padding: 10px;}
    .stTabs {background-color: #ffffff; padding: 10px; border-radius: 5px;}
    .success-metric {background-color: #d4edda; border-color: #c3e6cb; color: #155724;}
    .warning-metric {background-color: #fff3cd; border-color: #ffeaa7; color: #856404;}
    .danger-metric {background-color: #f8d7da; border-color: #f5c6cb; color: #721c24;}
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🎾 Dashboard Pádel Avanzado")
st.markdown("Explora tu rendimiento en pádel con estadísticas detalladas y visualizaciones interactivas.")

# --- LOAD DATA ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3HRJ4LcbIqwxl2ffbR-HDjXgG_dNyetWGTOLfcHGU9yl4lGYki2LoFR2hbLdcyCS1bLwPneVSDwCZ/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(url, parse_dates=["Date"], dayfirst=True)
        # Validate and clean data
        df["Hour"] = pd.to_datetime(df["Hour"], format="%H:%M", errors="coerce").dt.time
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month_name()
        df["Weekday"] = df["Date"].dt.day_name()
        df["Result"] = df["Result"].fillna("N").str.upper().replace({"WIN": "W", "LOSS": "L", "NO RESULT": "N"})
        if not df["Result"].isin(["W", "L", "N"]).all():
            st.warning("Advertencia: Columna 'Result' contiene valores no válidos. Se usarán 'W', 'L', 'N'.")
        numeric_cols = ["Game-Diff", "Rating", "Quimica", "Rendiment"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}. Usando datos de respaldo o datos vacíos.")
        return pd.DataFrame()  # Fallback to empty DataFrame

# --- ANALYSIS FUNCTIONS ---
def calculate_win_probability(wins, total_games, losses_only=False):
    """Calculate win probability with confidence adjustment"""
    if total_games == 0:
        return 0
    
    base_rate = wins / total_games
    
    # Confidence adjustment based on sample size
    confidence_factor = min(1, total_games / 10)  # Full confidence at 10+ games
    
    # Regression to mean (50% baseline)
    adjusted_rate = base_rate * confidence_factor + 0.5 * (1 - confidence_factor)
    
    return min(100, max(0, adjusted_rate * 100))

def create_performance_df(df, group_col, entity_name):
    """Create performance DataFrame for any grouping"""
    performance = df.groupby(group_col).agg({
        'Result': ['count', lambda x: (x == 'W').sum(), lambda x: (x == 'L').sum(), lambda x: (x == 'N').sum()],
        'Rating': 'mean',
        'Quimica': 'mean',
        'Rendiment': 'mean',
        'Game-Diff': 'mean'
    }).round(2)
    
    performance.columns = ['Total_Partidos', 'Victorias', 'Derrotas', 'Empates', 'Rating_Avg', 'Quimica_Avg', 'Rendiment_Avg', 'GameDiff_Avg']
    
    # Calculate percentages
    performance['Win_Rate_Total'] = (performance['Victorias'] / performance['Total_Partidos'] * 100).round(1)
    performance['Win_Rate_Sin_Empates'] = (performance['Victorias'] / (performance['Victorias'] + performance['Derrotas']) * 100).fillna(0).round(1)
    
    # Calculate win probability
    performance['Probabilidad_Victoria'] = performance.apply(
        lambda row: calculate_win_probability(row['Victorias'], row['Total_Partidos']), axis=1
    ).round(1)
    
    performance = performance.sort_values('Probabilidad_Victoria', ascending=False)
    performance.index.name = entity_name
    
    return performance.reset_index()

# --- MAIN ---
with st.spinner("Cargando datos de pádel..."):
    df = load_data()

if df.empty:
    st.error("No se pudieron cargar los datos. Por favor, verifica la URL o los datos.")
    st.stop()

# --- FILTERS ---
with st.sidebar:
    st.header("🎯 Filtros")
    
    # Helper function for "Include All" functionality
    def create_multiselect_with_all(label, options, key):
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.multiselect(label, options, default=options, key=key)
        with col2:
            if st.button("Todo", key=f"all_{key}"):
                st.session_state[key] = options
                st.rerun()
        return selected
    
    with st.expander("Opciones de filtrado", expanded=True):
        year = create_multiselect_with_all("Año", sorted(df["Year"].dropna().unique()), "year_filter")
        month = create_multiselect_with_all("Mes", sorted(df["Month"].dropna().unique()), "month_filter")
        weekday = create_multiselect_with_all("Día de la semana", sorted(df["Weekday"].dropna().unique()), "weekday_filter")
        location = create_multiselect_with_all("Lugar", sorted(df["Location"].dropna().unique()), "location_filter")
        teammate = create_multiselect_with_all("Compañero", sorted(df["Teammate"].dropna().unique()), "teammate_filter")
        
        # Add opponent filter if exists
        if "Opponent" in df.columns:
            opponent = create_multiselect_with_all("Rival", sorted(df["Opponent"].dropna().unique()), "opponent_filter")
        else:
            opponent = []
            
        result = create_multiselect_with_all("Resultado", ["W", "L", "N"], "result_filter")
        
        date_range = st.date_input("Rango de fechas", [df["Date"].min(), df["Date"].max()])
        
        if st.button("Restablecer filtros"):
            for key in st.session_state.keys():
                if key.endswith('_filter'):
                    del st.session_state[key]
            st.rerun()

# Apply filters
filtered = df[
    (df["Year"].isin(year)) &
    (df["Month"].isin(month)) &
    (df["Weekday"].isin(weekday)) &
    (df["Location"].isin(location)) &
    (df["Teammate"].isin(teammate)) &
    (df["Result"].isin(result)) &
    (df["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# Apply opponent filter if available
if "Opponent" in df.columns and opponent:
    filtered = filtered[filtered["Opponent"].isin(opponent)]

# --- METRICS ---
st.subheader("📊 Resumen Global")
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

total_games = len(filtered)
wins = (filtered['Result'] == 'W').sum()
losses = (filtered['Result'] == 'L').sum()
draws = (filtered['Result'] == 'N').sum()
win_rate = (wins / total_games * 100) if total_games > 0 else 0
win_rate_no_draws = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

col1.metric("Partidos", total_games, help="Total de partidos jugados")
col2.metric("Victorias", wins, help="Partidos ganados")
col3.metric("Derrotas", losses, help="Partidos perdidos")
col4.metric("% Victorias", f"{win_rate:.1f}%", help="Porcentaje de partidos ganados")
col5.metric("% Victorias (sin empates)", f"{win_rate_no_draws:.1f}%", help="Porcentaje de victorias sin contar empates")
col6.metric("Rating medio", f"{filtered['Rating'].mean():.2f}", help="Promedio de tu rating personal")
col7.metric("Química media", f"{filtered['Quimica'].mean():.2f}", help="Promedio de química con compañeros")
col8.metric("Rendimiento medio", f"{filtered['Rendiment'].mean():.2f}", help="Promedio de tu rendimiento")

# --- PERFORMANCE DATAFRAMES ---
st.subheader("🎯 Análisis de Rendimiento Detallado")

# Create performance DataFrames
teammates_df = create_performance_df(filtered, 'Teammate', 'Compañero')
locations_df = create_performance_df(filtered, 'Location', 'Lugar')

# Create hour analysis
filtered_copy = filtered.copy()
filtered_copy['Hour_Category'] = filtered_copy['Hour'].apply(
    lambda x: f"{x.hour:02d}:00" if pd.notna(x) else "N/A"
)
hours_df = create_performance_df(filtered_copy, 'Hour_Category', 'Hora')

# Create opponents DataFrame if available
if "Opponent" in df.columns:
    opponents_df = create_performance_df(filtered, 'Opponent', 'Rival')

# Display performance tables
tab_perf1, tab_perf2, tab_perf3, tab_perf4 = st.tabs(["👥 Compañeros", "📍 Lugares", "🕒 Horas", "⚔️ Rivales"])

with tab_perf1:
    st.subheader("Rendimiento por Compañero")
    st.dataframe(
        teammates_df.style.format({
            'Win_Rate_Total': '{:.1f}%',
            'Win_Rate_Sin_Empates': '{:.1f}%',
            'Probabilidad_Victoria': '{:.1f}%',
            'Rating_Avg': '{:.2f}',
            'Quimica_Avg': '{:.2f}',
            'Rendiment_Avg': '{:.2f}',
            'GameDiff_Avg': '{:.2f}'
        }),
        use_container_width=True
    )

with tab_perf2:
    st.subheader("Rendimiento por Lugar")
    st.dataframe(
        locations_df.style.format({
            'Win_Rate_Total': '{:.1f}%',
            'Win_Rate_Sin_Empates': '{:.1f}%',
            'Probabilidad_Victoria': '{:.1f}%',
            'Rating_Avg': '{:.2f}',
            'Quimica_Avg': '{:.2f}',
            'Rendiment_Avg': '{:.2f}',
            'GameDiff_Avg': '{:.2f}'
        }),
        use_container_width=True
    )

with tab_perf3:
    st.subheader("Rendimiento por Hora")
    st.dataframe(
        hours_df.style.format({
            'Win_Rate_Total': '{:.1f}%',
            'Win_Rate_Sin_Empates': '{:.1f}%',
            'Probabilidad_Victoria': '{:.1f}%',
            'Rating_Avg': '{:.2f}',
            'Quimica_Avg': '{:.2f}',
            'Rendiment_Avg': '{:.2f}',
            'GameDiff_Avg': '{:.2f}'
        }),
        use_container_width=True
    )

with tab_perf4:
    if "Opponent" in df.columns:
        st.subheader("Rendimiento por Rival")
        st.dataframe(
            opponents_df.style.format({
                'Win_Rate_Total': '{:.1f}%',
                'Win_Rate_Sin_Empates': '{:.1f}%',
                'Probabilidad_Victoria': '{:.1f}%',
                'Rating_Avg': '{:.2f}',
                'Quimica_Avg': '{:.2f}',
                'Rendiment_Avg': '{:.2f}',
                'GameDiff_Avg': '{:.2f}'
            }),
            use_container_width=True
        )
    else:
        st.info("No hay datos de rivales disponibles en el dataset")

# --- TABS ---
tabs = st.tabs(["🎾 Jugadores", "📍 Lugares", "🕒 Temporal", "📊 Gráficos", "📋 Datos", "🔍 Estadísticas Avanzadas", "🎯 Nuevos Análisis"])

# --- TAB 1: Jugadores ---
with tabs[0]:
    st.subheader("Análisis de Compañeros")
    
    # Enhanced teammate analysis
    teammates = (
        filtered.groupby("Teammate")
        .agg(
            Partidos=("Result", "count"),
            Victorias=("Result", lambda x: (x == "W").sum()),
            WinRate=("Result", lambda x: (x == "W").mean() * 100),
            Quimica=("Quimica", "mean"),
            Rendiment=("Rendiment", "mean"),
            Rating=("Rating", "mean"),
            GameDiff=("Game-Diff", "mean")
        )
        .sort_values("WinRate", ascending=False)
    )
    
    # Probability chart for teammates
    prob_chart = alt.Chart(teammates_df).mark_bar().encode(
        x=alt.X("Compañero", sort="-y", title="Compañero"),
        y=alt.Y("Probabilidad_Victoria", title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria", scale=alt.Scale(scheme="redyellowgreen"), title="Probabilidad"),
        tooltip=["Compañero", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(width=800, height=400, title="Probabilidad de Victoria por Compañero")
    st.altair_chart(prob_chart, use_container_width=True)
    
    # Chemistry vs Performance enhanced
    scatter = alt.Chart(filtered).mark_circle(size=100).encode(
        x=alt.X("Quimica", title="Química", scale=alt.Scale(zero=False)),
        y=alt.Y("Rendiment", title="Rendimiento", scale=alt.Scale(zero=False)),
        color=alt.Color("Result", scale=alt.Scale(domain=["W", "L", "N"], range=["green", "red", "gray"])),
        size=alt.Size("Rating", scale=alt.Scale(range=[50, 300])),
        tooltip=["Teammate", "Quimica", "Rendiment", "Rating", "Result", "Date"]
    ).properties(width=800, height=400, title="Química vs. Rendimiento (tamaño = Rating)")
    st.altair_chart(scatter, use_container_width=True)

# --- TAB 2: Lugares ---
with tabs[1]:
    st.subheader("Análisis de Lugares")
    
    # Enhanced location analysis
    places = (
        filtered.groupby("Location")
        .agg(
            Partidos=("Result", "count"),
            Victorias=("Result", lambda x: (x == "W").sum()),
            WinRate=("Result", lambda x: (x == "W").mean() * 100),
            Rating=("Rating", "mean"),
            Quimica=("Quimica", "mean"),
            Rendiment=("Rendiment", "mean")
        )
        .sort_values("WinRate", ascending=False)
    )
    
    # Location probability chart
    location_prob_chart = alt.Chart(locations_df).mark_bar().encode(
        x=alt.X("Lugar", sort="-y", title="Lugar"),
        y=alt.Y("Probabilidad_Victoria", title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["Lugar", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(width=800, height=400, title="Probabilidad de Victoria por Lugar")
    st.altair_chart(location_prob_chart, use_container_width=True)
    
    # Performance metrics by location
    location_metrics = alt.Chart(locations_df).mark_point(size=100).encode(
        x=alt.X("Rating_Avg", title="Rating Promedio"),
        y=alt.Y("Rendiment_Avg", title="Rendimiento Promedio"),
        color=alt.Color("Probabilidad_Victoria", scale=alt.Scale(scheme="redyellowgreen")),
        size=alt.Size("Total_Partidos", scale=alt.Scale(range=[100, 500])),
        tooltip=["Lugar", "Rating_Avg", "Rendiment_Avg", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(width=800, height=400, title="Métricas de Rendimiento por Lugar")
    st.altair_chart(location_metrics, use_container_width=True)

# --- TAB 3: Temporal ---
with tabs[2]:
    st.subheader("Análisis Temporal")
    
    # Enhanced rating evolution
    rating_by_date = filtered.groupby("Date").agg({
        "Rating": "mean",
        "Quimica": "mean",
        "Rendiment": "mean",
        "Result": lambda x: (x == "W").mean() * 100
    }).reset_index()
    
    # Multi-line chart
    base = alt.Chart(rating_by_date).add_selection(
        alt.selection_interval(bind='scales')
    )
    
    rating_line = base.mark_line(color='blue').encode(
        x=alt.X("Date:T", title="Fecha"),
        y=alt.Y("Rating:Q", title="Rating", scale=alt.Scale(zero=False)),
        tooltip=["Date", "Rating"]
    )
    
    winrate_line = base.mark_line(color='green').encode(
        x=alt.X("Date:T"),
        y=alt.Y("Result:Q", title="Win Rate (%)", scale=alt.Scale(zero=False)),
        tooltip=["Date", "Result"]
    )
    
    # Combine charts
    combined = alt.layer(rating_line, winrate_line).resolve_scale(
        y='independent'
    ).properties(width=800, height=400, title="Evolución Temporal: Rating y Win Rate")
    st.altair_chart(combined, use_container_width=True)
    
    # Enhanced heatmap
    filtered_copy = filtered.copy()
    filtered_copy["Hour_Int"] = filtered_copy["Hour"].apply(lambda x: x.hour if pd.notna(x) else 0)
    
    # Win rate heatmap
    heatmap_data = filtered_copy.groupby(["Weekday", "Hour_Int"]).agg({
        "Result": lambda x: (x == "W").mean() * 100
    }).reset_index()
    heatmap_data.columns = ["Weekday", "Hour_Int", "WinRate"]
    
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("Hour_Int:O", title="Hora del día"),
        y=alt.Y("Weekday:N", title="Día de la semana", 
               sort=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
        color=alt.Color("WinRate:Q", title="Win Rate (%)", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["Weekday", "Hour_Int", "WinRate"]
    ).properties(width=800, height=400, title="Win Rate por Día y Hora")
    st.altair_chart(heatmap, use_container_width=True)

# --- TAB 4: Gráficos ---
with tabs[3]:
    st.subheader("Gráficos Avanzados")
    
    # Correlation matrix
    numeric_cols = ["Rating", "Quimica", "Rendiment", "Game-Diff"]
    corr_data = filtered[numeric_cols].corr().reset_index().melt(id_vars="index")
    corr_data.columns = ["Variable1", "Variable2", "Correlation"]
    
    correlation_heatmap = alt.Chart(corr_data).mark_rect().encode(
        x=alt.X("Variable1:N", title=""),
        y=alt.Y("Variable2:N", title=""),
        color=alt.Color("Correlation:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 1])),
        tooltip=["Variable1", "Variable2", "Correlation"]
    ).properties(width=400, height=400, title="Matriz de Correlación")
    st.altair_chart(correlation_heatmap, use_container_width=True)
    
    # Performance distribution
    performance_dist = alt.Chart(filtered).mark_boxplot().encode(
        x=alt.X("Result:N", title="Resultado"),
        y=alt.Y("Rating:Q", title="Rating"),
        color=alt.Color("Result:N", scale=alt.Scale(domain=["W", "L", "N"], range=["green", "red", "gray"]))
    ).properties(width=600, height=400, title="Distribución de Rating por Resultado")
    st.altair_chart(performance_dist, use_container_width=True)
    
    # Game difference analysis
    game_diff_chart = alt.Chart(filtered).mark_bar().encode(
        x=alt.X("Game-Diff:Q", bin=alt.Bin(maxbins=20), title="Diferencia de Juegos"),
        y=alt.Y("count():Q", title="Frecuencia"),
        color=alt.Color("Result:N", scale=alt.Scale(domain=["W", "L", "N"], range=["green", "red", "gray"])),
        tooltip=["count()", "Game-Diff"]
    ).properties(width=800, height=400, title="Distribución de Diferencia de Juegos")
    st.altair_chart(game_diff_chart, use_container_width=True)

# --- TAB 5: Datos ---
with tabs[4]:
    st.subheader("Datos Completos")
    
    # Enhanced data view with search
    search_term = st.text_input("Buscar en los datos:", "")
    
    display_df = filtered.copy()
    if search_term:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    
    st.dataframe(
        display_df.sort_values("Date", ascending=False).reset_index(drop=True), 
        use_container_width=True
    )
    
    # Enhanced export options
    col1, col2, col3 = st.columns(3)
    with col1:
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"padel_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export summary statistics
        summary_stats = display_df.describe().to_csv().encode('utf-8')
        st.download_button(
            label="📊 Descargar Estadísticas",
            data=summary_stats,
            file_name=f"padel_stats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Export performance DataFrames
        performance_data = {
            'Compañeros': teammates_df,
            'Lugares': locations_df,
            'Horas': hours_df
        }
        
        if "Opponent" in df.columns:
            performance_data['Rivales'] = opponents_df
        
        # Create combined export
        combined_export = pd.DataFrame()
        for name, df_perf in performance_data.items():
            df_temp = df_perf.copy()
            df_temp['Categoria'] = name
            combined_export = pd.concat([combined_export, df_temp], ignore_index=True)
        
        perf_csv = combined_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="🎯 Descargar Análisis",
            data=perf_csv,
            file_name=f"padel_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# --- TAB 6: Estadísticas Avanzadas ---
with tabs[5]:
    st.subheader("Estadísticas Avanzadas")
    
    # Enhanced streak analysis
    def calculate_all_streaks(df):
        df_sorted = df.sort_values("Date")
        win_streaks = []
        loss_streaks = []
        current_win_streak = 0
        current_loss_streak = 0
        
        for result in df_sorted["Result"]:
            if result == "W":
                current_win_streak += 1
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0
            elif result == "L":
                current_loss_streak += 1
                if current_win_streak > 0:
                    win_streaks.append(current_win_streak)
                    current_win_streak = 0
            else:  # Draw
                if current_win_streak > 0:
                    win_streaks.append(current_win_streak)
                    current_win_streak = 0
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0
        
        # Don't forget the last streak
        if current_win_streak > 0:
            win_streaks.append(current_win_streak)
        if current_loss_streak > 0:
            loss_streaks.append(current_loss_streak)
            
        return win_streaks, loss_streaks
    
    win_streaks, loss_streaks = calculate_all_streaks(filtered)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if win_streaks:
            st.metric("🔥 Racha máxima victorias", max(win_streaks))
        else:
            st.metric("🔥 Racha máxima victorias", 0)
    
    with col2:
        if loss_streaks:
            st.metric("❄️ Racha máxima derrotas", max(loss_streaks))
        else:
            st.metric("❄️ Racha máxima derrotas", 0)
    
    with col3:
        if win_streaks:
            st.metric("📈 Racha promedio victorias", f"{np.mean(win_streaks):.1f}")
        else:
            st.metric("📈 Racha promedio victorias", 0)
    
    with col4:
        if loss_streaks:
            st.metric("📉 Racha promedio derrotas", f"{np.mean(loss_streaks):.1f}")
        else:
            st.metric("📉 Racha promedio derrotas", 0)
    
    # Enhanced time analysis
    filtered_copy = filtered.copy()
    filtered_copy["TimeOfDay"] = filtered_copy["Hour"].apply(
        lambda x: "Mañana" if pd.notna(x) and x.hour < 14 else "Tarde" if pd.notna(x) and x.hour < 20 else "Noche"
    )
    
    time_analysis = filtered_copy.groupby("TimeOfDay").agg({
        "Result": ["count", lambda x: (x == "W").sum(), lambda x: (x == "W").mean() * 100],
        "Rating": "mean",
        "Quimica": "mean",
        "Rendiment": "mean"
    }).round(2)
    
    time_analysis.columns = ["Partidos", "Victorias", "WinRate", "Rating", "Quimica", "Rendiment"]
    st.dataframe(time_analysis.style.format({"WinRate": "{:.1f}%"}), use_container_width=True)
    
    # Performance consistency
    consistency_metrics = filtered.groupby("Date").agg({
        "Rating": "mean",
        "Quimica": "mean", 
        "Rendiment": "mean"
    }).std()
    
    st.subheader("Consistencia de Rendimiento")
    col1, col2, col3 = st.columns(3)
    col1.metric("Desv. Rating", f"{consistency_metrics['Rating']:.2f}", help="Menor valor = más consistente")
    col2.metric("Desv. Química", f"{consistency_metrics['Qui

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
        df["Year"] = df[" CCA
        Date"].dt.year
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

# --- MAIN ---
with st.spinner("Cargando datos de pádel..."):
    df = load_data()

if df.empty:
    st.error("No se pudieron cargar los datos. Por favor, verifica la URL o los datos.")
    st.stop()

# --- FILTERS ---
with st.sidebar:
    st.header("🎯 Filtros")
    with st.expander("Opciones de filtrado", expanded=True):
        year = st.multiselect("Año", sorted(df["Year"].dropna().unique()), default=sorted(df["Year"].dropna().unique()))
        month = st.multiselect("Mes", sorted(df["Month"].dropna().unique()), default=sorted(df["Month"].dropna().unique()))
        weekday = st.multiselect("Día de la semana", sorted(df["Weekday"].dropna().unique()), default=sorted(df["Weekday"].dropna().unique()))
        location = st.multiselect("Lugar", sorted(df["Location"].dropna().unique()), default=sorted(df["Location"].dropna().unique()))
        teammate = st.multiselect("Compañero", sorted(df["Teammate"].dropna().unique()), default=sorted(df["Teammate"].dropna().unique()))
        result = st.multiselect("Resultado", ["W", "L", "N"], default=["W", "L", "N"])
        date_range = st.date_input("Rango de fechas", [df["Date"].min(), df["Date"].max()])
        if st.button("Restablecer filtros"):
            st.experimental_rerun()

filtered = df[
    (df["Year"].isin(year)) &
    (df["Month"].isin(month)) &
    (df["Weekday"].isin(weekday)) &
    (df["Location"].isin(location)) &
    (df["Teammate"].isin(teammate)) &
    (df["Result"].isin(result)) &
    (df["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# --- METRICS ---
st.subheader("📊 Resumen Global")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Partidos", len(filtered), help="Total de partidos jugados")
col2.metric("% Victorias", f"{(filtered['Result'] == 'W').mean() * 100:.1f}%", help="Porcentaje de partidos ganados")
col3.metric("Dif. juegos media", f"{filtered['Game-Diff'].mean():.2f}", help="Diferencia promedio de juegos por partido")
col4.metric("Rating medio", f"{filtered['Rating'].mean():.2f}", help="Promedio de tu rating personal")
col5.metric("Química media", f"{filtered['Quimica'].mean():.2f}", help="Promedio de química con compañeros")
col6.metric("Rendimiento medio", f"{filtered['Rendiment'].mean():.2f}", help="Promedio de tu rendimiento")

# --- TABS ---
tabs = st.tabs(["🎾 Jugadores", "📍 Lugares", "🕒 Temporal", "📊 Gráficos", "📋 Datos", "🔍 Estadísticas Avanzadas"])

# --- TAB 1: Jugadores ---
with tabs[0]:
    st.subheader("Rendimiento por compañero")
    teammates = (
        filtered.groupby("Teammate")
        .agg(
            Partidos=("Result", "count"),
            Victorias=("Result", lambda x: (x == "W").sum()),
            WinRate=("Result", lambda x: (x == "W").mean() * 100),
            Quimica=("Quimica", "mean"),
            Rendiment=("Rendiment", "mean"),
            Rating=("Rating", "mean")
        )
        .sort_values("WinRate", ascending=False)
    )
    st.dataframe(
        teammates.style.format({"WinRate": "{:.1f}%", "Quimica": "{:.2f}", "Rendiment": "{:.2f}", "Rating": "{:.2f}"}),
        use_container_width=True
    )
    
    # Bar chart for win rates
    bar = alt.Chart(teammates.reset_index()).mark_bar().encode(
        x=alt.X("Teammate", sort="-y", title="Compañero"),
        y=alt.Y("WinRate", title="% Victorias"),
        color=alt.Color("WinRate", scale=alt.Scale(scheme="blues")),
        tooltip=["Teammate", alt.Tooltip("WinRate", format=".1f")]
    ).properties(width=600, height=400, title="Porcentaje de victorias por compañero")
    st.altair_chart(bar, use_container_width=True)
    
    # Scatter plot for chemistry vs performance
    scatter = alt.Chart(filtered).mark_circle(size=60).encode(
        x=alt.X("Quimica", title="Química"),
        y=alt.Y("Rendiment", title="Rendimiento"),
        color="Teammate",
        tooltip=["Teammate", "Quimica", "Rendiment", "Date"]
    ).properties(width=600, height=400, title="Química vs. Rendimiento por compañero")
    st.altair_chart(scatter, use_container_width=True)

# --- TAB 2: Lugares ---
with tabs[1]:
    st.subheader("Rendimiento por ubicación")
    places = (
        filtered.groupby("Location")
        .agg(
            Partidos=("Result", "count"),
            Victorias=("Result", lambda x: (x == "W").sum()),
            WinRate=("Result", lambda x: (x == "W").mean() * 100),
            Rating=("Rating", "mean"),
)
        .sort_values("WinRate", ascending=False)
    )
    st.dataframe(
        places.style.format({"WinRate": "{:.1f}%", "Rating": "{:.2f}"}),
        use_container_width=True
    )
    
    # Pie chart for match distribution
    pie = alt.Chart(places.reset_index()).mark_arc().encode(
        theta=alt.Theta("Partidos:Q", title="Partidos"),
        color=alt.Color("Location:N", title="Lugar"),
        tooltip=["Location", "Partidos", alt.Tooltip("WinRate", format=".1f")]
    ).properties(width=600, height=400, title="Distribución de partidos por lugar")
    st.altair_chart(pie, use_container_width=True)

# --- TAB 3: Temporal ---
with tabs[2]:
    st.subheader("Evolución temporal")
    rating_by_date = filtered.groupby("Date")["Rating"].mean().reset_index()
    line = alt.Chart(rating_by_date).mark_line(point=True).encode(
        x=alt.X("Date:T", title="Fecha"),
        y=alt.Y("Rating:Q", title="Rating promedio"),
        tooltip=["Date", alt.Tooltip("Rating", format=".2f")]
    )
    trend = line.transform_loess("Date", "Rating", bandwidth=0.3).mark_line(color="red", size=3)
    chart = (line + trend).properties(width=800, height=400, title="Evolución del rating")
    st.altair_chart(chart, use_container_width=True)
    
    # Heatmap for matches by weekday and hour
    filtered["Hour_Int"] = filtered["Hour"].apply(lambda x: x.hour if pd.notna(x) else 0)
    heatmap_data = filtered.groupby(["Weekday", "Hour_Int"]).size().reset_index(name="Matches")
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("Hour_Int:O", title="Hora del día"),
        y=alt.Y("Weekday:N", title="Día de la semana", sort=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
        color=alt.Color("Matches:Q", title="Partidos", scale=alt.Scale(scheme="greens")),
        tooltip=["Weekday", "Hour_Int", "Matches"]
    ).properties(width=800, height=400, title="Partidos por día y hora")
    st.altair_chart(heatmap, use_container_width=True)

# --- TAB 4: Gráficos ---
with tabs[3]:
    st.subheader("Gráficos comparativos")
    # Bar chart for win rates by teammate
    bar = alt.Chart(teammates.reset_index()).mark_bar().encode(
        x=alt.X("Teammate", sort="-y", title="Compañero"),
        y=alt.Y("WinRate", title="% Victorias"),
        color=alt.Color("Teammate"),
        tooltip=["Teammate", alt.Tooltip("WinRate", format=".1f")]
    ).properties(width=600, height=400, title="Porcentaje de victorias por compañero")
    st.altair_chart(bar, use_container_width=True)
    
    # Win/Loss pie chart
    result_counts = filtered["Result"].value_counts().reset_index()
    result_counts.columns = ["Result", "Count"]
    pie_result = alt.Chart(result_counts).mark_arc().encode(
        theta=alt.Theta("Count:Q", title="Partidos"),
        color=alt.Color("Result:N", title="Resultado", scale=alt.Scale(domain=["W", "L", "N"], range=["#36A2EB", "#FF6384", "#E6E6E6"])),
        tooltip=["Result", "Count"]
    ).properties(width=600, height=400, title="Distribución de resultados")
    st.altair_chart(pie_result, use_container_width=True)
    
    # Rating histogram
    hist = alt.Chart(filtered).mark_bar().encode(
        x=alt.X("Rating:Q", bin=alt.Bin(maxbins=20), title="Rating"),
        y=alt.Y("count():Q", title="Número de partidos"),
        tooltip=["count()", alt.Tooltip("Rating", bin=True)]
    ).properties(width=600, height=400, title="Distribución de ratings")
    st.altair_chart(hist, use_container_width=True)

# --- TAB 5: Datos ---
with tabs[4]:
    st.subheader("Tabla completa de partidos")
    st.dataframe(filtered.sort_values("Date", ascending=False).reset_index(drop=True), use_container_width=True)
    # Export filtered data
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos filtrados (CSV)",
        data=csv,
        file_name="padel_data_filtered.csv",
        mime="text/csv"
    )

# --- TAB 6: Estadísticas Avanzadas ---
with tabs[5]:
    st.subheader("Estadísticas avanzadas")
    # Win streak analysis
    def calculate_streaks(df):
        streaks = []
        current_streak = 0
        for result in df.sort_values("Date")["Result"]:
            if result == "W":
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0
        if current_streak > 0:
            streaks.append(current_streak)
        return streaks

    streaks = calculate_streaks(filtered)
    if streaks:
        st.metric("Racha máxima de victorias", max(streaks), help="Mayor número de victorias consecutivas")
        st.write(f"Rachas de victorias: {streaks}")
    else:
        st.write("No hay rachas de victorias en los datos filtrados.")

    # Performance by time of day
    filtered["TimeOfDay"] = filtered["Hour"].apply(
        lambda x: "Mañana" if pd.notna(x) and x.hour < 14 else "Tarde" if pd.notna(x) and x.hour < 20 else "Noche"
    )
    time_perf = filtered.groupby("TimeOfDay").agg(
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == "W").mean() * 100)
    ).reset_index()
    st.dataframe(time_perf.style.format({"WinRate": "{:.1f}%"}), use_container_width=True)

    # Bar chart for performance by time of day
    time_bar = alt.Chart(time_perf).mark_bar().encode(
        x=alt.X("TimeOfDay", title="Momento del día"),
        y=alt.Y("WinRate", title="% Victorias"),
        color=alt.Color("TimeOfDay", scale=alt.Scale(scheme="set2")),
        tooltip=["TimeOfDay", alt.Tooltip("WinRate", format=".1f")]
    ).properties(width=600, height=400, title="Rendimiento por momento del día")
    st.altair_chart(time_bar, use_container_width=True)

# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Dashboard Pádel", layout="wide")
st.title("📈 Dashboard Pádel Personal")

# --- LOAD DATA ---
@st.cache_data

def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3HRJ4LcbIqwxl2ffbR-HDjXgG_dNyetWGTOLfcHGU9yl4lGYki2LoFR2hbLdcyCS1bLwPneVSDwCZ/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(url, parse_dates=["Date"], dayfirst=True)
    df["Hour"] = pd.to_datetime(df["Hour"], format="%H:%M", errors="coerce").dt.time
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Weekday"] = df["Date"].dt.day_name()
    df["Result"] = df["Result"].fillna("N")
    df["Game-Diff"] = pd.to_numeric(df["Game-Diff"], errors='coerce')
    df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce')
    df["Quimica"] = pd.to_numeric(df["Quimica"], errors='coerce')
    df["Rendiment"] = pd.to_numeric(df["Rendiment"], errors='coerce')
    return df

# --- MAIN ---
df = load_data()

# --- FILTERS ---
st.sidebar.header("🎯 Filtros")
year = st.sidebar.multiselect("Año", sorted(df["Year"].dropna().unique()), default=sorted(df["Year"].dropna().unique()))
location = st.sidebar.multiselect("Lugar", sorted(df["Location"].dropna().unique()), default=sorted(df["Location"].dropna().unique()))
teammate = st.sidebar.multiselect("Compañero", sorted(df["Teammate"].dropna().unique()), default=sorted(df["Teammate"].dropna().unique()))

filtered = df[
    df["Year"].isin(year) &
    df["Location"].isin(location) &
    df["Teammate"].isin(teammate)
]

# --- METRICS ---
st.subheader("Resumen Global")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos", len(filtered))
col2.metric("% Victorias", f"{(filtered['Result']=='W').mean()*100:.1f}%")
col3.metric("Dif. juegos media", f"{filtered['Game-Diff'].mean():.2f}")
col4.metric("Rating medio", f"{filtered['Rating'].mean():.2f}")

# --- TABS ---
tabs = st.tabs(["🎾 Jugadores", "📍 Lugares", "🕒 Temporal", "📊 Gráficos", "📋 Datos"])

# --- TAB 1: Jugadores ---
with tabs[0]:
    st.subheader("Rendimiento por compañero")
    teammates = (filtered.groupby("Teammate")
        .agg(Partidos=("Result", "count"),
             Victorias=("Result", lambda x: (x=="W").sum()),
             WinRate=("Result", lambda x: (x=="W").mean()*100),
             Quimica=("Quimica", "mean"),
             Rendiment=("Rendiment", "mean"),
             Rating=("Rating", "mean"))
        .sort_values("WinRate", ascending=False)
    )
    st.dataframe(teammates.style.format({"WinRate": "{:.1f}%", "Quimica": "{:.2f}", "Rendiment": "{:.2f}", "Rating": "{:.2f}"}))

# --- TAB 2: Lugares ---
with tabs[1]:
    st.subheader("Rendimiento por ubicación")
    places = (filtered.groupby("Location")
        .agg(Partidos=("Result", "count"),
             Victorias=("Result", lambda x: (x=="W").sum()),
             WinRate=("Result", lambda x: (x=="W").mean()*100),
             Rating=("Rating", "mean"))
        .sort_values("WinRate", ascending=False)
    )
    st.dataframe(places.style.format({"WinRate": "{:.1f}%", "Rating": "{:.2f}"}))

# --- TAB 3: Temporal ---
with tabs[2]:
    st.subheader("Evolución temporal")
    rating_by_date = filtered.groupby("Date")["Rating"].mean().reset_index()
    chart = alt.Chart(rating_by_date).mark_line(point=True).encode(
        x="Date:T",
        y=alt.Y("Rating:Q", title="Rating promedio"),
        tooltip=["Date", "Rating"]
    ).properties(width=800, height=400)
    st.altair_chart(chart, use_container_width=True)

# --- TAB 4: Gráficos ---
with tabs[3]:
    st.subheader("Gráficos comparativos")
    bar = alt.Chart(teammates.reset_index()).mark_bar().encode(
        x=alt.X("Teammate", sort="-y"),
        y=alt.Y("WinRate", title="% Victorias"),
        tooltip=["Teammate", "WinRate"]
    ).properties(width=800, height=400)
    st.altair_chart(bar, use_container_width=True)

# --- TAB 5: Datos ---
with tabs[4]:
    st.subheader("Tabla completa de partidos")
    st.dataframe(filtered.sort_values("Date", ascending=False).reset_index(drop=True))

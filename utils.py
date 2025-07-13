# utils.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data(show_spinner=False)
def load_data():
    """Carga y pre-procesa los datos desde una URL de Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3HRJ4LcbIqwxl2ffbR-HDjXgG_dNyetWGTOLfcHGU9yl4lGYki2LoFR2hbLdcyCS1bLwPneVSDwCZ/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(url, parse_dates=["Date"], dayfirst=True)
        df = df.sort_values(by="Date").reset_index(drop=True)
        df["Hour"] = pd.to_datetime(df["Hour"], format="%H:%M", errors="coerce").dt.time
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month_name()
        df["Weekday"] = df["Date"].dt.day_name()
        st.markdown(df.columns)
        st.markdown(df.info())

        numeric_cols = ["Merit", "Game-Diff", "Quimica", "Rendiment"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                st.warning(f"Advertencia: La columna '{col}' no se encontró. Se usarán ceros.")

        df["Rating"] = df["Merit"].cumsum()
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}. Usando un DataFrame vacío.")
        return pd.DataFrame()

def calculate_win_probability(wins, total_games):
    """Calcula la probabilidad de victoria ajustada por confianza."""
    if total_games == 0:
        return 0
    base_rate = wins / total_games
    confidence_factor = min(1, total_games / 10)
    adjusted_rate = base_rate * confidence_factor + 0.5 * (1 - confidence_factor)
    return min(100, max(0, adjusted_rate * 100))

def create_performance_df(df, group_col, entity_name):
    """Crea un DataFrame de rendimiento para una columna de agrupación específica."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()

    performance = df.groupby(group_col).agg({
        'Result': ['count', lambda x: (x == 'W').sum(), lambda x: (x == 'L').sum(), lambda x: (x == 'N').sum()],
        'Merit': 'mean',
        'Quimica': 'mean',
        'Rendiment': 'mean',
        'Game-Diff': 'mean'
    }).round(2)

    performance.columns = ['Total_Partidos', 'Victorias', 'Derrotas', 'Empates', 'Merit_Avg', 'Quimica_Avg', 'Rendiment_Avg', 'GameDiff_Avg']
    performance['Win_Rate_Total'] = (performance['Victorias'] / performance['Total_Partidos'] * 100).round(1)
    performance['Win_Rate_Sin_Empates'] = (performance['Victorias'] / (performance['Victorias'] + performance['Derrotas']) * 100).fillna(0).round(1)
    performance['Probabilidad_Victoria'] = performance.apply(
        lambda row: calculate_win_probability(row['Victorias'], row['Total_Partidos']), axis=1
    ).round(1)

    performance = performance.sort_values('Probabilidad_Victoria', ascending=False)
    performance.index.name = entity_name
    return performance.reset_index()

def calculate_all_streaks(df):
    """Calcula todas las rachas de victorias y derrotas."""
    df_sorted = df.sort_values("Date")
    win_streaks, loss_streaks = [], []
    current_win_streak, current_loss_streak = 0, 0
    
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
        else:
            if current_win_streak > 0:
                win_streaks.append(current_win_streak)
            if current_loss_streak > 0:
                loss_streaks.append(current_loss_streak)
            current_win_streak, current_loss_streak = 0, 0
            
    if current_win_streak > 0: win_streaks.append(current_win_streak)
    if current_loss_streak > 0: loss_streaks.append(current_loss_streak)
    return win_streaks, loss_streaks
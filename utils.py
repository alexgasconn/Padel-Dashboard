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

        numeric_cols = ["Merit", "Game-Diff", "Quimica", "Rendiment"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                st.warning(f"Advertencia: La columna '{col}' no se encontró. Se usarán ceros.")

        df["Rating"] = df["Merit"] # 'Rating' ahora es el 'Merit' del partido.
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}. Usando un DataFrame vacío.")
        return pd.DataFrame()

def scale_value(value, min_val, max_val):
    """Escala un valor entre 0 y 1."""
    if max_val == min_val:
        return 0.5 # Evitar división por cero si todos los valores son iguales
    return (value - min_val) / (max_val - min_val)

def calculate_advanced_win_probability(performance_df):
    """
    Calcula una probabilidad de victoria basada en múltiples factores.
    Factores: % Victorias, Partidos, Química, Rendimiento, Game-Diff, Merit.
    """
    if performance_df.empty:
        return pd.Series(dtype=float)

    # 1. Definir los pesos para cada factor. AJUSTA ESTOS VALORES SEGÚN TU PREFERENCIA.
    weights = {
        "win_rate": 0.35,      # El más importante
        "rendiment": 0.20,     # Rendimiento personal
        "game_diff": 0.15,     # Qué tan abultada es la victoria/derrota
        "quimica": 0.10,       # Sinergia con el compañero
        "merit": 0.10,         # Aporte neto en el partido (Rating +/-)
        "num_partidos": 0.10   # Factor de confianza
    }

    # 2. Escalar cada columna de 0 a 1 para que sean comparables
    df = performance_df.copy()
    scaled = pd.DataFrame(index=df.index)

    scaled['win_rate'] = df['Win_Rate_Sin_Empates'] / 100.0
    scaled['rendiment'] = scale_value(df['Rendiment_Avg'], df['Rendiment_Avg'].min(), df['Rendiment_Avg'].max())
    scaled['game_diff'] = scale_value(df['GameDiff_Avg'], df['GameDiff_Avg'].min(), df['GameDiff_Avg'].max())
    scaled['quimica'] = scale_value(df['Quimica_Avg'], df['Quimica_Avg'].min(), df['Quimica_Avg'].max())
    scaled['merit'] = scale_value(df['Merit_Avg'], df['Merit_Avg'].min(), df['Merit_Avg'].max())
    # Para el número de partidos, usamos una transformación logarítmica para reducir el impacto de valores muy altos
    scaled['num_partidos'] = np.log1p(df['Total_Partidos']) / np.log1p(df['Total_Partidos'].max())

    # Rellenar NaNs con 0.5 (valor neutral) que pueden aparecer si solo hay un registro
    scaled = scaled.fillna(0.5)

    # 3. Calcular el score ponderado
    final_score = (
        scaled['win_rate'] * weights['win_rate'] +
        scaled['rendiment'] * weights['rendiment'] +
        scaled['game_diff'] * weights['game_diff'] +
        scaled['quimica'] * weights['quimica'] +
        scaled['merit'] * weights['merit'] +
        scaled['num_partidos'] * weights['num_partidos']
    )

    # 4. Normalizar el score final para que esté entre un rango razonable (ej. 30% a 95%)
    # Esto hace que las probabilidades sean más intuitivas que un simple 0-100.
    min_prob = 30
    max_prob = 95
    final_prob = min_prob + (final_score * (max_prob - min_prob))

    return final_prob.round(1)


def create_performance_df(df, group_col, entity_name):
    """Crea un DataFrame de rendimiento para una columna de agrupación específica."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()

    performance = df.groupby(group_col).agg({
        'Result': ['count', lambda x: (x == 'W').sum()],
        'Merit': 'mean', # Esto es el Rating +/- promedio
        'Quimica': 'mean',
        'Rendiment': 'mean',
        'Game-Diff': 'mean'
    }).round(2)

    performance.columns = ['Total_Partidos', 'Victorias', 'Merit_Avg', 'Quimica_Avg', 'Rendiment_Avg', 'GameDiff_Avg']
    
    # Calcular % de Victorias (sin contar empates)
    performance['Win_Rate_Sin_Empates'] = (performance['Victorias'] / (df.groupby(group_col)['Result'].apply(lambda x: (x != 'N').sum())) * 100).fillna(0).round(1)

    # *** LLAMADA A LA NUEVA FUNCIÓN DE PROBABILIDAD ***
    performance['Probabilidad_Victoria'] = calculate_advanced_win_probability(performance)
    
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
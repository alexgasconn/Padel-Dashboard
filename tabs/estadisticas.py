# tabs/estadisticas.py
import streamlit as st
import numpy as np
import pandas as pd
from utils import calculate_all_streaks

def render(filtered_df):
    st.subheader("Estadísticas Avanzadas")

    if filtered_df.empty:
        st.info("No hay datos para mostrar estadísticas con los filtros actuales.")
        return

    # --- Análisis de Rachas ---
    st.markdown("##### Análisis de Rachas")
    win_streaks, loss_streaks = calculate_all_streaks(filtered_df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        max_win_streak = max(win_streaks) if win_streaks else 0
        st.metric("🔥 Racha Máx. Victorias", max_win_streak)
    with col2:
        max_loss_streak = max(loss_streaks) if loss_streaks else 0
        st.metric("❄️ Racha Máx. Derrotas", max_loss_streak)
    with col3:
        avg_win_streak = f"{np.mean(win_streaks):.1f}" if win_streaks else "0"
        st.metric("📈 Racha Prom. Victorias", avg_win_streak)
    with col4:
        avg_loss_streak = f"{np.mean(loss_streaks):.1f}" if loss_streaks else "0"
        st.metric("📉 Racha Prom. Derrotas", avg_loss_streak)

    st.divider()

    # --- Rendimiento por Momento del Día ---
    st.markdown("##### Rendimiento por Momento del Día")
    temp_df = filtered_df.copy()
    
    def get_time_of_day(hour_obj):
        if pd.isna(hour_obj):
            return "No especificado"
        hour = hour_obj.hour
        if 5 <= hour < 12: return "Mañana"
        if 12 <= hour < 17: return "Mediodía"
        if 17 <= hour < 21: return "Tarde"
        return "Noche"

    temp_df["TimeOfDay"] = temp_df["Hour"].apply(get_time_of_day)
    
    time_analysis = temp_df.groupby("TimeOfDay").agg(
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == "W").mean() * 100),
        Merit=("Merit", "mean"),
        Quimica=("Quimica", "mean"),
        Rendiment=("Rendiment", "mean")
    ).round(2).sort_values("Partidos", ascending=False)
    
    st.dataframe(time_analysis.style.format({
        "WinRate": "{:.1f}%", "Merit": "{:.2f}", "Quimica": "{:.2f}", "Rendiment": "{:.2f}"
    }), use_container_width=True)

    st.divider()

    # --- Consistencia de Rendimiento ---
    st.markdown("##### Consistencia de Rendimiento (Desviación Estándar)")
    consistency_metrics = filtered_df[["Merit", "Quimica", "Rendiment"]].std()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Desv. Merit", f"{consistency_metrics.get('Merit', 0):.2f}", help="Menor valor = más consistente")
    col2.metric("Desv. Química", f"{consistency_metrics.get('Quimica', 0):.2f}", help="Menor valor = más consistente")
    col3.metric("Desv. Rendimiento", f"{consistency_metrics.get('Rendiment', 0):.2f}", help="Menor valor = más consistente")
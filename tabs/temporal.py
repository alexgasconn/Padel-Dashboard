# tabs/temporal.py
import streamlit as st
import altair as alt
import pandas as pd

def render(filtered_df):
    st.subheader("Análisis Temporal")

    if filtered_df.empty:
        st.info("No hay datos para el análisis temporal con los filtros actuales.")
        return

    # --- Evolución Temporal ---
    # Asegurarse de que el dataframe esté ordenado por fecha
    df_sorted = filtered_df.sort_values("Date").reset_index()

    # Calcular media móvil para suavizar
    df_sorted['Rating_Rolling'] = df_sorted['Rating'].rolling(window=5, min_periods=1).mean()

    # Gráfico de Evolución del Rating
    rating_line = alt.Chart(df_sorted).mark_line(color='blue').encode(
        x=alt.X("Date:T", title="Fecha"),
        y=alt.Y("Rating_Rolling:Q", title="Rating (Media Móvil)", scale=alt.Scale(zero=False)),
        tooltip=["Date:T", "Rating_Rolling:Q"]
    ).properties(
        title="Evolución Temporal del Rating"
    ).interactive()
    st.altair_chart(rating_line, use_container_width=True)

    # --- Heatmap de Rendimiento por Día y Hora ---
    temp_df = filtered_df.copy()
    temp_df['Hour_Int'] = temp_df['Hour'].apply(lambda x: x.hour if pd.notna(x) else -1)
    
    heatmap_data = temp_df.groupby(["Weekday", "Hour_Int"]).agg(
        WinRate=("Result", lambda x: (x == 'W').mean() * 100),
        Partidos=("Result", "count")
    ).reset_index()
    
    # Ordenar los días de la semana
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("Hour_Int:O", title="Hora del día"),
        y=alt.Y("Weekday:N", title="Día de la semana", sort=weekday_order),
        color=alt.Color("WinRate:Q", title="Win Rate (%)", scale=alt.Scale(scheme="redyellowgreen", domain=[0, 100])),
        tooltip=["Weekday:N", "Hour_Int:O", alt.Tooltip("WinRate:Q", format=".1f"), "Partidos:Q"]
    ).properties(
        title="Win Rate por Día y Hora"
    )
    st.altair_chart(heatmap, use_container_width=True)
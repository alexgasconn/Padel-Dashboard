# tabs/lugares.py
import streamlit as st
import altair as alt

def render(filtered_df, locations_df):
    st.subheader("Análisis de Lugares")

    if locations_df.empty:
        st.info("No hay datos de lugares para mostrar con los filtros actuales.")
        return

    # Gráfico de Probabilidad de Victoria por Lugar
    location_prob_chart = alt.Chart(locations_df).mark_bar().encode(
        x=alt.X("Lugar:N", sort="-y", title="Lugar"),
        y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["Lugar", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Probabilidad de Victoria por Lugar")
    st.altair_chart(location_prob_chart, use_container_width=True)

    # Gráfico de Métricas de Rendimiento por Lugar
    location_metrics = alt.Chart(locations_df).mark_point(size=150, filled=True, opacity=0.8).encode(
        x=alt.X("Merit_Avg:Q", title="Rating Promedio"),
        y=alt.Y("Rendiment_Avg:Q", title="Rendimiento Promedio"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Prob. Victoria"),
        size=alt.Size("Total_Partidos:Q", scale=alt.Scale(range=[100, 500]), title="Partidos Jugados"),
        tooltip=["Lugar", "Merit_Avg", "Rendiment_Avg", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Métricas de Rendimiento por Lugar")
    st.altair_chart(location_metrics, use_container_width=True)
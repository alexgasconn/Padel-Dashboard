# tabs/jugadores.py
import streamlit as st
import altair as alt

def render(filtered_df, teammates_df):
    st.subheader("Análisis de Compañeros")

    if teammates_df.empty:
        st.info("No hay datos de compañeros para mostrar con los filtros actuales.")
        return

    # Gráfico de Probabilidad de Victoria por Compañero
    prob_chart = alt.Chart(teammates_df).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y", title="Compañero"),
        y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Probabilidad"),
        tooltip=["Compañero", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Probabilidad de Victoria por Compañero")
    st.altair_chart(prob_chart, use_container_width=True)

    # Gráfico de Dispersión: Química vs. Rendimiento
    scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.7).encode(
        x=alt.X("Quimica:Q", title="Química", scale=alt.Scale(zero=False)),
        y=alt.Y("Rendiment:Q", title="Rendimiento", scale=alt.Scale(zero=False)),
        color=alt.Color("Result:N", scale=alt.Scale(domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"])),
        size=alt.Size("Merit:Q", scale=alt.Scale(range=[50, 300]), title="Rating del Partido"),
        tooltip=["Teammate", "Quimica", "Rendiment", "Merit", "Result", "Date"]
    ).properties(title="Química vs. Rendimiento (Tamaño por Rating del Partido)")
    st.altair_chart(scatter, use_container_width=True)
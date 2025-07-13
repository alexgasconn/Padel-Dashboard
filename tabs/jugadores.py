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
        # size=alt.Size("Merit:Q", scale=alt.Scale(range=[50, 300]), title="Rating del Partido"),
        tooltip=["Teammate", "Quimica", "Rendiment", "Merit", "Result", "Date"]
    ).properties(title="Química vs. Rendimiento (Tamaño por Rating del Partido)")
    st.altair_chart(scatter, use_container_width=True)



    st.markdown("### Estadísticas de Compañeros")

    st.markdown(teammates_df.head(3))
    # Top compañeros por número de partidos
    top_partidos = teammates_df.sort_values("Total_Partidos", ascending=False).head(10)
    st.markdown("#### Compañeros con más partidos jugados")
    st.dataframe(top_partidos[["Compañero", "Total_Partidos", "Victorias", "Derrotas", "Probabilidad_Victoria"]])

    # Top compañeros por victorias
    top_victorias = teammates_df.sort_values("Victorias", ascending=False).head(10)
    st.markdown("#### Compañeros con más victorias")
    st.dataframe(top_victorias[["Compañero", "Victorias", "Total_Partidos", "Probabilidad_Victoria"]])

    # Mejores % victoria (mínimo 5 partidos)
    min_partidos = 5
    mejores_porcentaje = teammates_df[teammates_df["Total_Partidos"] >= min_partidos]
    mejores_porcentaje = mejores_porcentaje.sort_values("Probabilidad_Victoria", ascending=False).head(10)
    st.markdown(f"#### Mejores compañeros por % de victoria (mínimo {min_partidos} partidos)")
    st.dataframe(mejores_porcentaje[["Compañero", "Probabilidad_Victoria", "Total_Partidos", "Victorias"]])

    # Gráfico de barras: Top 5 compañeros por partidos jugados
    bar_top_partidos = alt.Chart(top_partidos.head(5)).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y"),
        y=alt.Y("Total_Partidos:Q"),
        color=alt.Color("Total_Partidos:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["Compañero", "Total_Partidos", "Victorias", "Probabilidad_Victoria"]
    ).properties(title="Top 5 compañeros por partidos jugados")
    st.altair_chart(bar_top_partidos, use_container_width=True)

    # Gráfico de barras: Top 5 compañeros por victorias
    bar_top_victorias = alt.Chart(top_victorias.head(5)).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y"),
        y=alt.Y("Victorias:Q"),
        color=alt.Color("Victorias:Q", scale=alt.Scale(scheme="greens")),
        tooltip=["Compañero", "Victorias", "Total_Partidos", "Probabilidad_Victoria"]
    ).properties(title="Top 5 compañeros por victorias")
    st.altair_chart(bar_top_victorias, use_container_width=True)

    # Gráfico de líneas: Evolución de % victoria con cada compañero (si hay fechas)
    if "Fecha" in teammates_df.columns:
        st.markdown("#### Evolución temporal de la probabilidad de victoria con cada compañero")
        line_chart = alt.Chart(teammates_df).mark_line(point=True).encode(
            x=alt.X("Fecha:T", title="Fecha"),
            y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria (%)"),
            color="Compañero:N",
            tooltip=["Compañero", "Probabilidad_Victoria", "Fecha"]
        ).properties(height=400)
        st.altair_chart(line_chart, use_container_width=True)

    # Estadísticas generales
    st.markdown("### Estadísticas Generales")
    total_partidos = teammates_df["Total_Partidos"].sum()
    total_victorias = teammates_df["Victorias"].sum()
    total_derrotas = teammates_df["Derrotas"].sum()
    media_victoria = teammates_df["Probabilidad_Victoria"].mean()
    st.metric("Total de partidos jugados con compañeros", total_partidos)
    st.metric("Total de victorias con compañeros", total_victorias)
    st.metric("Total de derrotas con compañeros", total_derrotas)
    st.metric("Media de % de victoria con compañeros", f"{media_victoria:.2f}%")
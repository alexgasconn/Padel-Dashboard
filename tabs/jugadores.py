# tabs/jugadores.py
import streamlit as st
import altair as alt
import pandas as pd


def render(filtered_df, teammates_df):
    st.subheader("Análisis de Compañeros")

    if teammates_df.empty:
        st.info("No hay datos de compañeros para mostrar con los filtros actuales.")
        return

    # Gráfico de Probabilidad de Victoria por Compañero
    prob_chart = alt.Chart(teammates_df).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y", title="Compañero"),
        y=alt.Y("Probabilidad_Victoria:Q",
                title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(
            scheme="redyellowgreen"), title="Probabilidad"),
        tooltip=["Compañero", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Probabilidad de Victoria por Compañero")
    st.altair_chart(prob_chart, use_container_width=True)

    # Gráfico de Dispersión: Química vs. Rendimiento
    scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.7).encode(
        x=alt.X("Quimica:Q", title="Química", scale=alt.Scale(zero=False)),
        y=alt.Y("Rendiment:Q", title="Rendimiento",
                scale=alt.Scale(zero=False)),
        color=alt.Color("Result:N", scale=alt.Scale(
            domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"])),
        # size=alt.Size("Merit:Q", scale=alt.Scale(range=[50, 300]), title="Rating del Partido"),
        tooltip=["Teammate", "Quimica", "Rendiment", "Merit", "Result", "Date"]
    ).properties(title="Química vs. Rendimiento (Tamaño por Rating del Partido)")
    st.altair_chart(scatter, use_container_width=True)

    st.markdown("### Estadísticas de Compañeros")

    # Cálculo de win rate real (Victorias / Total_Partidos)
    teammates_df = teammates_df.copy()
    teammates_df["WinRate"] = (
        teammates_df["Victorias"] / teammates_df["Total_Partidos"] * 100).round(2)

    # Top compañeros por win rate (mínimo 5 partidos)
    min_partidos = 5
    top_winrate = teammates_df[teammates_df["Total_Partidos"] >= min_partidos].sort_values(
        "WinRate", ascending=False).head(10)
    st.markdown(
        f"#### Mejores compañeros por win rate (mínimo {min_partidos} partidos)")
    cols = ["Compañero", "WinRate", "Total_Partidos", "Victorias", "Derrotas"]
    cols_presentes = [c for c in cols if c in top_winrate.columns]
    if not cols_presentes:
        st.warning(
            f"No se encontraron columnas esperadas en el DataFrame: {top_winrate.columns.tolist()}")
    else:
        st.dataframe(top_winrate[cols_presentes])
    st.write("Columnas en top_winrate:", top_winrate.columns.tolist())

    # Rachas de victorias/derrotas por compañero (si hay fechas)
    if "Fecha" in filtered_df.columns and "Teammate" in filtered_df.columns:
        st.markdown("#### Rachas recientes con compañeros")
        streaks = []
        for teammate, group in filtered_df.groupby("Teammate"):
            group = group.sort_values("Date")
            results = group["Result"].tolist()
            max_win_streak = max_streak = curr = 0
            for r in results:
                if r == "W":
                    curr += 1
                    max_win_streak = max(max_win_streak, curr)
                else:
                    curr = 0
            streaks.append(
                {"Compañero": teammate, "Mejor_Racha_Victorias": max_win_streak})
        streaks_df = pd.DataFrame(streaks).sort_values(
            "Mejor_Racha_Victorias", ascending=False).head(10)
        st.dataframe(streaks_df)

    # Boxplot/Violinplot de win rate por compañero (solo si hay suficientes datos)
    if len(teammates_df) >= 5:
        st.markdown("#### Distribución del win rate entre compañeros")
        box = alt.Chart(teammates_df).mark_boxplot(extent='min-max').encode(
            y=alt.Y("WinRate:Q", title="Win Rate (%)"),
            tooltip=["Compañero", "WinRate", "Total_Partidos"]
        ).properties(width=200, height=400)
        st.altair_chart(box, use_container_width=True)

        violin = alt.Chart(teammates_df).transform_density(
            "WinRate",
            as_=["WinRate", "density"],
            groupby=["Compañero"]
        ).mark_area(orient="horizontal", opacity=0.5).encode(
            y=alt.Y("Compañero:N", sort="-x"),
            x=alt.X("WinRate:Q"),
            color=alt.Color("Compañero:N", legend=None),
            tooltip=["Compañero"]
        ).properties(width=400, height=300)
        st.altair_chart(violin, use_container_width=True)

    # Evolución temporal del win rate (si hay fechas)
    if "Fecha" in teammates_df.columns:
        st.markdown("#### Evolución temporal del win rate con cada compañero")
        line_chart = alt.Chart(teammates_df).mark_line(point=True).encode(
            x=alt.X("Fecha:T", title="Fecha"),
            y=alt.Y("WinRate:Q", title="Win Rate (%)"),
            color="Compañero:N",
            tooltip=["Compañero", "WinRate", "Fecha"]
        ).properties(height=400)
        st.altair_chart(line_chart, use_container_width=True)

    # Estadísticas generales
    st.markdown("### Estadísticas Generales")
    total_partidos = teammates_df["Total_Partidos"].sum()
    total_victorias = teammates_df["Victorias"].sum()
    total_derrotas = teammates_df["Derrotas"].sum()
    media_winrate = teammates_df["WinRate"].mean()
    mejor_winrate = teammates_df["WinRate"].max()
    peor_winrate = teammates_df["WinRate"].min()
    st.metric("Total de partidos jugados con compañeros", total_partidos)
    st.metric("Total de victorias con compañeros", total_victorias)
    st.metric("Total de derrotas con compañeros", total_derrotas)
    st.metric("Media de win rate con compañeros", f"{media_winrate:.2f}%")
    st.metric("Mejor win rate", f"{mejor_winrate:.2f}%")
    st.metric("Peor win rate", f"{peor_winrate:.2f}%")

# tabs/nuevos_analisis.py
import streamlit as st
import pandas as pd
import altair as alt

def render(df, filtered_df, teammates_df, locations_df, hours_df):
    st.subheader("🎯 Insights Clave y Análisis Adicionales")

    if filtered_df.empty:
        st.info("No hay datos para mostrar análisis con los filtros actuales.")
        return

    # --- Factores de Éxito ---
    st.markdown("##### Diferencias Clave entre Victorias y Derrotas")
    success_factors = filtered_df.groupby("Result")[["Merit", "Quimica", "Rendiment", "Game-Diff"]].mean()
    
    if "W" in success_factors.index and "L" in success_factors.index:
        success_diff = success_factors.loc["W"] - success_factors.loc["L"]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("∆ Merit", f"+{success_diff.get('Merit', 0):.2f}")
        col2.metric("∆ Química", f"+{success_diff.get('Quimica', 0):.2f}")
        col3.metric("∆ Rendimiento", f"+{success_diff.get('Rendiment', 0):.2f}")
        col4.metric("∆ Dif. Juegos", f"+{success_diff.get('Game-Diff', 0):.2f}")
    else:
        st.write("No hay suficientes datos de victorias y derrotas para comparar.")

    st.divider()

    # --- Mejores y Peores Actuaciones ---
    st.markdown("##### Mejores y Peores Actuaciones (por Merit)")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**🏆 Top 5 Mejores Partidos**")
        best_games = filtered_df.nlargest(5, "Merit")[["Date", "Teammate", "Merit", "Result"]]
        st.dataframe(best_games.style.format({"Merit": "{:.2f}"}), use_container_width=True)
    with col2:
        st.write("**💔 Top 5 Peores Partidos**")
        worst_games = filtered_df.nsmallest(5, "Merit")[["Date", "Teammate", "Merit", "Result"]]
        st.dataframe(worst_games.style.format({"Merit": "{:.2f}"}), use_container_width=True)
        
    st.divider()

    # --- Insights Clave Generados ---
    st.markdown("##### 💡 Insights Clave")
    insights = []
    
    # Mejor compañero
    if not teammates_df.empty:
        best_teammate = teammates_df.iloc[0]
        if best_teammate['Total_Partidos'] > 2: # Añadir un umbral
             insights.append(f"🤝 Tu mejor compañero parece ser **{best_teammate['Compañero']}** con una probabilidad de victoria del **{best_teammate['Probabilidad_Victoria']:.1f}%**.")

    # Mejor lugar
    if not locations_df.empty:
        best_location = locations_df.iloc[0]
        if best_location['Total_Partidos'] > 2:
            insights.append(f"📍 Tu lugar preferido es **{best_location['Lugar']}** con una probabilidad de victoria del **{best_location['Probabilidad_Victoria']:.1f}%**.")

    # Mejor hora
    if not hours_df.empty:
        best_hour = hours_df.iloc[0]
        if best_hour['Total_Partidos'] > 2:
            insights.append(f"🕒 La hora a la que mejor rindes es **{best_hour['Hora']}** con una probabilidad de victoria del **{best_hour['Probabilidad_Victoria']:.1f}%**.")

    for insight in insights:
        st.success(insight)
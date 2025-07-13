# tabs/temporal.py
import streamlit as st
import altair as alt
import pandas as pd

def render(filtered_df):
    st.subheader("Análisis de Rendimiento a lo Largo del Tiempo")

    if filtered_df.empty:
        st.info("No hay datos para el análisis temporal con los filtros actuales.")
        return

    # --- Gráfico 1: Evolución del Rating y Forma Actual ---
    st.markdown("#### Evolución del Nivel y Estado de Forma")
    st.write("La línea azul muestra tu **Rating Acumulado** a lo largo del tiempo (tu nivel general). Los puntos de colores muestran tu **Merit promedio en los últimos 5 partidos** (tu estado de forma).")

    df_sorted = filtered_df.sort_values("Date").reset_index(drop=True)
    df_sorted['Rating_Acumulado'] = df_sorted['Merit'].cumsum()
    df_sorted['Forma_Actual (Merit Avg 5p)'] = df_sorted['Merit'].rolling(window=5, min_periods=1).mean()

    base = alt.Chart(df_sorted).encode(x=alt.X("Date:T", title="Fecha"))
    
    rating_line = base.mark_line(color='cornflowerblue', strokeWidth=3).encode(
        y=alt.Y('Rating_Acumulado:Q', title='Rating Acumulado', scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('Date:T', title='Fecha'), alt.Tooltip('Rating_Acumulado:Q', title='Rating Acumulado', format='.2f'), alt.Tooltip('Teammate:N', title='Compañero')]
    )

    form_points = base.mark_point(size=80, filled=True, opacity=0.8).encode(
        y=alt.Y('Forma_Actual (Merit Avg 5p):Q', title='Forma Actual (Merit Avg)', scale=alt.Scale(zero=True)),
        color=alt.Color('Forma_Actual (Merit Avg 5p):Q', scale=alt.Scale(scheme='redblue'), legend=alt.Legend(title='Forma (Merit Avg 5p)')),
        tooltip=[alt.Tooltip('Date:T', title='Fecha'), alt.Tooltip('Forma_Actual (Merit Avg 5p):Q', title='Forma (Merit Avg 5p)', format='.2f')]
    )

    combined_chart = alt.layer(rating_line, form_points).resolve_scale(y='independent').properties(title="Evolución de Rating Acumulado vs. Estado de Forma").interactive()
    st.altair_chart(combined_chart, use_container_width=True)
    st.divider()

    # --- Gráfico 2: Heatmap de Rendimiento por Día y Hora ---
    st.markdown("#### ¿Cuándo Juegas Mejor? Heatmap de Rendimiento Diario")
    st.write("Visualiza tu **% de Victorias** y tu **Merit Promedio** por día de la semana y hora del partido.")
    
    temp_df = filtered_df.copy()
    temp_df['Hour_Int'] = temp_df['Hour'].apply(lambda x: x.hour if pd.notna(x) else -1)
    
    heatmap_data_daily = temp_df.groupby(["Weekday", "Hour_Int"]).agg(
        WinRate=("Result", lambda x: (x == 'W').mean() * 100),
        Merit_Avg=("Merit", "mean"),
        Partidos=("Result", "count")
    ).reset_index()
    
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    metric_to_show_daily = st.selectbox(
        "Elige la métrica para el heatmap diario:",
        ["WinRate", "Merit_Avg"],
        format_func=lambda x: "% Victorias" if x == "WinRate" else "Merit Promedio",
        key="daily_heatmap_metric"
    )

    color_scale_daily = alt.Scale(scheme="redyellowgreen", domain=[0, 100]) if metric_to_show_daily == "WinRate" else alt.Scale(scheme="redblue")
    color_title_daily = "% Victorias" if metric_to_show_daily == "WinRate" else "Merit Promedio"

    heatmap_daily = alt.Chart(heatmap_data_daily).mark_rect().encode(
        x=alt.X("Hour_Int:O", title="Hora del día (24h)"),
        y=alt.Y("Weekday:N", title="Día de la semana", sort=weekday_order),
        color=alt.Color(f"{metric_to_show_daily}:Q", title=color_title_daily, scale=color_scale_daily),
        tooltip=[alt.Tooltip("Weekday:N", title="Día"), alt.Tooltip("Hour_Int:O", title="Hora"), alt.Tooltip("WinRate:Q", title="% Victorias", format=".1f"), alt.Tooltip("Merit_Avg:Q", title="Merit Promedio", format=".2f"), alt.Tooltip("Partidos:Q", title="Nº Partidos")]
    ).properties(title=f"Heatmap de {color_title_daily} por Día y Hora")
    st.altair_chart(heatmap_daily, use_container_width=True)
    st.divider()

    # --- NUEVO GRÁFICO 3: Heatmap de Rendimiento por Mes y Año ---
    st.markdown("#### Frecuencia y Rendimiento Mensual a lo Largo de los Años")
    st.write("Observa tus meses más activos y en cuáles tienes mejor rendimiento.")
    
    # Preparar datos
    monthly_data = filtered_df.groupby(["Year", "Month"]).agg(
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == 'W').mean() * 100)
    ).reset_index()

    month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    metric_to_show_monthly = st.selectbox(
        "Elige la métrica para el heatmap mensual:",
        ["Partidos", "WinRate"],
        format_func=lambda x: "Nº de Partidos" if x == "Partidos" else "% de Victorias",
        key="monthly_heatmap_metric"
    )
    
    color_scale_monthly = (
        alt.Scale(scheme="viridis") if metric_to_show_monthly == "Partidos" 
        else alt.Scale(scheme="redyellowgreen", domain=[0, 100])
    )
    color_title_monthly = "Nº de Partidos" if metric_to_show_monthly == "Partidos" else "% de Victorias"

    heatmap_monthly = alt.Chart(monthly_data).mark_rect().encode(
        x=alt.X('Month:N', title='Mes', sort=month_order),
        y=alt.Y('Year:O', title='Año', axis=alt.Axis(labelAngle=0)),
        color=alt.Color(f'{metric_to_show_monthly}:Q', title=color_title_monthly, scale=color_scale_monthly),
        tooltip=[
            alt.Tooltip('Year:O', title='Año'),
            alt.Tooltip('Month:N', title='Mes'),
            alt.Tooltip('Partidos:Q', title='Nº de Partidos'),
            alt.Tooltip('WinRate:Q', title='% Victorias', format='.1f')
        ]
    ).properties(
        title=f"Heatmap de {color_title_monthly} por Mes y Año"
    )

    st.altair_chart(heatmap_monthly, use_container_width=True)
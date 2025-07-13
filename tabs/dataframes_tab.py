# tabs/dataframes_tab.py
import streamlit as st
import pandas as pd

def render(df, teammates_df, locations_df, hours_df, opponents_df):
    st.subheader("Dataframes de Rendimiento Agregado")
    
    st.write("Aquí puedes ver las tablas de rendimiento agregado que se usan para los análisis. Los promedios y porcentajes se calculan sobre los datos filtrados.")

    # Pestañas para cada tabla de rendimiento
    tab_perf1, tab_perf2, tab_perf3, tab_perf4 = st.tabs(["👥 Compañeros", "📍 Lugares", "🕒 Horas", "⚔️ Rivales"])

    style_format = {
        'Win_Rate_Total': '{:.1f}%',
        'Win_Rate_Sin_Empates': '{:.1f}%',
        'Probabilidad_Victoria': '{:.1f}%',
        'Merit_Avg': '{:.2f}',
        'Quimica_Avg': '{:.2f}',
        'Rendiment_Avg': '{:.2f}',
        'GameDiff_Avg': '{:.2f}'
    }

    with tab_perf1:
        st.markdown("#### Rendimiento por Compañero")
        if not teammates_df.empty:
            st.dataframe(teammates_df.style.format(style_format), use_container_width=True)
        else:
            st.info("No hay datos de rendimiento de compañeros para los filtros seleccionados.")

    with tab_perf2:
        st.markdown("#### Rendimiento por Lugar")
        if not locations_df.empty:
            st.dataframe(locations_df.style.format(style_format), use_container_width=True)
        else:
            st.info("No hay datos de rendimiento por lugar para los filtros seleccionados.")

    with tab_perf3:
        st.markdown("#### Rendimiento por Hora")
        if not hours_df.empty:
            st.dataframe(hours_df.style.format(style_format), use_container_width=True)
        else:
            st.info("No hay datos de rendimiento por hora para los filtros seleccionados.")

    with tab_perf4:
        st.markdown("#### Rendimiento por Rival")
        if "Opponent" in df.columns and not opponents_df.empty:
            st.dataframe(opponents_df.style.format(style_format), use_container_width=True)
        else:
            st.info("No hay datos de rivales disponibles o no coinciden con los filtros.")
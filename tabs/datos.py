# tabs/datos.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render(filtered_df, teammates_df, locations_df, hours_df, opponents_df):
    st.subheader("Datos Completos Filtrados")
    
    # Búsqueda en los datos
    search_term = st.text_input("Buscar en los datos:", "")
    
    display_df = filtered_df.copy()
    if search_term:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    
    st.dataframe(
        display_df.sort_values("Date", ascending=False).reset_index(drop=True), 
        use_container_width=True
    )
    
    # Opciones de exportación
    st.subheader("Opciones de Exportación")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Datos Filtrados (CSV)",
            data=csv,
            file_name=f"padel_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Exportar resúmenes de rendimiento
        output = pd.ExcelWriter('rendimiento_padel.xlsx', engine='xlsxwriter')
        teammates_df.to_excel(output, sheet_name='Compañeros', index=False)
        locations_df.to_excel(output, sheet_name='Lugares', index=False)
        hours_df.to_excel(output, sheet_name='Horas', index=False)
        if not opponents_df.empty:
            opponents_df.to_excel(output, sheet_name='Rivales', index=False)
        output.close()
        
        with open('rendimiento_padel.xlsx', 'rb') as f:
            st.download_button(
                label="📊 Descargar Análisis de Rendimiento (Excel)",
                data=f,
                file_name=f"padel_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel"
            )
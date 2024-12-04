# Python libraries
import streamlit as st
from PIL import Image
import os

# User module files
from modelo_basico import mb

def main():

    #############
    # Main page #
    #############
    logo_path = os.path.join(os.path.dirname(__file__), "Credere_Logo2.png")

    st.sidebar.image(logo_path)
    options = ['Inicio', 'Modelo Basico']
    choice = st.sidebar.selectbox("Menu", options, key='1')

    if choice == 'Inicio':
        st.markdown(
            """
            <h1 style='text-align: center;'>Creador de informes financieros</h1>
            """,
            unsafe_allow_html=True,
        )
        st.image(logo_path, use_column_width=True)
        st.markdown(
            """
            <p style='text-align: center;'>Propiedad exclusiva de Credere Capital INC.</p>
            """,
            unsafe_allow_html=True,
        )
        pass

    elif choice == 'Modelo Basico':
        mb()

    else:
        st.stop()


main()
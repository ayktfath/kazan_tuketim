# app.py
import streamlit as st
from calculations.kazan_tuketim import run

st.set_page_config(
    page_title="Routeng Hesap Araçları",
    layout="centered"
)

run()

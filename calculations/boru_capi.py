import streamlit as st
from calculations.boru_capi import hava_yogunlugu_hesapla

st.title("CoolProp Test – Hava Yoğunluğu")

if st.button("Hesapla"):
    sonuc = hava_yogunlugu_hesapla()
    st.success(f"Havanın yoğunluğu: {sonuc:.4f} kg/m³")

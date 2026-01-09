import streamlit as st
from CoolProp.CoolProp import PropsSI


def run():
    st.title("🔥 Kazan Yakıt Tüketim Hesabı")
    st.caption("v1.2 | Son güncelleme: 10.01.2026")

    # -----------------------------
    # 1) Yakıt seçimi + LHV (kcal/Nm³)
    # -----------------------------
    yakıtlar = {
        "Doğalgaz (≈8250 kcal/Nm³)": {"lhv": 8250, "mix": "HEOS::Methane[0.95]&Ethane[0.05]"},
        "LNG / Metan ağırlıklı (≈9000 kcal/Nm³)": {"lhv": 9000, "mix": "HEOS::Methane[0.98]&Ethane[0.02]"},
        "LPG (≈22000 kcal/Nm³)": {"lhv": 22000, "mix": "HEOS::Propane[0.60]&n-Butane[0.40]"},
    }

    yakıt_secimi = st.selectbox("Yakıt türü", list(yakıtlar.keys()))
    lhv = yakıtlar[yakıt_secimi]["lhv"]
    mix = yakıtlar[yakıt_secimi]["mix"]

    st.caption(f"Seçilen yakıt için LHV (yaklaşık): **{lhv:,.0f} kcal/Nm³**")

    # LHV override (opsiyonel)
    with st.expander("⚙️ İleri ayarlar (LHV ve karışım)"):
        lhv = st.number_input("LHV (kcal/Nm³) - istersen elle düzelt", min_value=1.0, value=float(lhv), step=50.0)
        mix = st.text_input("CoolProp karışım tanımı (HEOS::...) - istersen değiştir", value=mix)

    # -----------------------------
    # 2) Kapasite birimi: kcal/h veya kW
    # -----------------------------
    birim = st.radio("Kazan kapasitesi birimi", ["kcal/h", "kW"], horizontal=True)

    if birim == "kcal/h":
        kazan_kcal_h = st.number_input("Kazan kapasitesi (kcal/h)", min_value=0.0, step=1000.0)
        kazan_kw = kazan_kcal_h / 860 if kazan_kcal_h > 0 else 0.0
    else:
        kazan_kw = st.number_input("Kazan kapasitesi (kW)", min_value=0.0, step=10.0)
        kazan_kcal_h = kazan_kw * 860 if kazan_kw > 0 else 0.0

    if kazan_kcal_h > 0:
        st.write(f"🔁 Eşdeğer kapasite: **{kazan_kw:,.2f} kW** |  **{kazan_kcal_h:,.0f} kcal/h**")

    verim = st.slider("Kazan verimi (%)", min_value=60, max_value=100, value=90)

    calisma_suresi = st.number_input(
        "Yıllık çalışma süresi (saat/yıl)",
        min_value=0,
        value=3000,
        step=100
    )

    st.markdown("---")
    st.markdown("### 📊 Hesaplama Sonuçları")

    # -----------------------------
    # 3) Hacimsel tüketim (Nm³/h, Nm³/yıl)
    # -----------------------------
    tuketim_saatlik_nm3 = 0.0
    tuketim_yillik_nm3 = 0.0

    if kazan_kcal_h > 0:
        # Formül: Kapasite / (Alt Isıl Değer * Verim)
        tuketim_saatlik_nm3 = kazan_kcal_h / (lhv * (verim / 100))
        st.success(f"⏱️ Saatlik yakıt tüketimi: **{tuketim_saatlik_nm3:.2f} Nm³/h**")

        if calisma_suresi > 0:
            tuketim_yillik_nm3 = tuketim_saatlik_nm3 * calisma_suresi
            st.info(f"📊 Yıllık yakıt tüketimi: **{tuketim_yillik_nm3:,.0f} Nm³/yıl**")

    # -----------------------------
    # 4) CoolProp ile yoğunluk: Nm³ -> kg dönüşümü
    # -----------------------------
    st.subheader("❄️ CoolProp ile Yoğunluk ve Kütlesel Debi")

    col1, col2 = st.columns(2)
    with col1:
        ref_kosul = st.selectbox("Nm³ referans şartı", ["Nm³ (0°C, 1.01325 bar)", "Sm³ (15°C, 1.01325 bar)"])

    if ref_kosul.startswith("Nm³"):
        T_ref_C = 0.0
    else:
        T_ref_C = 15.0
    P_ref_bar = 1.01325

    # İşletme şartları (opsiyonel)
    with st.expander("İşletme şartlarında da göster (opsiyonel)"):
        T_op_C = st.number_input("İşletme sıcaklığı (°C)", value=20.0, step=1.0)
        P_op_bar = st.number_input("İşletme basıncı (bar abs)", value=1.01325, step=0.1)

    def rho_from_coolprop(T_C: float, P_bar: float, fluid: str) -> float:
        T = T_C + 273.15
        P = P_bar * 1e5  # bar -> Pa
        return float(PropsSI("D", "T", T, "P", P, fluid))

    rho_ref = None
    rho_op = None

    try:
        rho_ref = rho_from_coolprop(T_ref_C, P_ref_bar, mix)
        st.write(f"✅ Referans şart yoğunluğu ρ_ref: **{rho_ref:.4f} kg/m³**")

        kwh_per_m3 = lhv / 860.0
        st.caption(f"Yaklaşık enerji eşdeğeri (LHV): **1 m³ ≈ {kwh_per_m3:.2f} kWh**")

        rho_op = rho_from_coolprop(T_op_C, P_op_bar, mix)
        st.write(f"✅ İşletme şart yoğunluğu ρ_op: **{rho_op:.4f} kg/m³** (T={T_op_C}°C, P={P_op_bar} bar abs)")

    except Exception as e:
        st.error("CoolProp yoğunluk hesabı başarısız oldu. Karışım tanımı veya şartlar uygun olmayabilir.")
        st.code(str(e))

    # 5) Kütlesel debi hesapla
    if tuketim_saatlik_nm3 > 0 and rho_ref is not None:
        kg_h = tuketim_saatlik_nm3 * rho_ref
        st
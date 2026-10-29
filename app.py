import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Pengaturan Halaman Web
st.set_page_config(
    page_title="Akuarimba SIC Dashboard",
    page_icon="🐟",
    layout="wide"
)

# Judul Utama Dashboard
st.title("🌊 AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Dashboard utama pemantauan kualitas air kolam/akuarium secara *real-time* untuk proyek Samsung Innovation Campus.")

# --- SIMULASI / TARIK DATA SENSOR TERKINI ---
# (Nanti bagian ini bisa dihubungkan ke database/API ESP32 via MQTT atau Firebase)
ph_val = 7.2
temp_val = 28.4
turbid_val = 12.5
light_val = 450
fish_sonar = 22.0

# --- BAGIAN 1: METRIK KARTU UTAMA ---
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Kadar pH Air", f"{ph_val} pH", "-0.2 (Normal)", delta_color="normal")
col2.metric("Suhu Air", f"{temp_val} °C", "+0.4 °C")
col3.metric("Kekeruhan", f"{turbid_val} NTU", "Jernih")
col4.metric("Cahaya Masuk", f"{light_val} Lux", "Cukup")
col5.metric("Aktivitas Sonar", f"{fish_sonar} cm", "Normal")

st.markdown("---")

# --- BAGIAN 2: GRAFIK TREN HISTORIS (PLOTLY) ---
st.subheader("📈 Grafik Tren Parameter Air (24 Jam Terakhir)")

# Data dummy historis untuk grafik
data_historis = pd.DataFrame({
    "Waktu": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
    "pH": [7.5, 7.3, 7.0, 6.8, 7.1, 7.2],
    "Suhu (°C)": [27.5, 27.2, 28.0, 29.1, 28.5, 28.4],
    "Kekeruhan (NTU)": [10, 11, 15, 14, 12, 12.5]
})

tab1, tab2, tab3 = st.tabs(["Grafik pH", "Grafik Suhu", "Grafik Kekeruhan"])

with tab1:
    fig_ph = px.line(data_historis, x="Waktu", y="pH", markers=True, title="Fluktuasi pH Air")
    fig_ph.add_hline(y=6.5, line_dash="dash", line_color="red", annotation_text="Batas Asam Min")
    fig_ph.add_hline(y=8.5, line_dash="dash", line_color="red", annotation_text="Batas Basa Maks")
    st.plotly_chart(fig_ph, use_container_width=True)

with tab2:
    fig_temp = px.line(data_historis, x="Waktu", y="Suhu (°C)", markers=True, title="Fluktuasi Suhu Air", color_discrete_sequence=["orange"])
    st.plotly_chart(fig_temp, use_container_width=True)

with tab3:
    fig_turbid = px.bar(data_historis, x="Waktu", y="Kekeruhan (NTU)", title="Tingkat Kekeruhan Air", color="Kekeruhan (NTU)")
    st.plotly_chart(fig_turbid, use_container_width=True)

# --- BAGIAN 3: STATUS KONTROL AKTUATOR & LOG ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⚙️ Status Aktuator Otomatis")
    st.info("🔹 **Pompa pH Up:** MATI (Kondisi pH Stabil)")
    st.info("🔹 **Pompa pH Down:** MATI (Kondisi pH Stabil)")
    st.info("🔹 **Lampu Buat (Artificial Light):** NYALA (Otomatis)")

with col_right:
    st.subheader("🚨 Log Peringatan & Sistem")
    st.warning("⚠️ [10:12:45] Sistem berjalan normal. Tidak ada anomali terdeteksi.")
    st.success("✅ [08:00:00] Kalibrasi sensor pH harian berhasil dilakukan.")

# Tombol Refresh Manual
if st.button("🔄 Perbarui Data Dashboard"):
    st.rerun()
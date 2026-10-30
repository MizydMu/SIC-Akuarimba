import streamlit as st
import pandas as pd
import plotly.express as px
import paho.mqtt.client as mqtt

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Akuarimba SIC Dashboard",
    page_icon="🐟",
    layout="wide"
)

# Inisialisasi Session State untuk menyimpan data sensor secara real-time
if 'ph' not in st.session_state:
    st.session_state.ph = "7.0"
if 'temp' not in st.session_state:
    st.session_state.temp = "27.0"
if 'turbid' not in st.session_state:
    st.session_state.turbid = "10.0"
if 'sonar' not in st.session_state:
    st.session_state.sonar = "25.0"
if 'light' not in st.session_state:
    st.session_state.light = "400"

# Fungsi Callback saat pesan MQTT diterima
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if msg.topic == "akuarimba/sensor/ph":
        st.session_state.ph = payload
    elif msg.topic == "akuarimba/sensor/temp":
        st.session_state.temp = payload
    elif msg.topic == "akuarimba/sensor/turbid":
        st.session_state.turbid = payload
    elif msg.topic == "akuarimba/sensor/sonar":
        st.session_state.sonar = payload
    elif msg.topic == "akuarimba/sensor/light":
        st.session_state.light = payload

# Inisialisasi MQTT Client (dijalankan sekali menggunakan st.cache_resource)
@st.cache_resource
def init_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect("broker.hivemq.com", 1883, 60)
        client.subscribe("akuarimba/sensor/#")
        client.loop_start()
    except Exception as e:
        print("Gagal koneksi MQTT:", e)
    return client

# Jalankan inisialisasi MQTT
init_mqtt_client()

# --- TAMPILAN DASHBOARD ---
st.title("🌊 AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Dashboard pemantauan kualitas air kolam secara *real-time* untuk Samsung Innovation Campus.")
st.markdown("---")

# Baris Metrik Utama
st.subheader("📊 Status Sensor Terkini (Live MQTT)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Kadar pH Air", f"{st.session_state.ph} pH")
col2.metric("Suhu Air", f"{st.session_state.temp} °C")
col3.metric("Kekeruhan", f"{st.session_state.turbid} NTU")
col4.metric("Cahaya", f"{st.session_state.light} Lux")
col5.metric("Sonar / Jarak", f"{st.session_state.sonar} cm")

st.markdown("---")

# Panel Informasi & Tombol Refresh
st.info("💡 **Petunjuk:** Ubah nilai sensor atau potensiometer pada simulasi Wokwi Anda, lalu klik tombol di bawah untuk melihat pembaruan data secara langsung.")

if st.button("🔄 Segarkan Data Dashboard"):
    st.rerun()
import streamlit as st
import paho.mqtt.client as mqtt
import time

st.set_page_config(page_title="Akuarimba SIC Dashboard", page_icon="🐟", layout="wide")

# Inisialisasi Session State
for key in ['ph', 'temp', 'turbid', 'sonar', 'light']:
    if key not in st.session_state:
        st.session_state[key] = "Menunggu..."

# Callback MQTT saat pesan masuk
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    topic = msg.topic
    if "ph" in topic:
        st.session_state.ph = payload
    elif "temp" in topic:
        st.session_state.temp = payload
    elif "turbid" in topic:
        st.session_state.turbid = payload
    elif "sonar" in topic:
        st.session_state.sonar = payload
    elif "light" in topic:
        st.session_state.light = payload

# Inisialisasi Koneksi MQTT (Singleton agar tidak terhubung ulang terus-menerus)
@st.cache_resource
def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.subscribe("akuarimba/sensor/#")
    client.loop_start()
    return client

start_mqtt()

# --- TAMPILAN DASHBOARD ---
st.title("🌊 AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Samsung Innovation Campus - Real-Time IoT Dashboard")
st.markdown("---")

st.subheader("📊 Status Sensor Terkini (Live MQTT)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Kadar pH Air", f"{st.session_state.ph} pH")
col2.metric("Suhu Air", f"{st.session_state.temp} °C")
col3.metric("Kekeruhan", f"{st.session_state.turbid} NTU")
col4.metric("Cahaya", f"{st.session_state.light} Lux")
col5.metric("Sonar / Jarak", f"{st.session_state.sonar} cm")

st.markdown("---")
st.info("💡 Data diperbarui otomatis dari simulasi Wokwi melalui Broker MQTT publik.")

# Tombol manual refresh jika diperlukan
if st.button("🔄 Perbarui Tampilan"):
    st.rerun()
import streamlit as st
import pandas as pd
import plotly.express as px
import paho.mqtt.client as mqtt
import threading

# Konfigurasi Halaman
st.set_page_config(page_title="Akuarimba Live Dashboard", page_icon="🐟", layout="wide")

st.title("🌊 AKUARIMBA: Real-Time IoT Dashboard")
st.markdown("Memantau kualitas air kolam secara langsung dari simulasi ESP32 (Wokwi).")
st.markdown("---")

# Variabel Global untuk menampung data sensor sementara
if 'sensor_data' not in st.session_state:
    st.session_state.ph = "7.0"
    st.session_state.temp = "27.0"
    st.session_state.turbid = "10.0"

# --- KONFIGURASI MQTT CLIENT ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_PH = "akuarimba/sensor/ph"
TOPIC_TEMP = "akuarimba/sensor/temp"
TOPIC_TURBID = "akuarimba/sensor/turbid"

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if msg.topic == TOPIC_PH:
        st.session_state.ph = payload
    elif msg.topic == TOPIC_TEMP:
        st.session_state.temp = payload
    elif msg.topic == TOPIC_TURBID:
        st.session_state.turbid = payload

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe("akuarimba/sensor/#")
    client.loop_start()

# Jalankan MQTT di background thread agar tidak memblokir Streamlit
@st.cache_resource
init_mqtt = lambda: start_mqtt()
try:
    init_mqtt()
except:
    pass

# --- TAMPILAN DASHBOARD ---
col1, col2, col3 = st.columns(3)

col1.metric("Kadar pH Air (Live)", f"{st.session_state.ph} pH")
col2.metric("Suhu Air (Live)", f"{st.session_state.temp} °C")
col3.metric("Kekeruhan (Live)", f"{st.session_state.turbid} NTU")

st.markdown("---")
st.info("💡 **Tips:** Putar potensiometer di Wokwi Anda, lalu klik tombol di bawah untuk melihat pembaruan data secara berkala.")

if st.button("🔄 Refresh Tampilan"):
    st.reruring = True
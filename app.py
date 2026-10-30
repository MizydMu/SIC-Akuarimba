import streamlit as st
import paho.mqtt.client as mqtt
import queue
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Akuarimba SIC Dashboard", page_icon="🐟", layout="wide")

# Auto-refresh halaman setiap 1 detik agar antrean pesan langsung terproses di layar
st_autorefresh(interval=1000, limit=None, key="frequent_refresh")

# Gunakan Queue agar thread MQTT aman berkomunikasi dengan Streamlit
if 'mqtt_queue' not in st.session_state:
    st.session_state.mqtt_queue = queue.Queue()

for key in ['ph', 'temp', 'turbid', 'sonar', 'light']:
    if key not in st.session_state:
        st.session_state[key] = "Menunggu..."

# Callback saat pesan MQTT masuk
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        topic = msg.topic
        st.session_state.mqtt_queue.put((topic, payload))
    except Exception as e:
        print("Error queue:", e)

# Inisialisasi MQTT Client (Singleton)
@st.cache_resource
def init_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="StreamlitDashboard_Akuarimba")
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.subscribe("akuarimba/sensor/#")
    client.loop_start()
    return client

init_mqtt()

# Proses pesan yang masuk dari antrean ke session_state secara aman
while not st.session_state.mqtt_queue.empty():
    topic, payload = st.session_state.mqtt_queue.get()
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
st.info("💡 Terhubung ke broker publik. Data diperbarui secara real-time dari simulasi Wokwi.")
import streamlit as st
import paho.mqtt.client as mqtt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Akuarimba SIC Dashboard", page_icon="🐟", layout="wide")

st_autorefresh(interval=2000, limit=None, key="emqx_refresh")

TOPIC_MAP = {
    "akuarimba/sensor/ph": "ph",
    "akuarimba/sensor/temp": "temp",
    "akuarimba/sensor/turbid": "turbid",
    "akuarimba/sensor/sonar": "sonar",
    "akuarimba/sensor/light": "light",
}

@st.cache_resource
def get_mqtt_client():
    # Penyimpanan data bersama (aman dibaca/ditulis dari thread lain)
    data = {k: "Menunggu..." for k in TOPIC_MAP.values()}
    data["_status"] = "Menghubungkan..."

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            data["_status"] = "Terhubung"
            client.subscribe("akuarimba/sensor/#")
        else:
            data["_status"] = f"Gagal (rc={rc})"

    def on_message(client, userdata, msg):
        key = TOPIC_MAP.get(msg.topic)
        if key:
            data[key] = msg.payload.decode("utf-8").strip()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="akuarimba-dashboard-streamlit",
        transport="websockets",
    )
    client.ws_set_options(path="/mqtt")   # path WebSocket EMQX
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async("broker.emqx.io", 8084, 60)
    client.loop_start()
    return data

data = get_mqtt_client()

# --- TAMPILAN DASHBOARD ---
st.title("🌊 AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Samsung Innovation Campus - Real-Time IoT Dashboard")
st.markdown("---")

st.subheader("📊 Status Sensor Terkini (EMQX Broker)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Kadar pH Air", f"{data['ph']} pH")
col2.metric("Suhu Air", f"{data['temp']} °C")
col3.metric("Kekeruhan", f"{data['turbid']} NTU")
col4.metric("Cahaya", f"{data['light']} Lux")
col5.metric("Sonar / Jarak", f"{data['sonar']} cm")

st.markdown("---")
st.info(f"💡 Status koneksi MQTT: **{data['_status']}** (broker.emqx.io via WSS)")
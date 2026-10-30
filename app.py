import streamlit as st
import paho.mqtt.client as mqtt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Akuarimba SIC Dashboard", page_icon="🐟", layout="wide")

st_autorefresh(interval=2000, limit=None, key="emqx_refresh")

for key in ['ph', 'temp', 'turbid', 'sonar', 'light']:
    if key not in st.session_state:
        st.session_state[key] = "Menunggu..."

@st.cache_resource
def get_mqtt_client():
    def on_connect(client, userdata, flags, rc, properties=None):
        client.subscribe("akuarimba/sensor/#")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
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
        except Exception as e:
            print("Error:", e)

    # Menggunakan WebSocket transport untuk menembus firewall Streamlit Cloud
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Mengaktifkan TLS agar kompatibel dengan port WSS 8443
        client.tls_set()
        client.connect("broker.emqx.io", 8443, 60)
        client.loop_start()
    except Exception as e:
        print("EMQX Connection failed:", e)
        
    return client

get_mqtt_client()

# --- TAMPILAN DASHBOARD ---
st.title("🌊 AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Samsung Innovation Campus - Real-Time IoT Dashboard")
st.markdown("---")

st.subheader("📊 Status Sensor Terkini (EMQX Broker)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Kadar pH Air", f"{st.session_state.ph} pH")
col2.metric("Suhu Air", f"{st.session_state.temp} °C")
col3.metric("Kekeruhan", f"{st.session_state.turbid} NTU")
col4.metric("Cahaya", f"{st.session_state.light} Lux")
col5.metric("Sonar / Jarak", f"{st.session_state.sonar} cm")

st.markdown("---")
st.info("💡 Terhubung ke broker.emqx.io via WebSocket Secure (WSS).")
import threading
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Akuarimba SIC Dashboard", page_icon="🐟", layout="wide")

st_autorefresh(interval=2000, limit=None, key="emqx_refresh")

# ==========================================================
# KONFIGURASI
# ==========================================================
BROKER = "broker.emqx.io"
WSS_PORT = 8084
PREFIX = "akuarimba/sensor/"
MAX_POINTS = 300                      # 300 titik x 3 detik = sekitar 15 menit riwayat
WIB = timezone(timedelta(hours=7))    # semua waktu ditampilkan dalam WIB

# Ambang batas pergerakan ikan (cm). Semakin dekat ke sensor, semakin anomali.
# FISH_ANOMALY_CM sengaja sama dengan batas alarm di sketch.ino (distance < 6.0).
FISH_ANOMALY_CM = 6.0     # di bawah ini  -> Anomali
FISH_WARNING_CM = 15.0    # di bawah ini  -> Waspada, di atasnya Normal

COLOR_OK = "#2e9e5b"
COLOR_WARN = "#d99a00"
COLOR_BAD = "#d64545"
COLOR_IDLE = "#8a8f98"

# key, label, satuan, warna garis grafik
SENSORS = [
    ("ph", "Kadar pH Air", "pH", "#6c5ce7"),
    ("temp", "Suhu Air", "°C", "#e17055"),
    ("turbid", "Kekeruhan", "NTU", "#b08968"),
    ("light", "Cahaya", "Lux", "#f0a500"),
    ("sonar", "Sonar / Jarak", "cm", "#0984e3"),
]


# ==========================================================
# KONEKSI MQTT (berjalan di thread terpisah, data disimpan di dict bersama)
# ==========================================================
@st.cache_resource
def get_state():
    state = {
        "lock": threading.Lock(),
        "latest": {k: None for k, *_ in SENSORS},
        "history": {k: deque(maxlen=MAX_POINTS) for k, *_ in SENSORS},
        "connected": False,
        "status": "Menghubungkan...",
        "count": 0,
        "last_time": None,
    }

    def on_connect(client, userdata, flags, rc, properties=None):
        with state["lock"]:
            if rc == 0:
                state["connected"] = True
                state["status"] = "Terhubung"
            else:
                state["connected"] = False
                state["status"] = f"Gagal (rc={rc})"
        if rc == 0:
            client.subscribe(PREFIX + "#", qos=0)

    def on_disconnect(client, userdata, flags, rc, properties=None):
        with state["lock"]:
            state["connected"] = False
            state["status"] = f"Terputus (rc={rc}), mencoba ulang..."

    def on_message(client, userdata, msg):
        if not msg.topic.startswith(PREFIX):
            return
        key = msg.topic[len(PREFIX):]
        if key not in state["latest"]:
            return
        try:
            value = float(msg.payload.decode("utf-8", errors="ignore").strip())
        except ValueError:
            return
        now = datetime.now(WIB)
        with state["lock"]:
            state["latest"][key] = value
            state["history"][key].append((now, value))
            state["count"] += 1
            state["last_time"] = now

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"akuarimba-dash-{uuid.uuid4().hex[:10]}",
        transport="websockets",
    )
    client.ws_set_options(path="/mqtt")
    client.tls_set()
    client.reconnect_delay_set(min_delay=2, max_delay=30)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect_async(BROKER, WSS_PORT, 60)
    client.loop_start()
    return state


state = get_state()

# Salin data ke variabel lokal supaya aman dibaca di thread utama
with state["lock"]:
    latest = dict(state["latest"])
    history = {k: list(v) for k, v in state["history"].items()}
    connected = state["connected"]
    status_text = state["status"]
    msg_count = state["count"]
    last_time = state["last_time"]


# ==========================================================
# FUNGSI BANTU
# ==========================================================
def show_chart(fig, key):
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key=key)


def fish_status(distance):
    """Mengembalikan (label, warna, deskripsi, tingkat anomali 0..1)."""
    if distance is None:
        return "Menunggu data", COLOR_IDLE, "Belum ada pembacaan dari sensor sonar.", 0.0
    score = max(0.0, min(1.0, (FISH_WARNING_CM - distance) / FISH_WARNING_CM))
    if distance < FISH_ANOMALY_CM:
        return ("Anomali", COLOR_BAD,
                "Ikan sangat dekat dengan sensor. Alarm darurat pada perangkat aktif.", score)
    if distance < FISH_WARNING_CM:
        return ("Waspada", COLOR_WARN,
                "Ikan mulai mendekati sensor. Pantau terus pergerakannya.", score)
    return ("Normal", COLOR_OK,
            "Ikan bergerak pada jarak aman dari sensor.", score)


def status_card(emoji, title, detail, color):
    st.markdown(
        f'<div style="border:2px solid {color};background:{color}1f;border-radius:14px;'
        f'padding:18px 16px;text-align:center;">'
        f'<div style="font-size:80px;line-height:1.1;">{emoji}</div>'
        f'<div style="font-size:26px;font-weight:700;color:{color};margin-top:4px;">{title}</div>'
        f'<div style="opacity:0.8;margin-top:4px;">{detail}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def make_chart(points, unit, color, sonar=False):
    times = [p[0] for p in points]
    values = [p[1] for p in points]
    fig = go.Figure(
        go.Scatter(
            x=times, y=values, mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate="%{x|%H:%M:%S}<br>%{y:.1f} " + unit + "<extra></extra>",
        )
    )
    if sonar:
        fig.add_hline(y=FISH_ANOMALY_CM, line_dash="dash", line_color=COLOR_BAD,
                      annotation_text="Anomali", annotation_position="bottom right")
        fig.add_hline(y=FISH_WARNING_CM, line_dash="dash", line_color=COLOR_WARN,
                      annotation_text="Waspada", annotation_position="top right")
    fig.update_layout(
        height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis=dict(title="Waktu (WIB)", tickformat="%H:%M:%S", nticks=4),
        yaxis=dict(title=unit),
    )
    return fig


# ==========================================================
# TAMPILAN DASHBOARD
# ==========================================================
st.title("AKUARIMBA: Smart Aquatic Monitoring System")
st.markdown("Samsung Innovation Campus - Real-Time IoT Dashboard")
st.markdown("---")

# --- Baris atas: status koneksi dan status pergerakan ikan ---
col_conn, col_fish = st.columns([1, 2])

with col_conn:
    st.subheader("Status koneksi")
    if connected:
        status_card("😊", "Terhubung", f"{BROKER} (WSS)", COLOR_OK)
    else:
        status_card("☹️", "Belum terhubung", status_text, COLOR_BAD)
    if last_time is not None:
        ago = int((datetime.now(WIB) - last_time).total_seconds())
        st.caption(f"Pesan diterima: {msg_count} | Data terakhir {ago} detik lalu")
    else:
        st.caption(f"Pesan diterima: {msg_count} | Belum ada data masuk")

with col_fish:
    st.subheader("Status pergerakan ikan")
    distance = latest["sonar"]
    label, color, desc, score = fish_status(distance)
    with st.container(border=True):
        left, right = st.columns([1, 1])
        with left:
            st.markdown(
                f'<div style="font-size:42px;font-weight:700;color:{color};line-height:1.1;">{label}</div>'
                f'<div style="opacity:0.8;margin-top:6px;">{desc}</div>',
                unsafe_allow_html=True,
            )
        with right:
            st.metric("Jarak ikan ke sensor",
                      f"{distance:.1f} cm" if distance is not None else "Menunggu...")
        st.progress(score, text=f"Tingkat anomali: {int(score * 100)}%")
        st.caption(
            f"Normal: {FISH_WARNING_CM:.0f} cm atau lebih | "
            f"Waspada: {FISH_ANOMALY_CM:.0f} sampai {FISH_WARNING_CM:.0f} cm | "
            f"Anomali: kurang dari {FISH_ANOMALY_CM:.0f} cm"
        )

st.markdown("---")

# --- Data sensor: satu kolom per data, lengkap dengan grafiknya ---
st.subheader("Data sensor terkini")
cols = st.columns(len(SENSORS))

for col, (key, name, unit, line_color) in zip(cols, SENSORS):
    with col:
        with st.container(border=True):
            value = latest[key]
            st.metric(name, f"{value:.1f} {unit}" if value is not None else "Menunggu...")
            points = history[key]
            if points:
                show_chart(make_chart(points, unit, line_color, sonar=(key == "sonar")),
                           key=f"chart_{key}")
            else:
                st.caption("Grafik akan muncul setelah data pertama diterima.")

st.caption(f"Data diterima dari {BROKER} lewat WebSocket Secure. Grafik menyimpan sekitar 15 menit terakhir.")

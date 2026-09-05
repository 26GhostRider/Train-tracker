import json
import threading
import time
import queue
import streamlit as st
import stomp

st.set_page_config(page_title="Network Rail Train Movements Tracker", layout="wide")


@st.cache_resource
def get_message_queue():
    return queue.Queue()


msg_queue = get_message_queue()

if "movements" not in st.session_state:
    st.session_state.movements = []
if "connection_status" not in st.session_state:
    st.session_state.connection_status = "Connecting to TRUST Feed..."


class TrustListener(stomp.ConnectionListener):
    def on_error(self, frame):
        msg_queue.put({"type": "status", "text": f"Error: {frame.body}"})

    def on_disconnected(self):
        msg_queue.put({"type": "status", "text": "Disconnected from feed"})

    def on_message(self, frame):
        try:
            data = json.loads(frame.body)
            for message in data:
                body = message.get("body", message)
                train_id = body.get("train_id")
                event_type = body.get("event_type")
                location = body.get("reporting_stanox", "Unknown")
                toc_id = body.get("toc_id")

                if train_id:
                    movement_record = {
                        "headcode": train_id,
                        "event": event_type,
                        "stanox_location": location,
                        "toc_id": toc_id,
                        "timestamp": body.get("actual_timestamp", "N/A")
                    }
                    msg_queue.put({"type": "movement", "data": movement_record})
        except Exception as e:
            print(f"Error parsing message: {e}")


def run_trust_client():
    host = 'datafeeds.networkrail.co.uk'
    port = 61618  # Network Rail STOMP port
    username = st.secrets["NWR_USERNAME"]
    password = st.secrets["NWR_PASSWORD"]
    topic = '/topic/TRAIN_MVT_ALL_TOC'

    try:
        conn = stomp.Connection(
            host_and_ports=[(host, port)],
            keepalive=True,
            vhost=host,
            heartbeats=(10000, 10000)
        )
        conn.set_listener('', TrustListener())
        conn.connect(username, password, wait=True)
        conn.subscribe(destination=topic, id=1, ack='auto')
        msg_queue.put({"type": "status", "text": "Connected to TRUST Feed!"})

        while True:
            time.sleep(1)
    except Exception as e:
        msg_queue.put({"type": "status", "text": f"Connection failed: {str(e)}"})


if "thread_started" not in st.session_state:
    st.session_state.thread_started = True
    t = threading.Thread(target=run_trust_client, daemon=True)
    t.start()

while not msg_queue.empty():
    item = msg_queue.get()
    if item["type"] == "status":
        st.session_state.connection_status = item["text"]
    elif item["type"] == "movement":
        st.session_state.movements.insert(0, item["data"])
        if len(st.session_state.movements) > 100:
            st.session_state.movements.pop()

st.title("🚆 Network Rail Train Movements & Headcodes")

st.sidebar.subheader("Feed Status")
st.sidebar.write(st.session_state.connection_status)

st.subheader("Live Train Movement Events")
st.write(f"Tracked Events: {len(st.session_state.movements)}")

if st.session_state.movements:
    st.dataframe(st.session_state.movements[:30], use_container_width=True)
else:
    st.info(
        "Listening for live train movement reports... (Movements stream in continuously as trains pass reporting points).")

time.sleep(2)
st.rerun()
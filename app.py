import json
import threading
import time
import streamlit as st
import stomp

st.set_page_config(page_title="Train Describer Tracker", layout="wide")

# Initialize session state
if "active_trains" not in st.session_state:
    st.session_state.active_trains = {}
if "system_logs" not in st.session_state:
    st.session_state.system_logs = []
if "connection_status" not in st.session_state:
    st.session_state.connection_status = "Connecting..."


class TDListener(stomp.ConnectionListener):
    def on_error(self, frame):
        st.session_state.connection_status = f"Error: {frame.body}"

    def on_disconnected(self):
        st.session_state.connection_status = "Disconnected from feed"

    def on_message(self, frame):
        try:
            data = json.loads(frame.body)
            for message in data:
                msg_type = message.get("msg_type")

                st.session_state.system_logs.insert(0, {
                    "type": msg_type,
                    "raw": message
                })
                if len(st.session_state.system_logs) > 100:
                    st.session_state.system_logs.pop()

                if msg_type in ["CA", "CT"]:
                    area = message.get("area")
                    berth = message.get("to", message.get("berth"))
                    headcode = message.get("descript")

                    if berth and headcode:
                        st.session_state.active_trains[berth] = {
                            "headcode": headcode,
                            "area": area,
                            "event": msg_type
                        }

                elif msg_type == "CB":
                    berth = message.get("berth")
                    if berth in st.session_state.active_trains:
                        del st.session_state.active_trains[berth]

        except Exception as e:
            print(f"Error parsing TD message: {e}")


def run_stomp_client():
    host = 'datafeeds.networkrail.co.uk'
    port = 61613
    username = 'YOUR_USERNAME'
    password = 'YOUR_PASSWORD'
    topic = '/topic/TD_SE_AREA'

    try:
        conn = stomp.Connection([(host, port)])
        conn.set_listener('', TDListener())
        conn.connect(username, password, wait=True)
        conn.subscribe(destination=topic, id=1, ack='auto')
        st.session_state.connection_status = "Connected successfully!"

        # Keep the thread alive
        while True:
            time.sleep(1)
    except Exception as e:
        st.session_state.connection_status = f"Connection failed: {str(e)}"


# Start the listener in a background thread only once
if "thread_started" not in st.session_state:
    st.session_state.thread_started = True
    t = threading.Thread(target=run_stomp_client, daemon=True)
    t.start()

# --- UI Layout ---
st.title("🚆 Network Rail Train Describer & Control Logs")

# Sidebar status
st.sidebar.subheader("Feed Status")
st.sidebar.write(st.session_state.connection_status)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Active Train Headcodes")
    st.write(f"Tracked Berths: {len(st.session_state.active_trains)}")
    if st.session_state.active_trains:
        st.json(st.session_state.active_trains)
    else:
        st.info("Waiting for incoming TD data stream...")

with col2:
    st.subheader("Control Logs Stream")
    st.write(f"Total Log Entries: {len(st.session_state.system_logs)}")
    if st.session_state.system_logs:
        st.dataframe(st.session_state.system_logs[:20], use_container_width=True)
    else:
        st.info("No logs recorded yet.")

# Auto-refresh to pull latest messages into the UI
time.sleep(2)
st.rerun()
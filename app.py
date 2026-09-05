import json
import threading
import time
import streamlit as st
import stomp

# Configure the Streamlit page
st.set_page_config(page_title="Train Describer Tracker", layout="wide")

# Initialize session state for storing live data safely across reruns
if "active_trains" not in st.session_state:
    st.session_state.active_trains = {}
if "system_logs" not in st.session_state:
    st.session_state.system_logs = []


class TDListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print(f"Received error: {frame.body}")

    def on_message(self, frame):
        try:
            data = json.loads(frame.body)
            for message in data:
                msg_type = message.get("msg_type")

                # Append to control logs
                st.session_state.system_logs.insert(0, {
                    "type": msg_type,
                    "raw": message
                })
                if len(st.session_state.system_logs) > 100:
                    st.session_state.system_logs.pop()

                # Parse Train Describer movements
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


@st.cache_resource
def start_stomp_listener():
    # Replace with your Network Rail Data Feed credentials
    host = 'datafeeds.networkrail.co.uk'
    port = 61613
    username = 'YOUR_USERNAME'
    password = 'YOUR_PASSWORD'
    topic = '/topic/TD_SE_AREA'

    conn = stomp.Connection([(host, port)])
    conn.set_listener('', TDListener())
    conn.connect(username, password, wait=True)
    conn.subscribe(destination=topic, id=1, ack='auto')


# Start background listener thread
try:
    start_stomp_listener()
except Exception as e:
    st.sidebar.error(f"STOMP Connection Error: {e}")

# Streamlit User Interface Layout
st.title("🚆 Network Rail Train Describer & Control Logs")

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
        # Display latest logs
        st.dataframe(st.session_state.system_logs[:20], use_container_width=True)
    else:
        st.info("No logs recorded yet.")

# Auto-refresh the Streamlit app every few seconds to show live updates
time.sleep(2)
st.rerun()
import json
import threading
from flask import Flask, jsonify
import stomp

app = Flask(__name__)

# In-memory store for current berth headcodes and control logs
active_trains = {}
system_logs = []


class TDListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print(f"Received error: {frame.body}")

    def on_message(self, frame):
        try:
            data = json.loads(frame.body)
            for message in data:
                msg_type = message.get("msg_type")

                # Log all incoming messages for control monitoring
                system_logs.append({
                    "type": msg_type,
                    "raw": message
                })
                # Keep the last 100 logs in memory to prevent memory bloat
                if len(system_logs) > 100:
                    system_logs.pop(0)

                # Train Describer movement types
                # 'CA' = Interpose (new headcode entered)
                # 'CT' = Step (headcode moves between berths)
                if msg_type in ["CA", "CT"]:
                    area = message.get("area")
                    berth = message.get("to", message.get("berth"))
                    headcode = message.get("descript")

                    if berth and headcode:
                        active_trains[berth] = {
                            "headcode": headcode,
                            "area": area,
                            "event": msg_type
                        }

                elif msg_type == "CB":  # Cancel description
                    berth = message.get("berth")
                    if berth in active_trains:
                        del active_trains[berth]

        except Exception as e:
            print(f"Error parsing TD message: {e}")


def start_stomp_listener():
    # Replace with your Network Rail Data Feed credentials and host/port
    host = 'datafeeds.networkrail.co.uk'
    port = 61613
    username = 'YOUR_USERNAME'
    password = 'YOUR_PASSWORD'
    topic = '/topic/TD_SE_AREA'  # South East area feed covering Crystal Palace

    conn = stomp.Connection([(host, port)])
    conn.set_listener('', TDListener())
    conn.connect(username, password, wait=True)
    conn.subscribe(destination=topic, id=1, ack='auto')
    print(f"Connected to Train Describer feed on {topic}")


@app.route('/api/live-headcodes', methods=['GET'])
def get_live_headcodes():
    return jsonify({
        "tracked_berths_count": len(active_trains),
        "trains": active_trains
    })


@app.route('/api/control-logs', methods=['GET'])
def get_control_logs():
    return jsonify({
        "total_logs": len(system_logs),
        "logs": system_logs
    })


if __name__ == '__main__':
    # Start the STOMP consumer thread in the background
    t = threading.Thread(target=start_stomp_listener, daemon=True)
    t.start()

    # Run Flask app
    app.run(debug=True, port=5000)
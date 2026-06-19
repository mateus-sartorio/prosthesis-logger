import json
import ssl
import time
import paho.mqtt.client as mqtt

# --- Configuration ---
BROKER = "1c3070463886424684be8c4f3c5941fe.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "mateus"
PASSWORD = "MateusTest123"
TOPIC = "prothesis/logs/raw"

# --- Your Exact Payload ---
payload_data = [
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0},
    {"cJ": -4481.79, "cJl": -500, "cJp": 0.42, "cP": 0, "cPl": 0, "cPp": 0.5, "pJ": 0, "pP": 0}
]

# Convert python list/dict straight to a clean JSON string
json_payload = json.dumps(payload_data)

# Track connection status across loops safely
connected = False

# --- Callback functions ---
def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    # In Paho VERSION2, rc is a ReasonCode object. Its integer value is evaluated or compared directly.
    if rc == 0:
        print("✅ Successfully connected to HiveMQ Cloud!")
        connected = True
    else:
        print(f"❌ Connection failed with reason code: {rc}")

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    # Successfully handles modern MQTT v5 callback argument length
    print(f"📥 Broker acknowledged receipt (Message ID: {mid})")

def on_disconnect(client, userdata, flags, rc, properties=None):
    global connected
    print(f"⚠️ Disconnected from broker. Reason: {rc}")
    connected = False

# --- Main Logic ---
# Initialize modern Paho Client using Callback Version 2
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# Link our tracking functions
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

# Configure secure TLS layout for Port 8883
client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

# Set cluster authentication credentials
client.username_pw_set(USERNAME, PASSWORD)

print("Connecting to broker...")
client.connect(BROKER, PORT, keepalive=60)

# Start background network loop thread to maintain connection silently
client.loop_start()

# Main infinite transmission loop
try:
    print("🚀 Starting periodic publishing loop... (Press Ctrl+C to stop)")
    while True:
        if connected:
            result = client.publish(TOPIC, json_payload, qos=1)
            
            # Target the `.rc` attribute rather than the whole result tuple/object
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Payload cleanly sent to topic: {TOPIC} (Local ID: {result.mid})")
            else:
                print(f"❌ Failed to publish packet locally, internal error: {result.rc}")
        else:
            print("⏳ Waiting for connection to establish...")
        
        # Pause execution for exactly 1 second
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Stopping loop gracefully...")

finally:
    # Stop background thread loop and sever network connection cleanly upon termination
    client.loop_stop()
    client.disconnect()
    print("👋 Cleaned up and exited.")
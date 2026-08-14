try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String, Float32
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

import json
import time
import paho.mqtt.client as mqtt
import threading

class MQTTBridgeNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('mqtt_bridge_node')
            self.declare_parameter('mqtt_broker', 'test.mosquitto.org')
            self.broker_address = self.get_parameter('mqtt_broker').get_parameter_value().string_value
            
            # Subscribe to system health and state topics
            self.health_sub = self.create_subscription(String, '/system/health', self.health_callback, 10)
            self.battery_sub = self.create_subscription(Float32, '/system/battery', self.battery_callback, 10)
            self.get_logger().info(f'MQTT Bridge Node initialized. Connecting to {self.broker_address}')
        else:
            self.broker_address = 'test.mosquitto.org'
            print(f"[INFO] MQTT Bridge Node initialized. Connecting to {self.broker_address}")

        # Initialize MQTT Client
        self.mqtt_client = mqtt.Client(client_id=f"agro_ai_robot_{int(time.time())}")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        # Connect to broker in a separate thread so it doesn't block
        threading.Thread(target=self.connect_mqtt, daemon=True).start()

        if HAS_ROS:
            # Timer to publish telemetry periodically
            self.timer = self.create_timer(2.0, self.publish_telemetry)
        
        # Internal state
        self.latest_health = "NOMINAL"
        self.latest_battery = 100.0

    def connect_mqtt(self):
        try:
            self.mqtt_client.connect(self.broker_address, 1883, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.log_info(f"Failed to connect to MQTT broker: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log_info("Successfully connected to MQTT Broker")
            client.subscribe('command/agro_ai_robot_001')
            self.log_info("Subscribed to command/agro_ai_robot_001")
        else:
            self.log_info(f"Failed to connect, return code {rc}")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def log_debug(self, msg):
        if HAS_ROS: self.get_logger().debug(msg)
        else: print(f"[DEBUG] {msg}")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if payload.get('command') == 'E-STOP':
                self.latest_health = 'E-STOP'
                self.log_info("CRITICAL: Received E-STOP command from dashboard! Halting machinery.")
        except Exception as e:
            self.log_info(f"Failed to parse command message: {e}")

    def health_callback(self, msg):
        self.latest_health = msg.data
        self.log_debug(f'Received health update: {self.latest_health}')

    def battery_callback(self, msg):
        self.latest_battery = msg.data
        self.log_debug(f'Received battery update: {self.latest_battery}')

    def publish_telemetry(self):
        # Publish to an MQTT broker
        payload = {
            'timestamp': time.time(),
            'device_id': 'agro_ai_robot_001',
            'health': self.latest_health,
            'battery_level': self.latest_battery
        }
        
        # Publish only if connected
        try:
            self.mqtt_client.publish('telemetry/agro_ai_robot_001', json.dumps(payload))
            self.log_debug(f'[MQTT PUBLISH] Topic: telemetry/agro_ai_robot_001 | Payload: {json.dumps(payload)}')
        except Exception as e:
            self.log_info(f"Failed to publish MQTT message: {e}")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = MQTTBridgeNode()
        
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()
    else:
        node = MQTTBridgeNode()
        # Mock loop publishing data every 2 seconds
        try:
            while True:
                node.latest_battery = max(0.0, node.latest_battery - (1 if time.time() % 10 > 8 else 0))
                node.publish_telemetry()
                time.sleep(2.0)
        except KeyboardInterrupt:
            print("Stopping mock MQTT publisher.")
            node.mqtt_client.loop_stop()

if __name__ == '__main__':
    main()

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

class MQTTBridgeNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('mqtt_bridge_node')
            self.declare_parameter('mqtt_broker', 'iot.eclipse.org')
        
            # Subscribe to system health and state topics
            self.health_sub = self.create_subscription(
                String,
                '/system/health',
                self.health_callback,
                10
            )
            self.battery_sub = self.create_subscription(
                Float32,
                '/system/battery',
                self.battery_callback,
                10
            )
            
            self.get_logger().info('MQTT Bridge Node initialized. Mocking MQTT telemetry publishing.')
            
            # Timer to publish telemetry periodically
            self.timer = self.create_timer(5.0, self.publish_telemetry)
        
        # Mock MQTT state
        self.latest_health = "UNKNOWN"
        self.latest_battery = 0.0

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def log_debug(self, msg):
        if HAS_ROS: self.get_logger().debug(msg)
        else: print(f"[DEBUG] {msg}")

    def health_callback(self, msg):
        self.latest_health = msg.data
        self.log_debug(f'Received health update: {self.latest_health}')

    def battery_callback(self, msg):
        self.latest_battery = msg.data
        self.log_debug(f'Received battery update: {self.latest_battery}')

    def publish_telemetry(self):
        # Mock publishing to an MQTT broker
        payload = {
            'timestamp': time.time(),
            'device_id': 'agro_ai_robot_001',
            'health': self.latest_health,
            'battery_level': self.latest_battery
        }
        
        # In a real implementation, this would use paho-mqtt or similar to publish
        self.log_info(f'[MOCK MQTT PUBLISH] Topic: telemetry/agro_ai_robot_001 | Payload: {json.dumps(payload)}')


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
        node.publish_telemetry()

if __name__ == '__main__':
    main()

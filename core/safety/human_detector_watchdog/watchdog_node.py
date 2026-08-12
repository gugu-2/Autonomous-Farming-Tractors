try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String, Bool
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

import json

class HumanDetectorWatchdog(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('human_detector_watchdog')
            self.yolo_sub = self.create_subscription(
                String,
                '/perception/yolo/detections',
                self.detection_callback,
                10)
            self.estop_pub = self.create_publisher(Bool, '/safety/estop_trigger', 10)
        
        self.safety_radius_meters = 5.0
        self.log_info("Human Detector Watchdog initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def detection_callback(self, msg):
        # Mock detection logic
        if HAS_ROS:
            try:
                detections = json.loads(msg.data)
                for det in detections:
                    if det.get('class') == 'person' and det.get('distance', 10.0) < self.safety_radius_meters:
                        self.log_info("HUMAN DETECTED IN SAFETY RADIUS! TRIGGERING E-STOP!")
                        stop_msg = Bool()
                        stop_msg.data = True
                        self.estop_pub.publish(stop_msg)
                        return
            except json.JSONDecodeError:
                pass
        else:
            self.log_info("Evaluated YOLO detections for safety breaches.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = HumanDetectorWatchdog()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = HumanDetectorWatchdog()
        node.detection_callback(None)

if __name__ == '__main__':
    main()

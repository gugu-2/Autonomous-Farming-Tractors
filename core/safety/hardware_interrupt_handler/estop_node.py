try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Bool, String
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class EStopNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('estop_node')
            self.watchdog_sub = self.create_subscription(
                Bool,
                '/safety/estop_trigger',
                self.trigger_callback,
                10)
            self.hw_button_sub = self.create_subscription(
                Bool,
                '/hardware/physical_estop',
                self.trigger_callback,
                10)
            # Publishes to all actuator nodes to halt immediately
            self.halt_pub = self.create_publisher(Bool, '/actuator/halt_all', 10)
        
        self.estop_active = False
        self.log_info("Hardware Interrupt E-Stop Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def trigger_callback(self, msg):
        if HAS_ROS:
            if msg.data and not self.estop_active:
                self.log_info(">>> EMERGENCY STOP ACTIVATED <<< Halting all actuators!")
                self.estop_active = True
                halt_msg = Bool()
                halt_msg.data = True
                self.halt_pub.publish(halt_msg)
        else:
            self.log_info("Processed potential E-Stop trigger.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = EStopNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = EStopNode()
        node.trigger_callback(None)

if __name__ == '__main__':
    main()

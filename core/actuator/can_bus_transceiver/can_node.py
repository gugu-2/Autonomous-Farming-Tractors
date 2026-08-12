try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from std_msgs.msg import Bool
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class CANBusTransceiverNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('can_bus_transceiver_node')
            self.cmd_sub = self.create_subscription(
                Twist,
                '/actuator/cmd_vel',
                self.cmd_callback,
                10)
            self.halt_sub = self.create_subscription(
                Bool,
                '/actuator/halt_all',
                self.halt_callback,
                10)
        
        self.halted = False
        self.log_info("CAN Bus Transceiver Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def halt_callback(self, msg):
        if HAS_ROS:
            if msg.data:
                self.halted = True
                self.log_info("HALT RECEIVED: Disabling all CAN Bus transmissions!")
                # Transmit 0x00 to all critical CAN IDs
        else:
            self.log_info("Processed halt command.")

    def cmd_callback(self, msg):
        if self.halted:
            return
            
        if HAS_ROS:
            # Mock converting Twist to J1939 CAN Frame
            self.log_info(f"Transmitting CAN Frame: Steer={msg.angular.z}, Speed={msg.linear.x}")
        else:
            self.log_info("Processed cmd_vel to CAN frame.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = CANBusTransceiverNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = CANBusTransceiverNode()
        node.cmd_callback(None)

if __name__ == '__main__':
    main()

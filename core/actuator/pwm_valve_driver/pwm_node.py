try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float32MultiArray, Bool
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class PWMValveDriverNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('pwm_valve_driver_node')
            self.cmd_sub = self.create_subscription(
                Float32MultiArray,
                '/actuator/hydraulic_cmds',
                self.cmd_callback,
                10)
            self.halt_sub = self.create_subscription(
                Bool,
                '/actuator/halt_all',
                self.halt_callback,
                10)
        
        self.halted = False
        self.log_info("PWM Valve Driver Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def halt_callback(self, msg):
        if HAS_ROS:
            if msg.data:
                self.halted = True
                self.log_info("HALT RECEIVED: Dropping all PWM signals to 0% duty cycle!")
        else:
            self.log_info("Processed halt command.")

    def cmd_callback(self, msg):
        if self.halted:
            return
            
        if HAS_ROS:
            # Mock converting floats [-1.0, 1.0] to PWM duty cycles
            self.log_info(f"Outputting PWM Duty Cycles: {msg.data}")
        else:
            self.log_info("Processed hydraulic cmds to PWM.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = PWMValveDriverNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = PWMValveDriverNode()
        node.cmd_callback(None)

if __name__ == '__main__':
    main()

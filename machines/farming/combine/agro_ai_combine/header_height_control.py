import time
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float32
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class HeaderHeightControlNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('header_height_control_node')
            self.declare_parameter('target_cut_height_m', 0.15)
            self.declare_parameter('kp', 1.2)
            self.declare_parameter('ki', 0.1)
            self.declare_parameter('kd', 0.05)
            
            self.target_height = self.get_parameter('target_cut_height_m').value
            self.kp = self.get_parameter('kp').value
            self.ki = self.get_parameter('ki').value
            self.kd = self.get_parameter('kd').value
            
            self.lidar_sub = self.create_subscription(Float32, '/sensor/ground_distance', self.ground_dist_cb, 10)
            self.actuator_pub = self.create_publisher(Float32, '/actuator/header_hydraulic_cmd', 10)
        else:
            self.target_height = 0.15
            self.kp = 1.2
            self.ki = 0.1
            self.kd = 0.05
            
        self.integral_error = 0.0
        self.prev_error = 0.0
        self.last_time = time.time()
        
        self.log_info("Combine Header Height PID Controller initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def ground_dist_cb(self, msg):
        current_height = msg.data if HAS_ROS else msg
        current_time = time.time()
        dt = current_time - self.last_time
        if dt <= 0: return
        
        error = self.target_height - current_height
        self.integral_error += error * dt
        derivative_error = (error - self.prev_error) / dt
        
        # PID Equation
        raw_cmd = (self.kp * error) + (self.ki * self.integral_error) + (self.kd * derivative_error)
        
        # Anti-windup
        cmd = max(-1.0, min(1.0, raw_cmd))
        if (raw_cmd > 1.0 and error > 0) or (raw_cmd < -1.0 and error < 0):
            self.integral_error -= error * dt # Revert integration if saturated and pushing further
            
        self.prev_error = error
        self.last_time = current_time
        
        if HAS_ROS:
            out_msg = Float32()
            out_msg.data = cmd
            self.actuator_pub.publish(out_msg)
        else:
            self.log_info(f"Height: {current_height:.3f}m | Target: {self.target_height:.3f}m | Error: {error:.3f}m | Hydraulic Cmd: {cmd:.3f}")

def main():
    if HAS_ROS:
        rclpy.init()
        node = HeaderHeightControlNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        node = HeaderHeightControlNode()
        # Simulate varying ground distance (e.g. going over a bump)
        distances = [0.15, 0.14, 0.10, 0.05, 0.08, 0.12, 0.15]
        for d in distances:
            node.ground_dist_cb(d)
            time.sleep(0.1)

if __name__ == '__main__':
    main()

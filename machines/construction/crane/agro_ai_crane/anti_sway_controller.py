import time
import math
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Imu
    from std_msgs.msg import Float32MultiArray
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class CraneAntiSwayNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('anti_sway_controller')
            self.imu_sub = self.create_subscription(Imu, '/sensor/payload_imu', self.imu_cb, 10)
            self.target_sub = self.create_subscription(Float32MultiArray, '/planning/target_xy', self.target_cb, 10)
            self.motor_pub = self.create_publisher(Float32MultiArray, '/actuator/trolley_cmds', 10)
        
        self.payload_accel = [0.0, 0.0, 9.81]
        self.target_xy = [0.0, 0.0]
        self.current_trolley_xy = [0.0, 0.0]
        
        # We would load an RL policy trained in Isaac Sim here
        if HAS_TORCH:
            self.log_info("Mock-loading RL Anti-Sway policy (Isaac Sim exported ONNX).")
        
        self.timer = self.create_timer(0.02, self.control_loop) if HAS_ROS else None
        
        self.log_info("Crane Anti-Sway Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def imu_cb(self, msg):
        if HAS_ROS:
            self.payload_accel = [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z]
        else:
            self.payload_accel = msg

    def target_cb(self, msg):
        if HAS_ROS:
            self.target_xy = list(msg.data)
        else:
            self.target_xy = msg

    def control_loop(self):
        # Calculate sway angle from IMU
        ax, ay, az = self.payload_accel
        sway_theta_x = math.atan2(ax, az) # Simplified
        sway_theta_y = math.atan2(ay, az)
        
        # Simplified PD control to counteract sway + move to target
        err_x = self.target_xy[0] - self.current_trolley_xy[0]
        err_y = self.target_xy[1] - self.current_trolley_xy[1]
        
        # P for position, D for sway counter-action
        cmd_vx = 0.5 * err_x - 1.5 * sway_theta_x
        cmd_vy = 0.5 * err_y - 1.5 * sway_theta_y
        
        # Saturation
        cmd_vx = max(-1.0, min(1.0, cmd_vx))
        cmd_vy = max(-1.0, min(1.0, cmd_vy))
        
        if HAS_ROS:
            out_msg = Float32MultiArray()
            out_msg.data = [cmd_vx, cmd_vy]
            self.motor_pub.publish(out_msg)
        else:
            self.log_info(f"Target: {self.target_xy} | Sway (deg): ({math.degrees(sway_theta_x):.1f}, {math.degrees(sway_theta_y):.1f}) | Trolley Cmd: ({cmd_vx:.2f}, {cmd_vy:.2f})")
            # Mock update
            self.current_trolley_xy[0] += cmd_vx * 0.02
            self.current_trolley_xy[1] += cmd_vy * 0.02

def main():
    if HAS_ROS:
        rclpy.init()
        node = CraneAntiSwayNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        node = CraneAntiSwayNode()
        node.target_cb([5.0, 5.0])
        # Simulate sway
        for i in range(10):
            sway_force = 2.0 * math.sin(i)
            node.imu_cb([sway_force, 0.0, 9.81])
            node.control_loop()

if __name__ == '__main__':
    main()

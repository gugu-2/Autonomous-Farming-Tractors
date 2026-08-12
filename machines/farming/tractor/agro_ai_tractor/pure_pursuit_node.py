import math
import numpy as np
try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist, PoseStamped
    from nav_msgs.msg import Path
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class PurePursuitNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('pure_pursuit_node')
            self.declare_parameter('lookahead_distance', 3.0)
            self.declare_parameter('wheelbase', 2.8)
            
            self.lookahead = self.get_parameter('lookahead_distance').value
            self.wheelbase = self.get_parameter('wheelbase').value
            
            self.path_sub = self.create_subscription(Path, '/planning/global_path', self.path_cb, 10)
            self.pose_sub = self.create_subscription(PoseStamped, '/ekf/global_pose', self.pose_cb, 10)
            self.cmd_pub = self.create_publisher(Twist, '/control/cmd_vel', 10)
        else:
            self.lookahead = 3.0
            self.wheelbase = 2.8
            
        self.current_path = []
        self.current_pose = None
        
        self.log_info("Tractor Pure Pursuit node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def path_cb(self, msg):
        if HAS_ROS:
            self.current_path = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        else:
            self.current_path = msg # Mock format

    def pose_cb(self, msg):
        if not self.current_path: return
        
        if HAS_ROS:
            x = msg.pose.position.x
            y = msg.pose.position.y
            # Extract yaw from quaternion
            q = msg.pose.orientation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
        else:
            x, y, yaw = msg['x'], msg['y'], msg['yaw']

        # Find target point
        target_pt = self.find_target_point(x, y)
        if not target_pt: return
        
        # Calculate steering angle (alpha)
        tx, ty = target_pt
        Ld = math.hypot(tx - x, ty - y)
        alpha = math.atan2(ty - y, tx - x) - yaw
        
        # Pure pursuit steering angle equation: delta = atan(2L * sin(alpha) / Ld)
        steering_angle = math.atan2(2.0 * self.wheelbase * math.sin(alpha), Ld)
        
        if HAS_ROS:
            cmd = Twist()
            cmd.linear.x = 2.5 # Constant 2.5 m/s (~9 kph)
            cmd.angular.z = steering_angle
            self.cmd_pub.publish(cmd)
        else:
            self.log_info(f"Target: ({tx:.2f}, {ty:.2f}) | Steer Angle: {math.degrees(steering_angle):.1f} deg")

    def find_target_point(self, rx, ry):
        best_pt = None
        min_dist = float('inf')
        for pt in self.current_path:
            d = math.hypot(pt[0] - rx, pt[1] - ry)
            if d >= self.lookahead and d < min_dist: # Find closest point BEYOND lookahead
                best_pt = pt
                min_dist = d
        if not best_pt and self.current_path: # Fallback to last point
            best_pt = self.current_path[-1]
        return best_pt

def main():
    if HAS_ROS:
        rclpy.init()
        node = PurePursuitNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        node = PurePursuitNode()
        node.path_cb([(0,0), (5,0), (10,5), (15,10)])
        node.pose_cb({'x': 8, 'y': 2, 'yaw': math.radians(45)})

if __name__ == '__main__':
    main()

import time
import numpy as np
try:
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import PoseStamped
    from std_msgs.msg import Float32MultiArray, Float32
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class BulldozerMPCNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('grading_mpc_node')
            self.declare_parameter('horizon', 10)
            self.declare_parameter('dt', 0.1)
            
            self.horizon = self.get_parameter('horizon').value
            self.dt = self.get_parameter('dt').value
            
            self.pose_sub = self.create_subscription(PoseStamped, '/ekf/global_pose', self.pose_cb, 10)
            self.target_sub = self.create_subscription(Float32, '/planning/target_grade_height', self.target_cb, 10)
            self.blade_pub = self.create_publisher(Float32MultiArray, '/actuator/blade_cmds', 10)
        else:
            self.horizon = 10
            self.dt = 0.1
            
        self.current_z = 0.0
        self.target_z = 0.0
        self.current_blade_pitch = 0.0
        
        self.timer = self.create_timer(0.1, self.mpc_loop) if HAS_ROS else None
        
        self.log_info("Bulldozer MPC Grading Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def pose_cb(self, msg):
        if HAS_ROS:
            self.current_z = msg.pose.position.z
        else:
            self.current_z = msg

    def target_cb(self, msg):
        if HAS_ROS:
            self.target_z = msg.data
        else:
            self.target_z = msg
            
    def mpc_cost(self, u, *args):
        # Extremely simplified 1D kinematic model for mock purposes
        # State: z_height, blade_pitch. Control: blade_pitch_rate
        z_curr, pitch_curr, z_target = args
        cost = 0
        z = z_curr
        pitch = pitch_curr
        for i in range(self.horizon):
            pitch_rate = u[i]
            pitch += pitch_rate * self.dt
            z += pitch * self.dt # kinematic approximation, assuming unit forward velocity
            cost += 10.0 * (z - z_target)**2 # Tracking cost
            cost += 0.1 * pitch_rate**2 # Control effort penalty
        return cost

    def mpc_loop(self):
        if not HAS_SCIPY:
            self.log_info("Scipy missing. Using simple proportional fallback.")
            # PD control since z is a double integrator of pitch_cmd (pitch_rate)
            pitch_cmd = 0.5 * (self.target_z - self.current_z) - 1.0 * self.current_blade_pitch
        else:
            # Solve MPC
            u0 = np.zeros(self.horizon)
            bounds = [(-1.0, 1.0) for _ in range(self.horizon)]
            args = (self.current_z, self.current_blade_pitch, self.target_z)
            
            res = minimize(self.mpc_cost, u0, args=args, bounds=bounds, method='SLSQP')
            pitch_cmd = res.x[0] if res.success else 0.0
            
        # Send cmds: [lift, tilt, pitch]
        blade_cmds = [0.0, 0.0, pitch_cmd]
            
        if HAS_ROS:
            msg = Float32MultiArray()
            msg.data = blade_cmds
            self.blade_pub.publish(msg)
        else:
            self.log_info(f"Z: {self.current_z:.2f} | Target: {self.target_z:.2f} | Blade Pitch Cmd: {pitch_cmd:.3f}")
            # simulate movement
            self.current_blade_pitch += pitch_cmd * self.dt
            self.current_z += self.current_blade_pitch * self.dt

def main():
    if HAS_ROS:
        rclpy.init()
        node = BulldozerMPCNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        node = BulldozerMPCNode()
        node.target_cb(5.0)
        node.pose_cb(6.5)
        for _ in range(10):
            node.mpc_loop()

if __name__ == '__main__':
    main()

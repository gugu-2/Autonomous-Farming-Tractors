import time
import numpy as np
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Float32MultiArray
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class ExcavatorRLInferenceNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('trenching_rl_inference')
            self.declare_parameter('model_path', 'excavator_ppo.pth')
            self.model_path = self.get_parameter('model_path').value
            
            # Subscriptions: joint states (boom, stick, bucket), target depth
            self.joint_sub = self.create_subscription(JointState, '/joint_states', self.joint_cb, 10)
            self.target_sub = self.create_subscription(Float32MultiArray, '/task/target_trench', self.target_cb, 10)
            
            # Publisher: hydraulic valve commands
            self.valve_pub = self.create_publisher(Float32MultiArray, '/actuator/valve_cmds', 10)
        else:
            self.model_path = 'mock_path'
            
        self.target_trench = [0.0, 0.0, -2.0] # x, y, z relative to base
        self.current_joints = [0.0, 0.0, 0.0] # boom, stick, bucket angles
        
        # Load the PPO policy
        if HAS_TORCH:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            try:
                # Load optimized TorchScript model for edge inference (if available)
                self.policy = torch.jit.load(self.model_path).to(self.device)
                self.policy.eval()
                self.log_info(f"Loaded RL Policy from {self.model_path} on {self.device}.")
            except Exception as e:
                self.log_info(f"Could not load policy from {self.model_path}, using mock. Error: {e}")
                self.policy = None
        else:
            self.log_info("PyTorch not installed. Using simple programmatic policy fallback.")
            self.policy = None
            
        self.timer = self.create_timer(0.05, self.inference_loop) if HAS_ROS else None
        
        self.log_info("Excavator RL Trenching Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def joint_cb(self, msg):
        if HAS_ROS:
            # Assumes order: boom, stick, bucket
            self.current_joints = list(msg.position[:3])
        else:
            self.current_joints = msg

    def target_cb(self, msg):
        if HAS_ROS:
            self.target_trench = list(msg.data)
        else:
            self.target_trench = msg

    def inference_loop(self):
        # Mathematical Validation:
        # Observation space O in R^6: joints theta in R^3, target position P in R^3.
        # Action space A in R^3: valve spool commands u in [-1, 1]^3.
        # The policy network models the optimal mapping \pi(u | \theta, P) maximizing trenching reward.
        obs = np.array(self.current_joints + self.target_trench, dtype=np.float32)
        
        # Inference
        if HAS_TORCH and self.policy is not None:
            # Optimize inference by disabling gradient tracking for edge deployment
            with torch.no_grad():
                obs_tensor = torch.tensor(obs).unsqueeze(0).to(self.device)
                valve_cmds = self.policy(obs_tensor).squeeze(0).cpu().numpy().tolist()
        else:
            # Fallback simple logic: linear mock controller
            valve_cmds = [0.1, -0.2, 0.5]
            
        if HAS_ROS:
            msg = Float32MultiArray()
            msg.data = valve_cmds
            self.valve_pub.publish(msg)
        else:
            self.log_info(f"Obs: {obs.round(2)} -> Valve Cmds (boom, stick, bucket): {valve_cmds}")

def main():
    if HAS_ROS:
        rclpy.init()
        node = ExcavatorRLInferenceNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        node = ExcavatorRLInferenceNode()
        for i in range(3):
            node.joint_cb([0.5 - i*0.1, 1.2 - i*0.2, -0.5 + i*0.1])
            node.inference_loop()
            time.sleep(0.1)

if __name__ == '__main__':
    main()

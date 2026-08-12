try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import NavSatFix, Imu
    from geometry_msgs.msg import PoseStamped
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

import numpy as np

class EKFLocalizationNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('ekf_localization_node')
            self.gps_sub = self.create_subscription(NavSatFix, '/sensor/gps/rtk', self.gps_callback, 10)
            self.imu_sub = self.create_subscription(Imu, '/sensor/imu/data', self.imu_callback, 10)
            self.pose_pub = self.create_publisher(PoseStamped, '/ekf/global_pose', 10)
        self.log_info("EKF Localization Node initialized.")
        
        # State vector: [x, y, z, yaw]
        self.state = np.zeros(4)

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def gps_callback(self, msg):
        # Mock GPS update
        if HAS_ROS:
            self.state[0] = msg.longitude # Simplified projection
            self.state[1] = msg.latitude
            self.publish_pose()
        else:
            self.log_info("Processed GPS update.")

    def imu_callback(self, msg):
        # Mock IMU update
        if HAS_ROS:
            self.state[3] = msg.orientation.z # Simplified quaternion to yaw
            self.publish_pose()
        else:
            self.log_info("Processed IMU update.")
            
    def publish_pose(self):
        if HAS_ROS:
            msg = PoseStamped()
            msg.pose.position.x = float(self.state[0])
            msg.pose.position.y = float(self.state[1])
            msg.pose.position.z = float(self.state[2])
            self.pose_pub.publish(msg)
        else:
            self.log_info(f"Published global pose: {self.state}")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = EKFLocalizationNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = EKFLocalizationNode()
        node.publish_pose()

if __name__ == '__main__':
    main()

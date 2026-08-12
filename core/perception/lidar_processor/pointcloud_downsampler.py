try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import PointCloud2
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

import numpy as np

class LidarProcessorNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('lidar_processor_node')
            self.subscription = self.create_subscription(
                PointCloud2,
                '/sensor/lidar/raw',
                self.listener_callback,
                10)
            self.publisher_ = self.create_publisher(PointCloud2, '/perception/lidar/downsampled', 10)
        self.log_info("LiDAR Processor Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def listener_callback(self, msg):
        # Mock downsampling logic
        if HAS_ROS:
            # Just passing through for mock
            self.publisher_.publish(msg)
        else:
            self.log_info(f"Received raw point cloud, outputting downsampled mock.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = LidarProcessorNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = LidarProcessorNode()
        node.listener_callback(None)

if __name__ == '__main__':
    main()

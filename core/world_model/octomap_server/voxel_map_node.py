try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import PointCloud2
    # We would use octomap_msgs here, but we'll mock it for now
    from std_msgs.msg import String 
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

class VoxelMapNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('voxel_map_node')
            self.pc_sub = self.create_subscription(
                PointCloud2,
                '/perception/lidar/downsampled',
                self.pc_callback,
                10)
            self.map_pub = self.create_publisher(String, '/world_model/octomap', 10)
        self.log_info("Voxel Map Node initialized.")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def pc_callback(self, msg):
        if HAS_ROS:
            # Mocking OctoMap generation
            out_msg = String()
            out_msg.data = "Mock OctoMap Data"
            self.map_pub.publish(out_msg)
        else:
            self.log_info("Processed downsampled point cloud into Voxel Map.")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = VoxelMapNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = VoxelMapNode()
        node.pc_callback(None)

if __name__ == '__main__':
    main()

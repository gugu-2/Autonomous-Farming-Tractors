try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

import numpy as np

class CameraNode(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('camera_node')
            self.publisher_ = self.create_publisher(Image, '/sensor/camera/rgb', 10)
            self.timer = self.create_timer(0.05, self.timer_callback) # 20 Hz
        self.log_info("Camera Node initialized (Intel RealSense mock).")

    def log_info(self, msg):
        if HAS_ROS: self.get_logger().info(msg)
        else: print(f"[INFO] {msg}")

    def timer_callback(self):
        # Mocking an RGB frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        if HAS_ROS:
            msg = Image()
            msg.height = frame.shape[0]
            msg.width = frame.shape[1]
            msg.encoding = 'rgb8'
            msg.data = frame.tobytes()
            self.publisher_.publish(msg)
        else:
            self.log_info("Published mock RGB frame (1920x1080x3).")

def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = CameraNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        node = CameraNode()
        node.timer_callback()

if __name__ == '__main__':
    main()

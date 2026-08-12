import numpy as np
import time

# Attempt to import ROS2 dependencies
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    Image = object
    print("WARNING: rclpy not found. Running in mock mode.")
    class Node:
        def __init__(self, name):
            pass
        def declare_parameter(self, name, default):
            pass
        def get_parameter(self, name):
            class Param:
                def get_parameter_value(self):
                    class Val:
                        string_value = 'yolov8s.pt'
                        double_value = 0.5
                    return Val()
            return Param()
        def get_logger(self):
            class Logger:
                def info(self, msg): print(f"[INFO] {msg}")
                def debug(self, msg): print(f"[DEBUG] {msg}")
            return Logger()
        def create_subscription(self, *args, **kwargs):
            return None
        def create_publisher(self, *args, **kwargs):
            class Pub:
                def publish(self, msg): print(f"[PUBLISH] {msg.data}")
            return Pub()
if HAS_ROS:
    try:
        from ultralytics import YOLO
        HAS_YOLO = True
    except ImportError:
        HAS_YOLO = False
        print("WARNING: ultralytics package not found.")
else:
    HAS_YOLO = False
    print("Running in mock mode, disabling real YOLO initialization.")


class MockDetection:
    """A mock detection structure to simulate weed detection."""
    class Box:
        def __init__(self, x1, y1, x2, y2, cls, conf):
            self.xyxy = [[x1, y1, x2, y2]]
            self.cls = [cls]
            self.conf = [conf]
            self.xywh = [[(x1+x2)/2, (y1+y2)/2, x2-x1, y2-y1]]
            
    def __init__(self, boxes):
        self.boxes = boxes


class MockYOLO:
    def __init__(self, *args, **kwargs):
        self.device = "mock"
        
    def __call__(self, img, *args, **kwargs):
        # Simulate inference delay
        time.sleep(0.015) 
        # Return a mock detection of a weed (class 1) in the center of the image
        box = MockDetection.Box(300, 300, 340, 340, cls=1.0, conf=0.92)
        return [MockDetection(box)]


class TrtYoloNode(Node):
    def __init__(self):
        super().__init__('trt_yolo_node')
        
        self.declare_parameter('model_path', 'yolov8s.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.conf_thresh = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        
        self.get_logger().info(f'Loading YOLO model from: {model_path}')
        
        if HAS_YOLO:
            # Optimization for edge deployment (TensorRT)
            # Ultralytics auto-handles .engine files. If .pt is provided, it runs via PyTorch.
            # We explicitly set task to 'detect' to ensure proper initialization
            self.model = YOLO(model_path, task='detect')
            self.get_logger().info(f"YOLO model {model_path} loaded successfully.")
        else:
            self.model = MockYOLO(model_path)
        
        # Subscribe to all 12 cameras
        self.subscriptions_list = []
        for i in range(1, 13):
            topic_name = f'/camera_{i:02d}/image_raw'
            sub = self.create_subscription(
                Image,
                topic_name,
                lambda msg, cam_id=i: self.image_callback(msg, cam_id),
                10
            )
            self.subscriptions_list.append(sub)
            
        # We would normally publish vision_msgs/Detection2DArray, but we'll publish custom simple strings for this prototype
        # to avoid needing the vision_msgs package installed for testing
        try:
            from std_msgs.msg import String
        except ImportError:
            class String: pass
        self.detection_pub = self.create_publisher(String, '/vision/weed_detections', 10)
        
        self.get_logger().info('YOLO Detector node initialized and waiting for images.')

    def image_callback(self, msg, cam_id):
        start_time = time.time()
        
        # Convert ROS Image to OpenCV image (mocked conversion)
        # Normally: cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        # Here we'll just create a dummy numpy array of the right size
        if hasattr(msg, 'width'):
            h, w = msg.height, msg.width
        else:
            h, w = 640, 640
            
        dummy_img = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Run inference optimized for edge (half precision)
        # Mathematical Validation: Object detection identifies a bounding box B_i = (x_c, y_c, w, h)
        # and class probability P(C_k | B_i). We filter by P(C_{weed} | B_i) > conf_thresh.
        kwargs = {'verbose': False}
        if HAS_YOLO:
            # FP16 optimization for Edge GPU/TensorRT
            kwargs['half'] = True
            
        results = self.model(dummy_img, **kwargs)
        
        inference_time = (time.time() - start_time) * 1000
        
        # Parse results
        weeds_found = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            try:
                if len(boxes) == 0:
                    continue
            except TypeError:
                pass # Mock object doesn't have len()
                
            # Safely move tensors to CPU numpy for indexing
            try:
                cls_ids = boxes.cls.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                xywhs = boxes.xywh.cpu().numpy()
            except AttributeError:
                # Fallback for mock objects
                cls_ids = boxes.cls
                confs = boxes.conf
                xywhs = boxes.xywh
                
            for i in range(len(cls_ids)):
                cls_id = int(cls_ids[i])
                conf = float(confs[i])
                
                # Class 1 = weed
                if cls_id == 1 and conf > self.conf_thresh:
                    # Get center coordinates: (x_c, y_c) mapped from pixel space
                    cx, cy = float(xywhs[i][0]), float(xywhs[i][1])
                    weeds_found.append({"cam": cam_id, "x": cx, "y": cy, "conf": conf})
                    
        # If weeds found, publish them
        if weeds_found:
            import json
            try:
                from std_msgs.msg import String
            except ImportError:
                class String: pass
            
            pub_msg = String()
            pub_msg.data = json.dumps({
                "timestamp": time.time(),
                "detections": weeds_found,
                "latency_ms": inference_time
            })
            self.detection_pub.publish(pub_msg)
            self.get_logger().debug(f'Published {len(weeds_found)} weeds from cam {cam_id}')

def main(args=None):
    # In a real environment, this starts the ROS2 node
    # If rclpy isn't available, we'll just run a test function
    try:
        import rclpy
        rclpy.init(args=args)
        node = TrtYoloNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    except (NameError, ImportError):
        print("ROS2 not installed. Running a simple test instance...")
        # Mock class for testing without ROS2
        class MockMsg:
            width = 640
            height = 640
        
        node = TrtYoloNode()
        print("Simulating camera frame arrival...")
        node.image_callback(MockMsg(), cam_id=4)
        print("Test complete.")

if __name__ == '__main__':
    main()

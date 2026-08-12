import json
import time
import math

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String, UInt64
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")


class PrecisionSprayLogic(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('precision_spray_logic')
            
            self.declare_parameter('boom_width_meters', 18.0) # 18 meters = ~60 ft
            self.declare_parameter('nozzle_count', 36)
            self.declare_parameter('camera_lookahead_meters', 1.5)
            self.declare_parameter('vehicle_speed_kph', 15.0) # Default if GPS vel is missing
            self.declare_parameter('spray_pulse_duration_ms', 100)
            
            self.boom_width = self.get_parameter('boom_width_meters').get_parameter_value().double_value
            self.num_nozzles = self.get_parameter('nozzle_count').get_parameter_value().integer_value
            self.lookahead = self.get_parameter('camera_lookahead_meters').get_parameter_value().double_value
            self.speed_kph = self.get_parameter('vehicle_speed_kph').get_parameter_value().double_value
            self.pulse_duration = self.get_parameter('spray_pulse_duration_ms').get_parameter_value().integer_value / 1000.0
            
            self.nozzle_spacing = self.boom_width / self.num_nozzles
            
            # Subscriptions
            self.vision_sub = self.create_subscription(String, '/vision/weed_detections', self.vision_callback, 10)
            # Normally we'd also subscribe to GPS velocity, for now we use fixed parameter speed
            
            # Publishers
            self.nozzle_pub = self.create_publisher(UInt64, '/hardware/nozzle_cmd', 10)
            
            # Delay buffer: list of dicts {"fire_time": float, "nozzle_idx": int}
            self.delay_buffer = []
            
            # Current state of nozzles
            self.current_nozzle_state = 0
            
            # Timer to check buffer
            self.timer = self.create_timer(0.01, self.buffer_check_callback) # 100Hz
            
            self.get_logger().info(f'Precision spray logic initialized. Nozzle spacing: {self.nozzle_spacing:.2f}m')
        else:
            self.boom_width = 18.0
            self.num_nozzles = 36
            self.lookahead = 1.5
            self.speed_kph = 15.0
            self.nozzle_spacing = self.boom_width / self.num_nozzles
            self.delay_buffer = []
            self.current_nozzle_state = 0
            self.pulse_duration = 0.1

    def log_info(self, msg):
        if HAS_ROS:
            self.get_logger().info(msg)
        else:
            print(f"[INFO] {msg}")

    def vision_callback(self, msg):
        # Weeds detected in camera frame
        data = json.loads(msg.data)
        detections = data.get("detections", [])
        
        speed_mps = self.speed_kph / 3.6
        time_to_target = self.lookahead / speed_mps
        
        fire_time = time.time() + time_to_target
        
        new_targets = 0
        
        for det in detections:
            cam_id = det.get("cam", 1)
            x_pixels = det.get("x", 320)
            
            # Extremely simplified mapping of camera ID and X-pixel to nozzle ID
            # In a real system, this uses a rigorous camera-to-world extrinsic matrix
            
            # Assume 12 cameras across 36 nozzles -> 3 nozzles per camera
            base_nozzle = (cam_id - 1) * 3
            
            # Map X pixel (0-640) to one of the 3 nozzles (0, 1, or 2)
            if x_pixels < 213:
                nozzle_offset = 0
            elif x_pixels < 426:
                nozzle_offset = 1
            else:
                nozzle_offset = 2
                
            nozzle_idx = base_nozzle + nozzle_offset
            
            # Clamp
            nozzle_idx = max(0, min(35, nozzle_idx))
            
            self.delay_buffer.append({
                "fire_time": fire_time,
                "off_time": fire_time + self.pulse_duration,
                "nozzle_idx": nozzle_idx,
                "active": False
            })
            new_targets += 1
            
        if new_targets > 0:
            self.log_info(f"Buffered {new_targets} targets to fire in {time_to_target:.2f}s")
            
    def buffer_check_callback(self):
        now = time.time()
        new_state = 0
        
        active_buffer = []
        
        for task in self.delay_buffer:
            if now >= task["off_time"]:
                # Task is done
                continue
            elif now >= task["fire_time"] and now < task["off_time"]:
                # Task is active
                task["active"] = True
                new_state |= (1 << task["nozzle_idx"])
                active_buffer.append(task)
            else:
                # Task is in the future
                active_buffer.append(task)
                
        self.delay_buffer = active_buffer
        state_changed = (new_state != self.current_nozzle_state)
        
        if state_changed:
            self.current_nozzle_state = new_state
            if HAS_ROS:
                msg = UInt64()
                msg.data = self.current_nozzle_state
                self.nozzle_pub.publish(msg)
            else:
                self.log_info(f"MOCK PUB -> Nozzle State: {bin(self.current_nozzle_state)}")


def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = PrecisionSprayLogic()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        print("ROS2 not installed. Running a simple test instance...")
        node = PrecisionSprayLogic()
        
        # Simulate incoming vision detection
        import json
        class MockMsg:
            data = json.dumps({
                "detections": [
                    {"cam": 4, "x": 100, "y": 320, "conf": 0.95},
                    {"cam": 10, "x": 500, "y": 320, "conf": 0.88}
                ]
            })
            
        print("Simulating weed detection message...")
        node.vision_callback(MockMsg())
        
        print(f"Delay buffer size: {len(node.delay_buffer)}. Advancing time manually to trigger...")
        start_t = time.time()
        while time.time() - start_t < 1.0:
            node.buffer_check_callback()
            time.sleep(0.01)
            
        print("Test complete.")


if __name__ == '__main__':
    main()

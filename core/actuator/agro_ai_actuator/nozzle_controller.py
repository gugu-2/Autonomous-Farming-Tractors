import time
import struct
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import UInt64
    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    print("WARNING: rclpy not found. Running in mock mode.")

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    print("WARNING: pyserial not found. Serial commands will be mocked.")


class NozzleController(Node if HAS_ROS else object):
    def __init__(self):
        if HAS_ROS:
            super().__init__('nozzle_controller')
            
            self.declare_parameter('serial_port', '/dev/ttyACM0')
            self.declare_parameter('baud_rate', 1000000)
            
            port = self.get_parameter('serial_port').get_parameter_value().string_value
            baud = self.get_parameter('baud_rate').get_parameter_value().integer_value
        else:
            # Mock initialization
            port = 'COM3'
            baud = 1000000
            
        self.log_info(f"Connecting to Arduino on {port} @ {baud} baud...")
        
        self.serial_conn = None
        if HAS_SERIAL:
            try:
                # In real scenario, we connect to the Arduino
                self.serial_conn = serial.Serial(port, baud, timeout=0.1)
                self.log_info(f"Successfully connected to serial port: {port}")
            except Exception as e:
                self.log_warn(f"Failed to connect to serial port {port}: {e}. Running mocked.")
                
        if HAS_ROS:
            # Subscribe to the nozzle_cmd topic which contains a 64-bit integer
            # where the lowest 36 bits represent the state of the 36 nozzles
            self.subscription = self.create_subscription(
                UInt64,
                '/hardware/nozzle_cmd',
                self.nozzle_cmd_callback,
                10
            )
            self.log_info('Nozzle controller node initialized.')

    def log_info(self, msg):
        if HAS_ROS:
            self.get_logger().info(msg)
        else:
            print(f"[INFO] {msg}")
            
    def log_warn(self, msg):
        if HAS_ROS:
            self.get_logger().warn(msg)
        else:
            print(f"[WARN] {msg}")

    def nozzle_cmd_callback(self, msg):
        # We expect msg.data to be a 64-bit unsigned integer
        bitmask = msg.data
        
        # We need to send 5 bytes (40 bits) to the Arduino to cover 36 nozzles
        # byte 0: bits 0-7
        # byte 1: bits 8-15
        # byte 2: bits 16-23
        # byte 3: bits 24-31
        # byte 4: bits 32-35 (and 36-39 padding)
        
        bytes_to_send = bytearray(5)
        bytes_to_send[0] = (bitmask & 0xFF)
        bytes_to_send[1] = ((bitmask >> 8) & 0xFF)
        bytes_to_send[2] = ((bitmask >> 16) & 0xFF)
        bytes_to_send[3] = ((bitmask >> 24) & 0xFF)
        bytes_to_send[4] = ((bitmask >> 32) & 0x0F)
        
        if self.serial_conn:
            try:
                self.serial_conn.write(bytes_to_send)
                # No flush needed for low latency, let OS handle buffer
            except Exception as e:
                self.log_warn(f"Failed to write to serial port: {e}. Connection lost.")
                self.serial_conn.close()
                self.serial_conn = None
        
        # Print a visual representation of the boom for debugging
        boom_vis = ""
        for i in range(36):
            if (bitmask >> i) & 1:
                boom_vis += "X" # Nozzle ON
            else:
                boom_vis += "-" # Nozzle OFF
                
        self.log_info(f"BOOM: [{boom_vis}]")


def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        node = NozzleController()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        print("ROS2 not installed. Running a simple test instance...")
        node = NozzleController()
        
        # Simulate turning on nozzles 5, 6, 7 and 20, 21
        # 0b000000000000001100000000000011100000
        test_mask = (1 << 5) | (1 << 6) | (1 << 7) | (1 << 20) | (1 << 21)
        
        class MockMsg:
            data = test_mask
            
        print(f"Sending test bitmask: {bin(test_mask)}")
        node.nozzle_cmd_callback(MockMsg())
        print("Test complete.")

if __name__ == '__main__':
    main()

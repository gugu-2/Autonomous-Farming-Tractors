import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """
    ROS2 Launch file for bringing up the AGRO-AI Smart Sprayer subsystem.
    This launches the mocked hardware nodes and the AI vision pipeline.
    """
    
    # Declare launch arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov8s.pt',
        description='Path to the YOLOv8 model (TensorRT engine or PyTorch pt)'
    )
    
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyACM0',
        description='Serial port for the Arduino Nozzle Controller'
    )
    
    # Define Nodes
    
    # 1. Hardware Interface Node (Nozzle Controller)
    nozzle_controller_node = Node(
        package='agro_ai_actuator',  # Assuming we package this properly later
        executable='nozzle_controller',
        name='nozzle_controller',
        output='screen',
        parameters=[{
            'serial_port': LaunchConfiguration('serial_port'),
            'baud_rate': 1000000
        }]
    )
    
    # 2. YOLO Vision Node
    yolo_detector_node = Node(
        package='agro_ai_world_model',
        executable='trt_yolo_node',
        name='yolo_detector',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'confidence_threshold': 0.55
        }]
    )
    
    # 3. Precision Spray Logic Node
    precision_logic_node = Node(
        package='agro_ai_sprayer',
        executable='precision_spray_logic',
        name='precision_spray_logic',
        output='screen',
        parameters=[{
            'boom_width_meters': 18.0,
            'nozzle_count': 36,
            'camera_lookahead_meters': 1.5,
            'vehicle_speed_kph': 15.0,
            'spray_pulse_duration_ms': 100
        }]
    )
    
    # 4. Mock Camera Drivers
    # In a real setup, we would launch 12 v4l2_camera nodes here.
    # We will log that they are starting.
    camera_launch_log = LogInfo(
        msg="Simulating 12 Camera Drivers (v4l2_camera) startup..."
    )
    
    return LaunchDescription([
        model_path_arg,
        serial_port_arg,
        camera_launch_log,
        nozzle_controller_node,
        precision_logic_node,
        yolo_detector_node
    ])

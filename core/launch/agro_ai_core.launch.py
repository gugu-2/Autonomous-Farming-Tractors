import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='agro_ai_world_model',
            executable='trt_yolo_node',
            name='trt_yolo_node'
        ),
        Node(
            package='agro_ai_world_model',
            executable='voxel_map_node',
            name='voxel_map_node'
        ),
        Node(
            package='camera_pipeline_ros2',
            executable='camera_node',
            name='camera_node'
        ),
        Node(
            package='lidar_processor',
            executable='pointcloud_downsampler',
            name='pointcloud_downsampler'
        ),
        Node(
            package='ekf_localization',
            executable='ekf_node',
            name='ekf_node'
        ),
        Node(
            package='hardware_interrupt_handler',
            executable='estop_node',
            name='estop_node'
        ),
        Node(
            package='human_detector_watchdog',
            executable='watchdog_node',
            name='watchdog_node'
        ),
        Node(
            package='agro_ai_telemetry',
            executable='mqtt_bridge_node',
            name='mqtt_bridge_node'
        ),
        Node(
            package='agro_ai_actuator',
            executable='nozzle_controller',
            name='nozzle_controller'
        ),
        Node(
            package='pwm_valve_driver',
            executable='pwm_node',
            name='pwm_node'
        ),
        Node(
            package='can_bus_transceiver',
            executable='can_node',
            name='can_node'
        )
    ])

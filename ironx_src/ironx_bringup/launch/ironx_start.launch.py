import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_cam = LaunchConfiguration('use_cam', default=False)

    robot_localization_file_path = os.path.join(get_package_share_directory('ironx_bringup'), 'config', 'ekf.yaml') 
    robot_state_publisher_file_dir = os.path.join(get_package_share_directory('ironx_gazebo'))
    bringup_launch_file_dir = os.path.join(get_package_share_directory('ironx_bringup'))

    return LaunchDescription([

        DeclareLaunchArgument(
            name='use_cam',
            default_value='False',
            description='Add use_cam:=true to activate the depth camera.'),
          
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_composition',
            output='screen',
            parameters=[{
            	'use_sim_time': use_sim_time,
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,  # A1 / A2
                'frame_id': 'base_scan',
                'inverted': False,
                'angle_compensate': True,
            }],
        ),

        Node(
            package='ironx_bringup',
            executable='ironx_driver',
            name='ironx_driver',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('/imu', '/imu/data'),
                ('/odom', '/wheel/odometry'),]
        ),
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[robot_localization_file_path, 
            {'use_sim_time': use_sim_time}],
            remappings=[("/odometry/filtered", "/odom")],
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([bringup_launch_file_dir, '/ironx_rscamera.launch.py']),
            launch_arguments={'use_sim_time': use_sim_time,}.items(), condition=IfCondition(use_cam)
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([robot_state_publisher_file_dir, '/robot_state_publisher.launch.py']),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

    ])


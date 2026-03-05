import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')
    use_omni = LaunchConfiguration('use_omni', default=False)

    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(get_package_share_directory('ironx_navigation'), 'map.yaml'))

#======================== find map from terminal's input to decode ==========================
    n = len(sys.argv)
    if n >= 1:
        for i in range(n):
            map_arg = sys.argv[i]
            map_path = map_arg.split('=')
            if map_path[0] == "map:":
                if map_path[1] != "" and "~" in map_path[1] and "$HOME" not in map_path:
                    check_home = map_path[1].split('~')
                    map_dir = os.path.expanduser('~') + check_home[1]
                else:
                    map_dir = map_path[1]
#============================================================================================

    nav2_launch_file_dir = os.path.join(
        get_package_share_directory('nav2_bringup'), 'launch')

    diff_params_file = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('ironx_navigation'), 'config', 'teb_params_sim.yaml')) #navigation_sim.yaml

    omni_params_file = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('ironx_navigation'), 'config', 'teb_omni_params_sim.yaml')) #navigation_omni_sim.yaml

    rviz_config_dir = os.path.join(
        get_package_share_directory('ironx_navigation'),
        'rviz',
        'ironx_navigation.rviz')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='True',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            name='use_omni',
            default_value='False',
            description='Default is differential system fill use_omni:=True to active omnidirectional system.'),
            
        DeclareLaunchArgument(
            name='map',
            default_value=map_dir,
            description='Navigation map path'),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_launch_file_dir, '/bringup_launch.py']),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': omni_params_file
            }.items(), condition=IfCondition(use_omni)
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_launch_file_dir, '/bringup_launch.py']),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': diff_params_file
            }.items(), condition=UnlessCondition(use_omni)
        ),
                
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])

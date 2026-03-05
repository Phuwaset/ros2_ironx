#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    urdf_path = 'ironx_3d_camera.urdf'
    urdf = os.path.join(
        get_package_share_directory('ironx_bringup'),
        'urdf',
        urdf_path)

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        Node(
            package='ironx_bringup',
            executable='ironx_imu',
            name='ironx_imu',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('/imu', '/imu/data_raw')]),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=[urdf]),

        Node(
            package='imu_complementary_filter',
            executable='complementary_filter_node',
            name='imu_filter_node_for_orientation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],),

        Node(
            package='ironx_bringup',
            executable='tf_broadcaster_imu',
            name='ironx_imu',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],),
        
    ])

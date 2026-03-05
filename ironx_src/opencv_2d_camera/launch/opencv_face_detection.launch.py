from launch import LaunchDescription
from launch_ros.actions import Node
import os

package_name = 'opencv_2d_camera'
rviz_config_path = os.path.join('src', package_name,'rviz') + "/opencv_face_detection.rviz"

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="opencv_2d_camera",
            executable="opencv_face_detection",
            output="screen"
        ),
        Node(
            package="opencv_2d_camera",
            executable="opencv_result_to_cmd_vel",
            output="screen"
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config_path]
        ),
        
    ])
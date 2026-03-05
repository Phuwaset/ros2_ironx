import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    rs_launch_file_dir = os.path.join(
        get_package_share_directory('realsense2_camera'), 'launch')

    return LaunchDescription([

      IncludeLaunchDescription(
          PythonLaunchDescriptionSource([rs_launch_file_dir, '/rs_launch.py']),
          launch_arguments={'publish_odom_tf': 'False',
          'depth_module.profile': '424x240x6',
          'rgb_camera.profile': '424x240x6',
          }.items(),
      ),
    ])

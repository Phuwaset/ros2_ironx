from setuptools import setup
import os
from glob import glob

package_name = 'opencv_2d_camera'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'opencv_2d_camera'), glob('opencv_2d_camera/*.xml'))
        # Include all config files.   
        #(os.path.join('share', package_name), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ironx',
    maintainer_email='ironx@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
                'opencv_vdo_streaming_publisher = opencv_2d_camera.opencv_vdo_streaming_publisher:main',
                'opencv_vdo_streaming_subscriber = opencv_2d_camera.opencv_vdo_streaming_subscriber:main',
                'opencv_face_detection = opencv_2d_camera.opencv_face_detection:main',
                'opencv_lowerbody_detection = opencv_2d_camera.opencv_lowerbody_detection:main',
                'opencv_aruco = opencv_2d_camera.opencv_aruco:main',
                'opencv_color_detection = opencv_2d_camera.opencv_color_detection:main',
                'opencv_result_to_cmd_vel = opencv_2d_camera.opencv_result_to_cmd_vel:main',
        ],
    },
)

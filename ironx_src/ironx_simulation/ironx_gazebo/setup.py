import os
from glob import glob
from setuptools import setup

package_name = 'ironx_gazebo'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share/' + package_name + '/models/ironx_3d_camera/meshes'), glob('models/ironx_3d_camera/meshes/*.dae')),
        (os.path.join('share/' + package_name + '/models/ironx_world/meshes'), glob('models/ironx_world/meshes/*.dae')),
        (os.path.join('share/' + package_name + '/worlds/empty_worlds'), glob('worlds/empty_worlds/*.model')),
        (os.path.join('share/' + package_name + '/worlds/ironx_worlds'), glob('worlds/ironx_worlds/*.model')),

        
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='agv',
    maintainer_email='agv@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)

import os
from glob import glob
from setuptools import setup
from setuptools import find_packages

package_name = 'ironx_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name+ '/config'), glob('config/*')),
        (os.path.join('share/' + package_name + '/urdf'), glob('urdf/*.urdf')),
        (os.path.join('share/' + package_name + '/meshes/stl'), glob('meshes/stl/*.stl')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi',
    maintainer_email='pi@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ironx_driver = ironx_bringup.ironx_driver:main',
            'ironx_imu = ironx_bringup.ironx_imu:main',
		    'tf_broadcaster_imu = ironx_bringup.tf_broadcaster_imu:main',
        ],
    },
)

#!/usr/bin/python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading

import time
import math
import numpy as np
import serial
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped, PoseWithCovarianceStamped
from sensor_msgs.msg import Temperature, Imu, Joy
import tf_transformations
from tf2_ros import TransformBroadcaster

comport = serial.Serial("/dev/ttyACM0",115200,timeout=1)
comport.close()
comport.open()

# waiting for controller ready
string_rev = ""
#comport.write("Home\n\r".encode()) # for sync with controller board

def callback_cmd_vel(msg):
    x_speed = msg.linear.x
    y_speed = msg.linear.y
    Rotate_angle = msg.angular.z

    ########## Speed limit ##########
    if x_speed > 0.5:
        x_speed = 0.5
    elif x_speed < -0.5:
        x_speed = -0.5

    if y_speed > 0.5:
        y_speed = 0.5
    elif y_speed < -0.5:
        y_speed = -0.5
    ################################
        
    string_ROS_STM32 = "CD" + "," + str(x_speed) + "," + str(y_speed) + "," + str(Rotate_angle) + ",\r\n"
    comport.write(string_ROS_STM32.encode())
    print(string_ROS_STM32)

def main(args=None):
    rclpy.init(args=args)

    node = rclpy.create_node('ironx_driver')
    # Publisher object
    imu_publisherObject = node.create_publisher(Imu, 'imu' , 10)
    odom_publisherObject = node.create_publisher( Odometry, 'odom' , 10)
    voltage_publisherObject = node.create_publisher(String , 'ironx_voltage' , 10)

    #Start Subscribe
    subscription = node.create_subscription(Twist, '/cmd_vel', callback_cmd_vel,10)

    # Topic data
    imu = Imu()
    imu.header.frame_id = "imu_link" #"base_imu_link"
    
    odom = Odometry()
    odom.header.frame_id = "odom"
    odom.child_frame_id = "base_footprint"

    initial_pose = PoseWithCovarianceStamped()
    initial_pose.header.frame_id = "map"

    data_voltage = String()

    odom_pose_x = 0
    odom_pose_y = 0
    odom_yaw = 0
    z = 0
    w = 0
    last_time_odom = 0.0
    diff_x_pose = 0
    diff_y_pose = 0
    diff_yaw_pose = 0

    imu_roll = 0
    imu_pitch = 0 
    imu_yaw = 0

    last_time_IMU = 0.0

    now_odom = time.time()
    vel_dt = now_odom - last_time_odom # sec unit
    last_time_odom = now_odom

    now_IMU = time.time()
    imu_dt = now_IMU - last_time_IMU # sec unit
    last_time_IMU = now_IMU

    while rclpy.ok:
        try:
            rclpy.spin_once(node, executor=None, timeout_sec=0.01)
            STM32_string_data = 0
            string_rev = ""
            while len(string_rev) < 13:
                string_rev = comport.read_until('\n'.encode()).decode('utf-8')
                rclpy.spin_once(node, executor=None, timeout_sec=0.01)

            STM32_string_data = string_rev.split(',')
            
            if STM32_string_data[0] == "RD" and "RD" not in STM32_string_data[1] and "RD" not in STM32_string_data[2] and "RD" not in STM32_string_data[3] and "RD" not in STM32_string_data[4] and "RD" not in STM32_string_data[5] and "RD" not in STM32_string_data[6] and "RD" not in STM32_string_data[7] and "RD" not in STM32_string_data[8] and "RD" not in STM32_string_data[9] and "RD" not in STM32_string_data[10]:
                accel_x = float(STM32_string_data[1])
                accel_y = float(STM32_string_data[2])
                accel_z = float(STM32_string_data[3])
                
                gyro_x = float(STM32_string_data[4]) # unit deg/s
                gyro_y = float(STM32_string_data[5]) # unit deg/s
                gyro_z = float(STM32_string_data[6]) # unit deg/s
                
                vel_linear_x = float(STM32_string_data[7]) # unit meters/s 
                vel_linear_y = float(STM32_string_data[8]) # unit meters/s 
                diff_vel_yaw = float(STM32_string_data[9]) # unit rad/s  
                voltage = float(STM32_string_data[10]) #  unit v


                ###################### Voltage part ##################
                vol_Raw = str(voltage)
                vol_percent = ((110*voltage)/3)-365.6667
                if vol_percent > 100:
                    vol_percent = 100
                elif vol_percent < 0:
                    vol_percent = 0
                vol_percent = "{:.1f}".format(vol_percent)
                data_voltage.data  = vol_Raw + "," + vol_percent + "%"
                voltage_publisherObject.publish(data_voltage)
                
                
                ###################### odom_raw(Pose) Part #####################
                now_odom = time.time()
                vel_dt = now_odom - last_time_odom # sec unit
                diff_yaw_pose = diff_vel_yaw * vel_dt # rad unit
                diff_x_pose = (vel_linear_x * math.cos(odom_yaw) - vel_linear_y * math.sin(odom_yaw))*vel_dt
                diff_y_pose = (vel_linear_x * math.sin(odom_yaw) + vel_linear_y * math.cos(odom_yaw))*vel_dt
                
            
                odom_pose_x = odom_pose_x + diff_x_pose
                odom_pose_y = odom_pose_y + diff_y_pose
                odom_yaw = odom_yaw + diff_yaw_pose
                
                last_time_odom = now_odom
                
                z = math.sin(odom_yaw/2)
                w = math.cos(odom_yaw/2)

                odom.pose.pose.position.x = odom_pose_x
                odom.pose.pose.position.y = odom_pose_y
                odom.pose.pose.position.z = 0.0
                odom.pose.pose.orientation.x = 0.0
                odom.pose.pose.orientation.y = 0.0
                odom.pose.pose.orientation.z = z
                odom.pose.pose.orientation.w = w
                odom.pose.covariance = [1e-9, 0.0, 0.0, 0.0, 0.0, 0.0, 
                                        0.0, 1e-3, 1e-9, 0.0, 0.0, 0.0, 
                                        0.0, 0.0, 1e6, 0.0, 0.0, 0.0,
                                        0.0, 0.0, 0.0, 1e6, 0.0, 0.0, 
                                        0.0, 0.0, 0.0, 0.0, 1e6, 0.0, 
                                        0.0, 0.0, 0.0, 0.0, 0.0, 1e3 ]
                
                
                odom.twist.twist.linear.x = vel_linear_x
                odom.twist.twist.linear.y = vel_linear_y
                odom.twist.twist.linear.z = 0.0
                odom.twist.twist.angular.x = 0.0
                odom.twist.twist.angular.y = 0.0
                odom.twist.twist.angular.z = diff_vel_yaw
                
                odom.twist.covariance = [1e-9, 0.0, 0.0, 0.0, 0.0, 0.0, 
                                        0.0, 1e-3, 1e-9, 0.0, 0.0, 0.0, 
                                        0.0, 0.0, 1e6, 0.0, 0.0, 0.0,
                                        0.0, 0.0, 0.0, 1e6, 0.0, 0.0, 
                                        0.0, 0.0, 0.0, 0.0, 1e6, 0.0, 
                                        0.0, 0.0, 0.0, 0.0, 0.0, 0.1]
                odom.header.stamp = node.get_clock().now().to_msg()
                odom_publisherObject.publish(odom)
                
                ###################### IMU Part #####################
                now_IMU = time.time()
                imu_dt = now_IMU - last_time_IMU # sec unit
                
                diff_imu_roll = gyro_x * imu_dt * (math.pi/180) # rad unit
                imu_roll = imu_roll + diff_imu_roll # rad unit

                diff_imu_pitch = gyro_y * imu_dt * (math.pi/180) # rad unit
                imu_pitch = imu_pitch + diff_imu_pitch # rad unit

                diff_imu_yaw = gyro_z * imu_dt * (math.pi/180) # rad unit
                imu_yaw = imu_yaw + diff_imu_yaw # rad unit

                last_time_IMU = now_IMU
                
                imu.linear_acceleration.x = accel_x*9.81
                imu.linear_acceleration.y = accel_y*9.81
                imu.linear_acceleration.z = accel_z*9.81
                imu.linear_acceleration_covariance = [ 1e-2, 0.0, 0.0,
                                                        0.0, 0.0, 0.0,
                                                        0.0, 0.0, 0.0]

                imu.angular_velocity.x = gyro_x*(math.pi/180)
                imu.angular_velocity.y = gyro_y*(math.pi/180)
                imu.angular_velocity.z = gyro_z*(math.pi/180)            
                imu.angular_velocity_covariance = [ 1e6, 0.0, 0.0,
                                                    0.0, 1e6, 0.0,
                                                    0.0, 0.0, 1e6]

                imu_orientation = tf_transformations.quaternion_from_euler(imu_roll, imu_pitch, imu_yaw)
                imu.orientation.x = imu_orientation[0]
                imu.orientation.y = imu_orientation[1]
                imu.orientation.z = imu_orientation[2]
                imu.orientation.w = imu_orientation[3]
                imu.orientation_covariance = [  1e6, 0.0, 0.0,
                                                0.0, 1e6, 0.0,
                                                0.0, 0.0, 0.05]
       
                
                imu.header.stamp = node.get_clock().now().to_msg()
                imu_publisherObject.publish(imu)

                # print("orientation.w", imu.orientation.w)
                # print("orientation.z", imu.orientation.z)  
                # print("x ", imu.orientation.x)  
                # print("y ", imu.orientation.y)     
                # print("z ", imu.orientation.z) 
                # print("w ", imu.orientation.w)      
                
        except KeyboardInterrupt:
            comport.close()
            print("comport close and End program")
            exit()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()


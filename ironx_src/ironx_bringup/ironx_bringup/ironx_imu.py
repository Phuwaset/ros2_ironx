#!/usr/bin/python3
import rclpy
import time
import math
import serial
from sensor_msgs.msg import Imu, Joy
import tf_transformations

imu = Imu()

comport = serial.Serial("/dev/ttyACM0",115200,timeout=1)
comport.close()
comport.open()

# waiting for controller ready
string_rev = ""

def main(args=None):
    rclpy.init(args=args)

    node = rclpy.create_node('imu_node')
    # Publisher object
    imu_publisherObject = node.create_publisher(Imu, 'imu' , 10)

    imu_roll = 0
    imu_pitch = 0 
    imu_yaw = 0

    last_time_IMU = 0.0

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


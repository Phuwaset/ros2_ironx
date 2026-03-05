#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class publisher(Node):
    def __init__(self):
        super().__init__('Line_msgs_publisher')
        self.topic = "Line_Notify"
        self.publishers_ = self.create_publisher(String,self.topic,10)
        timer_peroid = 10.0 #seconds
        self.timer = self.create_timer(timer_peroid,self.timer_callback)
    
    def timer_callback(self):
        msg = String()
        msg.data = "เราส่งข้อมูลชุดนี้ ผ่านROS เพื่อส่งต่อไปยัง Line Notify"
        self.publishers_.publish(msg)    

def main(args=None):
    rclpy.init(args=args)

    pub = publisher()
    rclpy.spin(pub)

    pub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
    
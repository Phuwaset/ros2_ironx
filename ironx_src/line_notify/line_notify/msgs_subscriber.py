#!/usr/bin/python3
import requests
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

url = "https://notify-api.line.me/api/notify"
token = "Your Line Notify token​​" # FNAw1Z0jedQZBzSm5pthgx6j8NeL1qXIBGTCxJDavjp 
headers = {'Authorization':'Bearer ' + token}
line_msg = {
    "message":""
    }

class subscriber(Node):
    def __init__(self):
        super().__init__('Line_msgs_subscriber')
        self.topic = "Line_Notify"
        self.subscription = self.create_subscription(String,self.topic,self.listener_callback,10)
        self.subscription
        
        
    def listener_callback(self,msg):
        global ros_msg
        self.get_logger().info('I heard: "%s"' %msg.data)
        ros_msg = msg.data
        line_msg = {
            "message": ros_msg
        }
        res = requests.post(url, headers=headers , data = line_msg)


def main(args=None):
    
    rclpy.init(args=args)
    
    sub = subscriber()
    rclpy.spin(sub)

    sub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
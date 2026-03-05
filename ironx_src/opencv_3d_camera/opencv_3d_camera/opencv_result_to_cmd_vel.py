# Import the necessary libraries
import rclpy # Python library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from std_msgs.msg import String # String is the message type
from geometry_msgs.msg import Twist
 
class msg_Result_Subscriber(Node):

  def __init__(self):
    """
    Class constructor to set up the node
    """
    # Initiate the Node class's constructor and give it a name
    super().__init__('image_result_to_cmd_vel')
      
    self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
    self.subscription = self.create_subscription(String, 'ironx/pub_msgs/result', self.listener_callback,50)

    
  def listener_callback(self, data):
    """
    Callback function.
    """
    vel_msg = Twist()
    result = data.data.split(",")
    direction = result[0]
    speed = float(result[1])/5000 # must fine tune

    print("===================")
    print(result)
    print(speed)
    print("\n\n")
    

    if direction == "forward":
      vel_msg.linear.x = 1.0 * speed * 5.0
      vel_msg.linear.y = 0.0
      vel_msg.linear.z = 0.0
      vel_msg.angular.x = 0.0
      vel_msg.angular.y = 0.0
      vel_msg.angular.z = 0.0
    elif direction == "backward":
      vel_msg.linear.x = -1.0 * speed * 5.0
      vel_msg.linear.y = 0.0
      vel_msg.linear.z = 0.0
      vel_msg.angular.x = 0.0
      vel_msg.angular.y = 0.0
      vel_msg.angular.z = 0.0
    elif direction == "left":
      vel_msg.linear.x = 0.0
      vel_msg.linear.y = 1.0 * speed
      vel_msg.linear.z = 0.0
      vel_msg.angular.x = 0.0
      vel_msg.angular.y = 0.0
      vel_msg.angular.z = 0.0
    elif direction == "right":
      vel_msg.linear.x = 0.0
      vel_msg.linear.y = 1.0 * speed
      vel_msg.linear.z = 0.0
      vel_msg.angular.x = 0.0
      vel_msg.angular.y = 0.0
      vel_msg.angular.z = 0.0
    elif direction == "stop":
      vel_msg.linear.x = 0.0
      vel_msg.linear.y = 0.0
      vel_msg.linear.z = 0.0
      vel_msg.angular.x = 0.0
      vel_msg.angular.y = 0.0
      vel_msg.angular.z = 0.0

    self.cmd_vel_publisher.publish(vel_msg)

    # Display the message on the console
    self.get_logger().info('Receiving Result data')

def main(args=None):
  # Initialize the rclpy library
  rclpy.init(args=args)

  # Create the node
  Result_Subscriber = msg_Result_Subscriber()

  # Spin the node so the callback function is called.
  rclpy.spin(Result_Subscriber)

  # Destroy the node explicitly
  # (optional - otherwise it will be done automatically
  # when the garbage collector destroys the node object)
  Result_Subscriber.destroy_node()

  # Shutdown the ROS client library for Python
  rclpy.shutdown()

if __name__ == '__main__':
    main()
# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
import ament_index_python # Python API for access the ament resource index.
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String# String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 # OpenCV library
import pyrealsense2.pyrealsense2 as rs  # Intel RealSense cross-platform open-source API
import numpy as np
import os
 
class ImagePublisher(Node):
    """
    Create an ImagePublisher class, which is a subclass of the Node class.
    """
    def __init__(self):
        """
        Class constructor to set up the node
        """
        # Initiate the Node class's constructor and give it a name
        super().__init__('ironx_camera')

        # Create the publisher. This publisher will publish an Image
        # to the video_frames topic. The queue size is 10 messages.
        self.vdo_publisher = self.create_publisher(Image, 'ironx/pub_3Dcamera_image/color_image', 10)
        self.vdo_face_detection_publisher = self.create_publisher(Image, 'ironx/pub_3Dcamera_image/face_detection', 10)
        self.face_detection_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

        # We will publish a message every 0.02 seconds
        timer_period = 0.02  # seconds

        # Create the timer
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")
            exit(0)

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        if device_product_line == 'L500':
            config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
        else:
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        self.pipeline.start(config)

        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()
        
        package_name = 'opencv_3d_camera'
        
        pkg_path = ament_index_python.get_package_share_directory(package_name)
        print(pkg_path)
        
        self.face_cascade = cv2.CascadeClassifier(os.path.join(pkg_path,package_name) + '/haarcascade_frontalface_default.xml')
        #self.face_cascade = cv2.CascadeClassifier(os.path.join('src', package_name,package_name) + '/haarcascade_frontalface_default.xml')
        #self.face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')

        self.UpperBound_Distance_Condition=400 # too far
        self.LowerBound_Distance_Condition=300 # too close
            

    def timer_callback(self):
        msg = String()
        # Wait for a coherent pair of frames: depth and color
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())


        self.vdo_publisher.publish(self.br.cv2_to_imgmsg(color_image))
        #convert color image to gray scale
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        #use haarcascades model for detecting face
        faces = self.face_cascade.detectMultiScale(gray_image, 1.3, 5)

        #create list for collect point of face detecrted
        point_face=[]
        # Collect point form every face im image
        for (x,y,w,h) in faces:
            # Create rectangle in face dtected
            cv2.rectangle(color_image,(x,y),(x+w,y+h),(255,0,255),3)
            
            center=(int((x + x+w) * 0.5), int((y+ y+h) * 0.5))
            cv2.circle(color_image,center , 10, (255,0,0), -1)

            #add point to list created before
            point_face.append(center)

        # get height and width of image
        height = color_image.shape[0]
        width = color_image.shape[1]
        # find center of image        
        view_point=(int(width/2),int(height/2))
        cv2.circle(color_image,view_point , 10, (255,0,0), -1)
        
        if len(point_face) > 0:
            for point in point_face:
                # Get point from face as x,y
                point_x,point_y=(point)
                distance_face = depth_frame.get_distance(point_x,point_y)
                distance_face=int(distance_face*1000)

                if (point_x != 0) and (point_y != 0) :
                    # Draw line from cenxter of image to center of face
                    cv2.line(color_image, view_point, (point_x,point_y), (0, 255, 0), 3)

                    #dist_x is distance in x-axis from center of image to center of aruco
                    dist_x = (view_point[0]-point_x)

                    # Find movement value of aruco forward or backward
                    distance_face=abs(distance_face)
                    #print(Distance_face)
                    # Set statement for check offset left or right
                    # from 10 pixel of center
                    if dist_x>75:
                        # text are use following format
                        # 'left or Right , distance offset of aruco in pixel unit', Distance of face in pixel^2 unit
                        text='left,'+str(100+dist_x)+','+str(distance_face)
                        cv2.putText(color_image, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                    elif dist_x<(-75):
                        text='right,'+str(dist_x-100)+','+str(distance_face)
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                    # Set statement for check forward and backward
                    elif abs(dist_x)< 75  and distance_face<self.LowerBound_Distance_Condition:
                        # text are use following format
                        # forward or backward , Distance or face
                        text='backward,'+str(50)+','+str(distance_face)
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                    elif abs(dist_x)< 75 and distance_face>self.UpperBound_Distance_Condition:
                        text='forward,'+str(50)+','+str(distance_face)
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    else :
                        text='stop,'+'0'+','+str(distance_face)
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                    msg.data = text
                    self.face_detection_result_publisher.publish(msg)
        else:
            text='stop,'+'0'
            msg.data = text
            self.face_detection_result_publisher.publish(msg)

        cv2.imshow("ROS2 publisher webcam",color_image)
        self.vdo_face_detection_publisher.publish(self.br.cv2_to_imgmsg(color_image))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            #closing all open windows 
            cv2.destroyAllWindows()
            exit() 

        # Display the message on the console
        self.get_logger().info('Publishing video frame')

def main(args=None):
    # Initialize the rclpy library
    rclpy.init(args=args)

    # Create the node
    image_publisher = ImagePublisher()

    # Spin the node so the callback function is called.
    rclpy.spin(image_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    image_publisher.destroy_node()

    # Shutdown the ROS client library for Python
    rclpy.shutdown()

if __name__ == '__main__':
    main()
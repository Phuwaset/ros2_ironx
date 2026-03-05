# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String # String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images

import cv2 # OpenCV library
import cv2.aruco as aruco # sudo pip3 install opencv-contrib-python
import numpy as np
import pyrealsense2.pyrealsense2 as rs  # Intel RealSense cross-platform open-source API
 
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
        self.vdo_aruco_publisher = self.create_publisher(Image, 'ironx/pub_3Dcamera_image/aruco', 10)
        self.aruco_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

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
        
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_1000)
        self.parameters = aruco.DetectorParameters_create()

        self.parameters.minDistanceToBorder = 0
        self.parameters.adaptiveThreshWinSizeMax = 400

        self.marker = aruco.drawMarker(self.aruco_dict, 200, 200)
        self.marker = cv2.cvtColor(self.marker, cv2.COLOR_GRAY2BGR)

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

        corners, ids, _ = aruco.detectMarkers(gray_image, self.aruco_dict, parameters=self.parameters)

        # create list for collect 6 aruco
        aruco_amount = 6
        point_aruco = np.zeros((aruco_amount,2),dtype=int)
        ids_aruco = np.zeros(aruco_amount,dtype=int)
        Distance_aruco = 0
        # Put text of aruco into image
        for (i, b) in enumerate(corners):

            # get coordinate corner of aruco c=(x,y)
            c1 = (b[0][0][0], b[0][0][1])
            c2 = (b[0][1][0], b[0][1][1])
            c3 = (b[0][2][0], b[0][2][1])
            c4 = (b[0][3][0], b[0][3][1])

            # calculate center of each aruco 
            x = int((c1[0] + c2[0] + c3[0] + c4[0]) / 4)
            y = int((c1[1] + c2[1] + c3[1] + c4[1]) / 4)
            
            # draw rectacngle of each detected aruco
            contours = np.array( [ [c1[0],c1[1]], [c2[0],c2[1]], [c3[0],c3[1]], [c4[0],c4[1]] ] )
            cv2.drawContours(color_image, np.int32([contours]), -1, (255, 0, 255), 3)
            cv2.putText(color_image, str(ids[i]), (x, y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

            # Collect coordinate point of 6 aruco
            for m in range(aruco_amount):
                if ids[i] == [m+1]:
                    point_aruco[m]=(x,y)
                    ids_aruco[m]=ids[i]
        
        # get height and width of image
        height = color_image.shape[0]
        width = color_image.shape[1]

        # find center of image        
        view_point=(int(width/2),int(height/2))
        cv2.circle(color_image,view_point , 10, (255,0,0), -1)

        if max(ids_aruco) > 0:
            for index,point in enumerate(point_aruco):
                # Get point from aruco as x,y
                point_x,point_y=(point)

                Distance_aruco = depth_frame.get_distance(point_x,point_y)
                Distance_aruco=int(Distance_aruco*1000)

                # statement check if point are 0 or not
                # If not 0 then put text into image and yeild
                # yeild evert time of loop and collecg by loop in main function
                if (point_x != 0) and (point_y != 0):
                    # Draw line from center of image to center of aruco
                    cv2.line(color_image, view_point, (point_x,point_y), (0, 255, 0), 3)

                    #dist_x is distance in x-axis from center of image to center of aruco
                    dist_x = (view_point[0]-point_x)

                    Distance_aruco=abs(Distance_aruco)

                    # Set statement for check offset left or right
                    # from 10 pixel of center
                    if dist_x>75:

                        # text are use following format
                        # 'ID , left or Right , distance offset of aruco in pixel unit'
                        text='left,'+str(20 + dist_x) +','+str(Distance_aruco)+ ',' + str(ids_aruco[index])
                        cv2.putText(color_image, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                    elif dist_x<(-75):
                        text='right,'+str(dist_x-20)+','+str(Distance_aruco) + ',' + str(ids_aruco[index])
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    # Set statement for check forward and backward
                    elif abs(dist_x)<75 and Distance_aruco < self.LowerBound_Distance_Condition:
                        # text are use following format
                        # 'ID , forward or backward , Distance or aruco
                        text='backward,'+str(50) +','+str(Distance_aruco) + ','+ str(ids_aruco[index])
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    elif abs(dist_x)<40 and Distance_aruco > self.UpperBound_Distance_Condition:
                        text='forward,'+str(50) +','+str(Distance_aruco) + ',' + str(ids_aruco[index])
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    else:
                        text='stop,'+'0'+','+str(Distance_aruco)+',' + str(ids_aruco[index])
                        cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    msg.data = text
                    self.aruco_result_publisher.publish(msg)
        else:
            text='stop,'+'0,0'
            msg.data = text
            self.aruco_result_publisher.publish(msg)

        cv2.imshow("ROS2 publisher webcam",color_image)
        cv2.imshow("Depth Cam", depth_image)
        self.vdo_aruco_publisher.publish(self.br.cv2_to_imgmsg(color_image))
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
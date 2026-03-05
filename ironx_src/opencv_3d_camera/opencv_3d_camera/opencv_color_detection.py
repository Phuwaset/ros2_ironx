# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String# String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images

import pyrealsense2.pyrealsense2 as rs  # Intel RealSense cross-platform open-source API
import cv2 # OpenCV library
import numpy as np
 
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
        self.vdo_color_detection_publisher = self.create_publisher(Image, 'ironx/pub_3Dcamera_image/color_detection', 10)
        self.color_detection_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

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

        self.UpperBound_Distance_Condition = 400 # too far
        self.LowerBound_Distance_Condition = 300 # too close

        self.windowName = 'ROS2 publisher webcam'
        cv2.namedWindow(self.windowName, cv2.WINDOW_AUTOSIZE)
        cv2.createTrackbar("threshold", self.windowName, 46, 100, self.nothing) 
        cv2.createTrackbar("thresh_HSV", self.windowName, 47, 255, self.nothing) 
        cv2.createTrackbar("h_Fillter", self.windowName, 103, 255, self.nothing) 
        cv2.createTrackbar("s_Fillter", self.windowName, 109, 255, self.nothing) 
        cv2.createTrackbar("v_Fillter", self.windowName, 204, 255, self.nothing) 

    # for trackbar
    def nothing(self,x):  
        pass
            

    def timer_callback(self):
        #Received value from trackbar
        thresh = cv2.getTrackbarPos("threshold", self.windowName)
        thresh_HSV = cv2.getTrackbarPos("thresh_HSV", self.windowName)
        h_Fillter = cv2.getTrackbarPos("h_Fillter", self.windowName)
        s_Fillter = cv2.getTrackbarPos("s_Fillter", self.windowName)
        v_Fillter = cv2.getTrackbarPos("v_Fillter", self.windowName)

        msg = String()
        # Wait for a coherent pair of frames: depth and color
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        pallet=np.zeros_like(color_image)

        self.vdo_publisher.publish(self.br.cv2_to_imgmsg(color_image))
        # Convert image to HSV
        img_hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV) 

        # Create pallet with zeros numpy array for filling color that will be use for detect color
        pallet=cv2.cvtColor(pallet, cv2.COLOR_BGR2HSV)
        pallet[:,:] = [h_Fillter,s_Fillter,v_Fillter]
        Pallet_image=cv2.cvtColor(pallet, cv2.COLOR_HSV2BGR)
    
        # set min and max value of HSV as thresh_HSV
        minHSV = np.array([h_Fillter - thresh_HSV, s_Fillter - thresh_HSV, v_Fillter - thresh_HSV])
        maxHSV = np.array([h_Fillter + thresh_HSV, s_Fillter + thresh_HSV, v_Fillter + thresh_HSV])

        # Merge original image with hsv for get only interest color
        maskColor = cv2.inRange(img_hsv, minHSV, maxHSV)
        img_Color_Detector = cv2.bitwise_and(color_image,color_image,mask = maskColor)

        # convert image after deteced to GRAY for thresholding and contour
        img_gray = cv2.cvtColor(img_Color_Detector, cv2.COLOR_BGR2GRAY)
        ret, thresh_image = cv2.threshold(img_gray,thresh, 255, cv2.THRESH_BINARY)

        # finding contour
        contours = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        # Create list for collect point color and Distances
        point_color=[]
        areas = []
        Distance_color=0
        #statemet for check contoured or not
        if len(contours) > 0:
            
            #Collect contour Distance
            for contour in (contours):
                ar = cv2.contourArea(contour)
                areas.append(ar)

            # checking for max value of contour
            max_area_index = areas.index(max(areas))
            
            # Collect point form contour
            x,y,w,h = cv2.boundingRect(contours[max_area_index])
            #draw rectangle of contour to image
            cv2.rectangle(color_image,(x,y),(x+w,y+h),(255,0,255),3)
            
            center=(int((x + x+w) * 0.5), int((y+ y+h) * 0.5))
            cv2.circle(color_image,center , 10, (255,0,0), -1)
            point_color.append(center)

            # get height and width of image
            height = color_image.shape[0]
            width = color_image.shape[1]
            
            # find center of image    
            view_point=(int(width/2),int(height/2))
            cv2.circle(color_image,view_point , 10, (255,0,0), -1)
            
            if len(point_color) > 0:
                for point in point_color:
                        # Get point from point_color as x,y
                        point_x,point_y=(point)
                        Distance_color = depth_frame.get_distance(point_x,point_y)
                        Distance_color=int(Distance_color*1000)

                        # statement check if point are 0 or not
                        # If not 0 then put text into image and yeild
                        # yeild evert time of loop and collecg by loop in main function
                        if (point_x != 0) and (point_y != 0):
                            # Draw line from center of image to center of deteced color
                            cv2.line(color_image, view_point, (point_x,point_y), (0, 255, 0), 3)

                            #dist_x is distance in x-axis from center of image to center of deteced color
                            dist_x = (view_point[0]-point_x)
                            
                            # Find movement value of aruco forward or backward
                            Distance_color=abs(Distance_color)
                            #print(Distance_color)

                            # Set statement for check offset left or right
                            # from 10 pixel of center
                            if dist_x>75:
                                # text are use following format
                                # 'left or Right , distance offset of aruco in pixel unit'
                                text='left,'+str(150)+ "," + str(Distance_color) 
                                cv2.putText(color_image, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                                
                            elif dist_x<(-75):
                                text='right,'+str(-150)+ "," + str(Distance_color)  
                                cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                            # Set statement for check forward and backward
                            elif abs(dist_x)< 75  and Distance_color < self.LowerBound_Distance_Condition:
                                # text are use following format
                                # forward or backward , Distance or color
                                text='backward,'+str(50)+ "," + str(Distance_color) 
                                cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                            elif abs(dist_x)< 75 and Distance_color > self.UpperBound_Distance_Condition:
                                text='forward,'+str(50)+ "," + str(Distance_color) 
                                cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                            else :
                                text='stop,'+'0'+ "," + str(Distance_color) 
                                cv2.putText(color_image, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                            
                            msg.data = text
                            self.color_detection_result_publisher.publish(msg)
            else:
                text='stop,'+'0'
                msg.data = text
                self.color_detection_result_publisher.publish(msg)

        show = np.hstack((color_image,Pallet_image))
        cv2.imshow(self.windowName, show)

        self.vdo_color_detection_publisher.publish(self.br.cv2_to_imgmsg(color_image))
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
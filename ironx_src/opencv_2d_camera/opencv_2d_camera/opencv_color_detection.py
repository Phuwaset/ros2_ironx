# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String# String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images

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
        self.vdo_publisher = self.create_publisher(Image, 'ironx/pub_camera_image/color_image', 10)
        self.vdo_color_detection_publisher = self.create_publisher(Image, 'ironx/pub_camera_image/color_detection', 10)
        self.color_detection_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

        # We will publish a message every 0.02 seconds
        timer_period = 0.02  # seconds

        # Create the timer
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Create a VideoCapture object
        # The argument '0' gets the default webcam.
        self.cap = cv2.VideoCapture(0)

        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()

        self.UpperBound_Area_Condition = 20000 # too close
        self.LowerBound_Area_Condition = 4000 # too far

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
        ret, frame = self.cap.read()

        if ret == True:
            pallet=np.zeros_like(frame)

            self.vdo_publisher.publish(self.br.cv2_to_imgmsg(frame))
            # Convert image to HSV
            img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 

            # Create pallet with zeros numpy array for filling color that will be use for detect color
            pallet=cv2.cvtColor(pallet, cv2.COLOR_BGR2HSV)
            pallet[:,:] = [h_Fillter,s_Fillter,v_Fillter]
            Pallet_image=cv2.cvtColor(pallet, cv2.COLOR_HSV2BGR)
        
            # set min and max value of HSV as thresh_HSV
            minHSV = np.array([h_Fillter - thresh_HSV, s_Fillter - thresh_HSV, v_Fillter - thresh_HSV])
            maxHSV = np.array([h_Fillter + thresh_HSV, s_Fillter + thresh_HSV, v_Fillter + thresh_HSV])

            # Merge original image with hsv for get only interest color
            maskColor = cv2.inRange(img_hsv, minHSV, maxHSV)
            img_Color_Detector = cv2.bitwise_and(frame,frame,mask = maskColor)

            # convert image after deteced to GRAY for thresholding and contour
            img_gray = cv2.cvtColor(img_Color_Detector, cv2.COLOR_BGR2GRAY)
            ret, thresh_image = cv2.threshold(img_gray,thresh, 255, cv2.THRESH_BINARY)

            # finding contour
            contours = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

            # Create list for collect point color and areas
            point_color=[]
            areas = []
            Area_color=0
            #statemet for check contoured or not
            if len(contours) > 0:
                
                #Collect contour area
                for contour in (contours):
                    ar = cv2.contourArea(contour)
                    areas.append(ar)

                # checking for max value of contour
                max_area_index = areas.index(max(areas))
                
                # Collect point form contour
                x,y,w,h = cv2.boundingRect(contours[max_area_index])
                Area_color = int(h*w)
                #draw rectangle of contour to image
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,255),3)
                
                center=(int((x + x+w) * 0.5), int((y+ y+h) * 0.5))
                cv2.circle(frame,center , 10, (255,0,0), -1)
                point_color.append(center)

                # get height and width of image
                height = frame.shape[0]
                width = frame.shape[1]
                
                # find center of image    
                view_point=(int(width/2),int(height/2))
                cv2.circle(frame,view_point , 10, (255,0,0), -1)
                
                if len(point_color) > 0:
                    for point in point_color:
                            # Get point from point_color as x,y
                            point_x,point_y=(point)

                            # statement check if point are 0 or not
                            # If not 0 then put text into image and yeild
                            # yeild evert time of loop and collecg by loop in main function
                            if (point_x != 0) and (point_x != 0):
                                # Draw line from center of image to center of deteced color
                                cv2.line(frame, view_point, (point_x,point_y), (0, 255, 0), 3)

                                #dist_x is distance in x-axis from center of image to center of deteced color
                                dist_x = (view_point[0]-point_x)
                                
                                # Find movement value of aruco forward or backward
                                Area_color=abs(Area_color)
                                #print(Area_color)

                                # Set statement for check offset left or right
                                # from 10 pixel of center
                                if dist_x>20:
                                    # text are use following format
                                    # 'left or Right , distance offset of aruco in pixel unit'
                                    text='left,'+str(150)+ "," + str(Area_color) 
                                    cv2.putText(frame, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                                    
                                elif dist_x<(-20):
                                    text='right,'+str(-150)+ "," + str(Area_color)  
                                    cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                                # Set statement for check forward and backward
                                elif abs(dist_x)< 20  and Area_color > self.UpperBound_Area_Condition:
                                    # text are use following format
                                    # forward or backward , area or color
                                    text='backward,'+str(50)+ "," + str(Area_color) 
                                    cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                                elif abs(dist_x)< 20 and Area_color < self.LowerBound_Area_Condition:
                                    text='forward,'+str(50)+ "," + str(Area_color) 
                                    cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                                else :
                                    text='stop,'+'0'+ "," + str(Area_color) 
                                    cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                                
                                msg.data = text
                                self.color_detection_result_publisher.publish(msg)
                else:
                    text='stop,'+'0'
                    msg.data = text
                    self.color_detection_result_publisher.publish(msg)

            show = np.hstack((frame,Pallet_image))
            cv2.imshow(self.windowName, show)

            self.vdo_color_detection_publisher.publish(self.br.cv2_to_imgmsg(frame))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                #closing all open windows 
                cv2.destroyAllWindows()
                self.cap.release()
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
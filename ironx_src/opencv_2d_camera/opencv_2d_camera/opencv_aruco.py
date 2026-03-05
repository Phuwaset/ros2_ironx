# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String # String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images

import cv2 # OpenCV library
import cv2.aruco as aruco # sudo pip3 install opencv-contrib-python
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
        self.vdo_aruco_publisher = self.create_publisher(Image, 'ironx/pub_camera_image/aruco', 10)
        self.aruco_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

        # We will publish a message every 0.02 seconds
        timer_period = 0.02  # seconds

        # Create the timer
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Create a VideoCapture object
        # The argument '0' gets the default webcam.
        self.cap = cv2.VideoCapture(0)

        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()
        
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_1000)
        self.parameters = aruco.DetectorParameters_create()

        self.parameters.minDistanceToBorder = 0
        self.parameters.adaptiveThreshWinSizeMax = 400

        self.marker = aruco.drawMarker(self.aruco_dict, 200, 200)
        self.marker = cv2.cvtColor(self.marker, cv2.COLOR_GRAY2BGR)

        self.UpperBound_Area_Condition=30000 # too close
        self.LowerBound_Area_Condition=10000 # too far
            

    def timer_callback(self):
        msg = String()
        ret, frame = self.cap.read()

        if ret == True:
            self.vdo_publisher.publish(self.br.cv2_to_imgmsg(frame))
            #convert color image to gray scale
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            corners, ids, _ = aruco.detectMarkers(gray_image, self.aruco_dict, parameters=self.parameters)

            # create list for collect 6 aruco
            aruco_amount = 6
            point_aruco = np.zeros((aruco_amount,2),dtype=int)
            ids_aruco = np.zeros(aruco_amount,dtype=int)
            Area_aruco = 0
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
                cv2.drawContours(frame, np.int32([contours]), -1, (255, 0, 255), 3)
                cv2.putText(frame, str(ids[i]), (x, y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                # Collect coordinate point of 6 aruco
                for m in range(aruco_amount):
                    if ids[i] == [m+1]:
                        point_aruco[m]=(x,y)
                        ids_aruco[m]=ids[i]

                        #find area of aruco
                        Area_aruco= int(cv2.contourArea(contours))
            
                # get height and width of image
            height = frame.shape[0]
            width = frame.shape[1]

            # find center of image        
            view_point=(int(width/2),int(height/2))
            cv2.circle(frame,view_point , 10, (255,0,0), -1)

            if max(ids_aruco) > 0:
                for index,point in enumerate(point_aruco):
                    # Get point from aruco as x,y
                    point_x,point_y=(point)

                    # statement check if point are 0 or not
                    # If not 0 then put text into image and yeild
                    # yeild evert time of loop and collecg by loop in main function
                    if (point_x != 0) and (point_x != 0):
                        # Draw line from center of image to center of aruco
                        cv2.line(frame, view_point, (point_x,point_y), (0, 255, 0), 3)

                        #dist_x is distance in x-axis from center of image to center of aruco
                        dist_x = (view_point[0]-point_x)
                        
                        # Find movement value of aruco forward or backward
                        Area_aruco=abs(Area_aruco)
                        #print(Area_aruco)

                        # Set statement for check offset left or right
                        # from 10 pixel of center
                        if dist_x>40:

                            # text are use following format
                            # 'ID , left or Right , distance offset of aruco in pixel unit'
                            text='left,'+str(20 + dist_x) +','+str(Area_aruco)+ ',' + str(ids_aruco[index])
                            cv2.putText(frame, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                        elif dist_x<(-40):
                            text='right,'+str(dist_x-20)+','+str(Area_aruco) + ',' + str(ids_aruco[index])
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                        
                        # Set statement for check forward and backward
                        elif abs(dist_x)<40 and Area_aruco > self.UpperBound_Area_Condition:
                            # text are use following format
                            # 'ID , forward or backward , area or aruco
                            text='backward,'+str(50) +','+str(Area_aruco) + ','+ str(ids_aruco[index])
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                        
                        elif abs(dist_x)<40 and Area_aruco < self.LowerBound_Area_Condition:
                            text='forward,'+str(50) +','+str(Area_aruco) + ',' + str(ids_aruco[index])
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                        
                        else:
                            text='stop,'+'0'+','+str(Area_aruco)+',' + str(ids_aruco[index])
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                        
                        msg.data = text
                        self.aruco_result_publisher.publish(msg)
            else:
                text='stop,'+'0,0'
                msg.data = text
                self.aruco_result_publisher.publish(msg)

            cv2.imshow("ROS2 publisher webcam",frame)
            self.vdo_aruco_publisher.publish(self.br.cv2_to_imgmsg(frame))
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
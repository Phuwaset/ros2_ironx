# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of node
import ament_index_python # Python API for access the ament resource index.
from sensor_msgs.msg import Image # Image is the message type
from std_msgs.msg import String# String is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 # OpenCV library
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
        self.vdo_publisher = self.create_publisher(Image, 'ironx/pub_camera_image/color_image', 10)
        self.vdo_face_detection_publisher = self.create_publisher(Image, 'ironx/pub_camera_image/face_detection', 10)
        self.face_detection_result_publisher = self.create_publisher(String, 'ironx/pub_msgs/result', 10)

        # We will publish a message every 0.02 seconds
        timer_period = 0.02  # seconds

        # Create the timer
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Create a VideoCapture object
        # The argument '0' gets the default webcam.
        self.cap = cv2.VideoCapture(0)

        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()
        
        package_name = 'opencv_2d_camera'
        
        pkg_path = ament_index_python.get_package_share_directory(package_name)
        print(pkg_path)
        
        #print("~/" + os.path.join('src', package_name,package_name) + '/haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(os.path.join(pkg_path,package_name) + '/haarcascade_frontalface_default.xml')
        #self.face_cascade = cv2.CascadeClassifier("~/" + os.path.join('src', package_name,package_name) + '/haarcascade_frontalface_default.xml')
        #self.face_cascade = cv2.CascadeClassifier('/home/rengy/ros2_ws/src/opencv_2d_camera/opencv_2d_camera/haarcascade_frontalface_default.xml')
        self.UpperBound_Area_Condition=30000 # too close
        self.LowerBound_Area_Condition=15000 # too far
            

    def timer_callback(self):
        msg = String()
        ret, frame = self.cap.read()

        if ret == True:
            self.vdo_publisher.publish(self.br.cv2_to_imgmsg(frame))
            #convert color image to gray scale
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            #use haarcascades model for detecting face
            faces = self.face_cascade.detectMultiScale(gray_image, 1.3, 5)

            #create list for collect point of face detecrted
            point_face=[]
            Area_face=0
            # Collect point form every face im image
            for (x,y,w,h) in faces:
                # Create rectangle in face dtected
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,255),3)
                
                center=(int((x + x+w) * 0.5), int((y+ y+h) * 0.5))
                cv2.circle(frame,center , 10, (255,0,0), -1)

                #add point to list created before
                point_face.append(center)
                Area_face=int(h*w)

            # get height and width of image
            height = frame.shape[0]
            width = frame.shape[1]
            # find center of image        
            view_point=(int(width/2),int(height/2))
            cv2.circle(frame,view_point , 10, (255,0,0), -1)
            
            if len(point_face) > 0:
                for point in point_face:
                    # Get point from face as x,y
                    point_x,point_y=(point)

                    if (point_x != 0) and (point_x != 0) :
                        # Draw line from cenxter of image to center of face
                        cv2.line(frame, view_point, (point_x,point_y), (0, 255, 0), 3)

                        #dist_x is distance in x-axis from center of image to center of aruco
                        dist_x = (view_point[0]-point_x)

                        # Find movement value of aruco forward or backward
                        Area_face=abs(Area_face)#Area_Condition-Area_face
                        #print(Area_face)
                        # Set statement for check offset left or right
                        # from 10 pixel of center
                        if dist_x>30:
                            # text are use following format
                            # 'left or Right , distance offset of aruco in pixel unit', area of face in pixel^2 unit
                            text='left,'+str(100+dist_x)+','+str(Area_face)
                            cv2.putText(frame, text , (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                        elif dist_x<(-30):
                            text='right,'+str(dist_x-100)+','+str(Area_face)
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                        # Set statement for check forward and backward
                        elif abs(dist_x)< 30  and Area_face>self.UpperBound_Area_Condition:
                            # text are use following format
                            # forward or backward , area or face
                            text='backward,'+str(50)+','+str(Area_face)
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                        elif abs(dist_x)< 30 and Area_face<self.LowerBound_Area_Condition:
                            text='forward,'+str(50)+','+str(Area_face)
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)
                        
                        else :
                            text='stop,'+'0'+','+str(Area_face)
                            cv2.putText(frame, text, (point_x+50,point_y), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 255), 2, cv2.LINE_AA)

                        msg.data = text
                        self.face_detection_result_publisher.publish(msg)
            else:
                text='stop,'+'0'
                msg.data = text
                self.face_detection_result_publisher.publish(msg)

            cv2.imshow("ROS2 publisher webcam",frame)
            self.vdo_face_detection_publisher.publish(self.br.cv2_to_imgmsg(frame))
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
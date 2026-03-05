import numpy as np
import cv2

cap  = cv2.VideoCapture(0)

while True:
    
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    LowerBody_cascade = cv2.CascadeClassifier('haarcascade_lowerbody.xml')
    LowerBody = LowerBody_cascade.detectMultiScale(gray,1.01,1)
    for (x,y,w,h) in LowerBody:
        
        point_lowerbody=[]
        area = w * h
        print(area)
        if area > 35000:
            center=(int((x + x+w) * 0.5), int((y+ y+h) * 0.5))
            #center of interest
            cv2.circle(frame,center , 10, (255,0,0), -1)
            #area of interest
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(frame,"LowerBody",(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
            
            point_lowerbody.append(center)
                    
        if len(point_lowerbody) > 0:
                    for point in point_lowerbody:
                        # Get point from lowerbody as x,y
                        point_x,point_y=(point)
                        # Draw line from cenxter of image to center of lowerbody
                        cv2.line(frame, view_point, (point_x,point_y), (0, 255, 0), 3)  
        #For center point view        
    height = frame.shape[0]
    width = frame.shape[1]            
    view_point=(int(width/2),int(height/2))
    cv2.circle(frame,view_point , 10, (255,0,0), -1)
   
    
    cv2.imshow('LowerBody',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        #closing all open windows 
        cv2.destroyAllWindows()
        cap.release()

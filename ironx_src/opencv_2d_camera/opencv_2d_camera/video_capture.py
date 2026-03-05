import numpy as np
import cv2 # pip3 install opencv-python

cap = cv2.VideoCapture(2)
 
while(True):
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow('Video original',frame)
    cv2.imshow('Video gray',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

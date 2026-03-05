#pip3 install requests​​
import requests
import cv2 # pip3 install opencv-python3
import time

cap = cv2.VideoCapture(0)
ret,frame = cap.read()

dir_img = "./figure.jpg"
cv2.imwrite(dir_img,frame)
time.sleep(1.0)

url = "https://notify-api.line.me/api/notify"
token =  "Your Line Notify token​​" # VYCpo1CIak5QYYJhDP2ubO0naY6p5UMcdiCFB0wtUJ1 
headers = {'Authorization':'Bearer ' + token}

msg = {
            "message":(None,"We can send photo to Line Notify"),
            'imageFile':open(dir_img,"r+b")
            }

res = requests.post(url, headers=headers, files=msg)
print(res.text)

# After the loop release the cap object
cap.release()
# Destroy all the windows
cv2.destroyAllWindows()
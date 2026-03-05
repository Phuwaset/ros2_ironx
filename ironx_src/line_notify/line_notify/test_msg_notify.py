
#pip3 install requests​​
import requests

url = "https://notify-api.line.me/api/notify"
token = "Your Line Notify token​​" # FNAw1Z0jedQZBzSm5pthgx6j8NeL1qXIBGTCxJDavjp 
headers = {'Authorization':'Bearer ' + token}

msg = {
    "message":"We can do Line Notify \n เราสามารถส่ง Line Notify ได้"
    }

res = requests.post(url, headers=headers , data = msg)
print(res.text)
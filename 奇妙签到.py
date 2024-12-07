import requests
import schedule#这里不按教程来会出现红线
import time
YourToken = '你的token'#把"你的token"换成你的token
sign_url = "http://www.magicalapp.cn/user/api/signDays"
headers = {'token': YourToken}
user_id = "你的id"#把"你的id"换成你的id
burst_url = f"https://www.magicalapp.cn/api/game/api/getCoinP?userId={user_id}"
def sign_request():
    sign_response = requests.get(sign_url, headers=headers)
    if sign_response.status_code == 200:
        print('签到成功')
    else:
        print('签到失败')
    burst_response = requests.get(burst_url)
    if burst_response.status_code == 200:
        print('获取金币成功')
    else:
        print('获取金币失败')
schedule.every().day.at("10:00").do(sign_request)
#10:00改成同样格式的其他时间即可自定义定时
while True:
    schedule.run_pending()
    time.sleep(60)
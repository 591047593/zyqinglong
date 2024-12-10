import requests
import schedule
import time

# 将"你的token"替换成你的实际token
YourToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5NDI0ODc4IiwiZXhwIjo0ODg3MTU5NTY4fQ.03DKVmU4hIhzYlsyVsoYBigbtEA2wxwhVaHngXwVbJ4'
# 将"你的id"替换成你的实际用户ID
user_id = "9424878"

# 正确的签到API URL
sign_url = "http://www.magicalapp.cn/user/api/signDays"
# 设置请求头，包含Token用于身份验证
headers = {'token': YourToken}

# 正确的获取金币API URL，并包含用户ID
burst_url = f"https://www.magicalapp.cn/api/game/api/getCoinP?userId={user_id}"

def sign_request():
    # 发送GET请求到签到URL
    sign_response = requests.get(sign_url, headers=headers)
    if sign_response.status_code == 200:
        print('签到成功')
    else:
        print('签到失败')
    
    # 发送GET请求到获取金币的URL
    burst_response = requests.get(burst_url)
    if burst_response.status_code == 200:
        print('获取金币成功')
    else:
        print('获取金币失败')

# 设置定时任务，每天10:00执行sign_request函数
# 你可以根据需要将"10:00"改成其他时间
#schedule.every().day.at("10:00").do(sign_request)

# 开始一个无限循环，以执行定时任务
#while True:
#   schedule.run_pending()
#  time.sleep(60)
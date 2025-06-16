import requests
import json
import time
 
api_keys = [
    "IKSCYvQXQHc5zqLTCTKS7NvD4RmDYxtV"
    # 在这里放置 "<X-API-KEY>"，可放置多项
]
url = "https://api.v2.rainyun.com/user/reward/tasks"
 
print("Rainyun-AutoSignin-V2 script, by CodeZhangBorui\n[Time] ", end='')
print(time.ctime())
 
for key in api_keys:
    print("# 用 X-API-KEY 登录: " + key[:10] + "*"*22)
    headers = {
       'x-api-key': key,
       'User-Agent': 'Rainyun-AutoSignin/2.0 (https://codezhangborui.eu.org/2023/06/rainyun-auto-python-scripts/)'
    }
    response = requests.request("GET", url, headers=headers, data={})
    result = json.loads(response.text)
    print("# 获取可领取任务列表")
    undone = []
    for task in result['data']:
        if(task['Status'] == 0):
            print("## - 未完成：" + task['Name'])
        elif(task['Status'] == 1):
            print("## > 可领取：" + task['Name'] + " | 可获得积分：" + str(task['Points']))
            undone.append(task['Name'])
        elif(task['Status'] == 2):
            print("## V 已领取：" + task['Name'])
        else:
            print("## ? 未知状态：" + task['Name'] + " | 服务器 DATA：" + str(task))
    # undone.append("每日签到")
    if(undone == []):
        print("# 没有可领取任务！")
    else:
        for task in undone:
            try:
                print("## 请求完成任务：" + task, end='')
                response = requests.request("POST", url, headers=headers, json={"task_name": task})
                result = json.loads(response.text)
                print(" | 服务器 DATA：" + str(result))
            except:
                print(":( Something went wrong, retry in 10 seconds...")
                time.sleep(10)
                try:
                    print("## 请求完成任务：" + task, end='')
                    response = requests.request("POST", url, headers=headers, json={"task_name": task})
                    result = json.loads(response.text)
                    print(" | 服务器 DATA：" + str(result))
                except:
                    print(":( Something went wrong, retry in 30 seconds...")
                    time.sleep(30)
                    try:
                        print("## 请求完成任务：" + task, end='')
                        response = requests.request("POST", url, headers=headers, json={"task_name": task})
                        result = json.loads(response.text)
                        print(" | 服务器 DATA：" + str(result))
                    except:
                        print(":( Something went wrong, skip this task")
                        continue
    print("")
print("# 程序已结束！")
time.sleep(10)
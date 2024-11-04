
# #!/usr/bin/python3
# # -- coding: utf-8 --
# # @Time : 2024/9/26 8:23
# #源作者：https://www.52pojie.cn/thread-1231190-1-1.html
# #出处：https://github.com/vistal8/tianyiyun
# # -本人只负责修改并测试可以运行，多账号可能会很慢。耐心等待
# # cron "30 4 * * *" script-path=xxx.py,tag=匹配cron用
# # const $ = new Env('天翼云盘签到');
# # 变量 ty_username 用户名 &隔开  ty_password 密码 &隔开
# # 示例 ty_username 1334567228&133222222   ty_password 123456&123456
# # 出现验证码错误问题，概率账号风控。手动登陆网页版 输入验证码。建议一天运行一次就可以
# #  推送变量为plustoken 
import time
import os
import random
import json
import base64
import hashlib
import rsa
import requests
import re
from urllib.parse import urlparse

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

s = requests.Session()

# 从环境变量获取账号信息
ty_usernames = os.getenv("ty_username").split('&')
ty_passwords = os.getenv("ty_password").split('&')

# 检查是否正确设置了环境变量
if not ty_usernames or not ty_passwords:
    raise ValueError("请设置环境变量 ty_username 和 ty_password")

# 将用户名和密码组合成一个列表
accounts = [{"username": u, "password": p} for u, p in zip(ty_usernames, ty_passwords)]

# 填入pushplus token
plustoken = os.getenv("plustoken")

def int2char(a):
    return BI_RM[a]

def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = B64MAP.index(list(a)[i])
            if 0 == e:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif 1 == e:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif 2 == e:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d

def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result

def calculate_md5_sign(params):
    return hashlib.md5('&'.join(sorted(params.split('&'))).encode('utf-8')).hexdigest()

def login(username, password):
    urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
    s = requests.Session()
    r = s.get(urlToken)
    pattern = r"https?://[^\s'\"]+"  # 匹配以http或https开头的url
    match = re.search(pattern, r.text)  # 在文本中搜索匹配
    if match:  # 如果找到匹配
        url = match.group()  # 获取匹配的字符串
    else:  # 如果没有找到匹配
        print("没有找到url")
        return None

    r = s.get(url)
    pattern = r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\""  # 匹配id为j-tab-login-link的a标签，并捕获href引号内的内容
    match = re.search(pattern, r.text)  # 在文本中搜索匹配
    if match:  # 如果找到匹配
        href = match.group(1)  # 获取捕获的内容
    else:  # 如果没有找到匹配
        print("没有找到href链接")
        return None

    r = s.get(href)
    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
    s.headers.update({"lt": lt})

    username = rsa_encode(j_rsakey, username)
    password = rsa_encode(j_rsakey, password)
    url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
        'Referer': 'https://open.e.189.cn/',
    }
    data = {
        "appKey": "cloud",
        "accountType": '01',
        "userName": f"{{RSA}}{username}",
        "password": f"{{RSA}}{password}",
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
    }
    r = s.post(url, data=data, headers=headers, timeout=5)
    if r.json().get('result', None) == 0:
        print(r.json()['msg'])
    else:
        print(r.json()['msg'])
    redirect_url = r.json()['toUrl']
    r = s.get(redirect_url)
    return s

def main():
    for account in accounts:
        username = account["username"]
        password = account["password"]
        session = login(username, password)
        if session is not None:
            rand = str(round(time.time() * 1000))
            surl = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K'
            url = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
            url2 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN'
            url3 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
                "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
                "Host": "m.cloud.189.cn",
                "Accept-Encoding": "gzip, deflate",
            }
            response = session.get(surl, headers=headers)
            netdiskBonus = response.json()['netdiskBonus']
            if response.json()['isSign'] == "false":
                print(f"未签到，签到获得{netdiskBonus}M空间")
                res1 = f"未签到，签到获得{netdiskBonus}M空间"
            else:
                print(f"已经签到过了，签到获得{netdiskBonus}M空间")
                res1 = f"已经签到过了，签到获得{netdiskBonus}M空间"

            response = session.get(url, headers=headers)
            if "errorCode" in response.text:
                print(response.text)
                res2 = ""
            else:
                description = response.json()['description']
                print(f"抽奖获得{description}")
                res2 = f"抽奖获得{description}"

            time.sleep(random.randint(5, 10))  
            response = session.get(url2, headers=headers)
            if "errorCode" in response.text:
                print(response.text)
                res3 = ""
            else:
                description = response.json()['prizeName']
                print(f"抽奖获得{description}")
                res3 = f"抽奖获得{description}"

            time.sleep(random.randint(5, 10))      
            response = session.get(url3, headers=headers)
            if "errorCode" in response.text:
                print(response.text)
                res4 = ""
            else:
                description = response.json()['prizeName']
                print(f"链接3抽奖获得{description}")
                res4 = f"链接3抽奖获得{description}"

            if plustoken:
                title = '天翼云盘签到'
                url = 'http://www.pushplus.plus/send'
                data = {
                    "token": plustoken,
                    "title": title,
                    "content": f'{username}\n{res1}\n{res2}\n{res3}\n{res4}\n',
                }
                body = json.dumps(data).encode(encoding='utf-8')
                headers = {'Content-Type': 'application/json'}
                requests.post(url, data=body, headers=headers)

def lambda_handler(event, context):  # aws default
    main()

def main_handler(event, context):  # tencent default
    main()

def handler(event, context):  # aliyun default
    main()

if __name__ == "__main__":
    main()
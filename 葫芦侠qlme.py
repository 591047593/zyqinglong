import requests
import time
import hashlib
import json
import uuid
import os

random_uuid = str(uuid.uuid4())

device_codess=f'[d]{uuid.uuid4()}'
hlx_android_id=f'{uuid.uuid4()}'
hlx_oaid=f'{uuid.uuid4()}'

login_url = 'https://floor.huluxia.com/account/login/ANDROID/4.1.8'
# 目标URL
url = 'https://floor.huluxia.com/user/signin/ANDROID/4.1.8'
# 固定参数
params_base = {
    'platform': 2,
    'gkey': '000000',
    'app_version': '4.3.0.4',
    'versioncode': '20141495',
    'market_id': 'floor_web',
    'device_code': device_codess,
    'phone_brand_type': 'IPHONE',  # 根据实际情况修改
    'hlx_imei': '',
    'hlx_android_id': hlx_android_id,
    'hlx_oaid': hlx_oaid,
}

# 请求头
headers = {
    'Connection': 'close',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'floor.huluxia.com',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.8.1'
}


def md5(param):
    m = hashlib.md5()
    m.update(param.encode('utf-8'))
    return m.hexdigest()


# 生成签名函数
def generate_sign(account, login_type, password_md5):
    sign_str = f'account{account}device_code{device_codess}password{password_md5}voice_codefa1c28a5b62e79c3e63d9030b6142e4b'
    # print(sign_str)
    return md5(sign_str)


# 用户登录并获取_key
def login(username, password):
    login_data = {
        'account': username,
        'login_type': 2,  # 根据实际情况修改
        'password': md5(password),
        'sign': generate_sign(username, 2, md5(password))
    }

    global params_base  # 使用global关键字来修改外部的params_base字典
    response = requests.post(login_url, headers=headers, params=params_base, data=login_data)
    response_json = response.json()  # 解析JSON响应

    # 检查登录是否成功
    if response_json.get('status') == 1:  # 假设status字段为1时表示登录成功
        # 读取_key值
        key = response_json.get('_key')
        if key:
            params_base['_key'] = key
          #  print('_key:', params_base['_key'])
        else:
            print("登录失败，未返回_key")
            return False
    else:
        print("登录失败，请检查用户名和密码")
        return False
    return True

def 响应解析提取经验和天数(response_text):
    try:
        # 将响应文本转换为JSON对象
        response_json = json.loads(response_text)
        # 提取continueDays和experienceVal的值
        continue_days = response_json.get('continueDays', 0)
        experience_val = response_json.get('experienceVal', 0)
        # 返回提取的值
        return continue_days, experience_val
    except json.JSONDecodeError:
        print("IP被封，请更换网络")
        return 0, 0

# 假设环境变量hlx的值是这样的："user1,password1@user2,password2"
accounts = os.getenv('hlx')
# 使用@作为分隔符分割账户
accounts_list = accounts.split('@')
# 然后对每个账户使用,作为分隔符分割用户名和密码
accounts_dict = []
for account in accounts_list:
    if '#' in account:
        username, password = account.split('#')
        accounts_dict.append({'username': username, 'password': password})

num_of_accounts = len(accounts_list)
print(f"共检测到{num_of_accounts}个账户")
# print(accounts_list)
for i, account in enumerate(accounts_list, start=1):
    print(f"正在签到第{i}个账户:{account}")
    username, password = account.split('#')
    if login(username, password):
        catids = {1, 2, 3, 4, 6, 15, 16, 21, 22, 68, 29, 69, 43, 44, 45, 67, 57, 58, 60, 63, 67, 68, 69, 70, 71, 76, 77,
                  81, 82, 84, 90, 92, 94, 96, 98, 102, 105, 107, 108, 110, 111, 115, 119, 123, 124, 125}  # 这里添加完整的ID集合
        countexp = 0
        experience_all = 0  # 总获得经验
        noID = []  # 没有ID的板块数

        # 遍历ID池中的每个ID
        for cat_id in catids:
            # 更新参数中的cat_id
            params = params_base.copy()
            params['cat_id'] = cat_id

            # 获取当前时间戳整秒
            time1 = str(time.time()).split(".")[0] + str(time.time()).split(".")[1][0:3]

            # 更新参数中的时间
            params['time'] = time1

            # 请求体
            sign = md5(f'cat_id{cat_id}time{time1}fa1c28a5b62e79c3e63d9030b6142e4b')
            data = {'sign': sign}

            # 发送POST请求
            response = requests.post(url, headers=headers, params=params, data=data)
            time.sleep(0.4)
            continue_days, experience_val = 响应解析提取经验和天数(response.text)
            if experience_val == 0:
                print(f"板块不存在,ID：{cat_id}")
                noID = noID + [cat_id]
                continue
            countexp = countexp + 1  # 循环一次，板块数+1
            experience_all = experience_all + experience_val  # 总获得经验
            # 打印响应内容
            print(f"板块ID：{cat_id},获得经验：{experience_val},连续签到天数：{continue_days}")
        print(f"板块总数：{countexp},获得经验：{experience_all}")
        print(f"没有ID的板块数：{noID}")
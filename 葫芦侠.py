# -*- coding: utf-8 -*-
"""
葫芦侠签到（多账号）
export hlx="user1#pwd1@user2#pwd2"
cron: 0 7 * * *
const $ = new Env("葫芦侠");
"""
import os
import time
import json
import uuid
import hashlib
import requests
from datetime import datetime

# 复用同目录 sendNotify.py
from sendNotify import send
send_notify = send           # 别名，保持后面零改动

# ---------- 新通知风格 ----------
def fmt_single(user, exp, days, miss):
    return f"""🌟 葫芦侠签到结果
👤 用户: {user}
📊 连续签到: {days} 天
🎁 本次经验: +{exp}
🈚 无效板块: {miss}
⏰ 时间: {datetime.now().strftime('%m-%d %H:%M')}"""

def fmt_summary(total, ok, all_exp):
    return f"""📊 葫芦侠签到汇总
📈 总计: {total} 账号
✅ 成功: {ok} 账号
🎓 总经验: +{all_exp}
📊 成功率: {ok/total*100:.1f}%
⏰ 完成: {datetime.now().strftime('%m-%d %H:%M')}"""
# ----------------------------------


random_uuid = str(uuid.uuid4())
device_codess = f'[d]{uuid.uuid4()}'
hlx_android_id = f'{uuid.uuid4()}'
hlx_oaid = f'{uuid.uuid4()}'

login_url = 'https://floor.huluxia.com/account/login/ANDROID/4.1.8'
sign_url = 'https://floor.huluxia.com/user/signin/ANDROID/4.1.8'

params_base = {
    'platform': 2, 'gkey': '000000', 'app_version': '4.3.0.4', 'versioncode': '20141495',
    'market_id': 'floor_web', 'device_code': device_codess, 'phone_brand_type': 'IPHONE',
    'hlx_imei': '', 'hlx_android_id': hlx_android_id, 'hlx_oaid': hlx_oaid,
}

headers = {
    'Connection': 'close', 'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'floor.huluxia.com', 'Accept-Encoding': 'gzip', 'User-Agent': 'okhttp/3.8.1'
}


def md5(param):
    return hashlib.md5(param.encode('utf-8')).hexdigest()


def generate_sign(account, login_type, password_md5):
    sign_str = f'account{account}device_code{device_codess}password{password_md5}voice_codefa1c28a5b62e79c3e63d9030b6142e4b'
    return md5(sign_str)


def login(username, password):
    login_data = {
        'account': username,
        'login_type': 2,
        'password': md5(password),
        'sign': generate_sign(username, 2, md5(password))
    }
    resp = requests.post(login_url, headers=headers, params=params_base, data=login_data, timeout=15)
    js = resp.json()
    if js.get('status') == 1:
        key = js.get('_key')
        if key:
            params_base['_key'] = key
            return True
    print(f"账号 {username} 登录失败：{js}")
    return False


def parse_exp_days(text):
    try:
        j = json.loads(text)
        return j.get('continueDays', 0), j.get('experienceVal', 0)
    except json.JSONDecodeError:
        print("IP被封或响应异常")
        return 0, 0


if __name__ == '__main__':
    accounts = os.getenv('hlx', '').strip()
    if not accounts:
        print("⚠️ 未配置环境变量 hlx")
        exit()
    account_list = [a for a in accounts.split('@') if a]
    total_acc = len(account_list)
    ok_acc = 0
    total_exp = 0

    for idx, acc in enumerate(account_list, 1):
        username, password = acc.split('#', 1)
        print(f"======== 第 {idx}/{total_acc} 账号：{username} ========")
        if not login(username, password):
            send_notify("葫芦侠签到失败", fmt_single(username, 0, 0, "登录失败"))
            continue

        catids = {1, 2, 3, 4, 6, 15, 16, 21, 22, 68, 29, 69, 43, 44, 45, 67, 57, 58, 60, 63, 70, 71, 76, 77,
                  81, 82, 84, 90, 92, 94, 96, 98, 102, 105, 107, 108, 110, 111, 115, 119, 123, 124, 125}
        countexp = 0
        exp_all = 0
        no_id = []

        for cat_id in catids:
            params = params_base.copy()
            params['cat_id'] = cat_id
            t = str(int(time.time() * 1000))
            params['time'] = t
            sign = md5(f'cat_id{cat_id}time{t}fa1c28a5b62e79c3e63d9030b6142e4b')
            resp = requests.post(sign_url, headers=headers, params=params,
                                 data={'sign': sign}, timeout=15)
            days, exp = parse_exp_days(resp.text)
            if exp == 0:
                no_id.append(cat_id)
                continue
            countexp += 1
            exp_all += exp
            print(f"板块ID：{cat_id}, 获得经验：{exp}, 连续签到：{days}")
            time.sleep(0.4)

        print(f"有效板块：{countexp}, 总经验：{exp_all}, 无效板块：{no_id}")
        ok_acc += 1
        total_exp += exp_all
        send_notify("葫芦侠签到", fmt_single(username, exp_all, days, len(no_id)))

    if total_acc:
        send_notify("葫芦侠签到汇总", fmt_summary(total_acc, ok_acc, total_exp))

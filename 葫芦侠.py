#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
葫芦侠三楼·38版块签到（整洁通知版 | 含成功计数）
变量：hlx  手机号,密码@手机号2,密码2
cron: 0 8 * * *
"""
import os
import json
import time
import random
import hashlib
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- 图标通知模板 ----------
def fmt_single(user, exp, days, miss, succ):
    return f"""🌟 葫芦侠签到结果
👤 用户: {user}
📊 连续签到: {days} 天
✅ 成功板块: {succ} 个
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
# ------------------------------------


# ---------- 原仓库版块映射 ----------
CAT_NAME = {
    "1":"3楼公告版","2":"泳池","3":"自拍","4":"游戏","6":"意见反馈",
    "15":"葫芦山","16":"玩机广场","21":"穿越火线","22":"英雄联盟","29":"次元阁",
    "43":"实用软件","44":"玩机教程","45":"原创技术","57":"头像签名","58":"恶搞",
    "60":"未知版块","63":"我的世界","67":"MC贴子","68":"资源审核","69":"优秀资源",
    "70":"福利活动","71":"王者荣耀","76":"娱乐天地","81":"手机美化","82":"3楼学院",
    "84":"3楼精选","92":"模型玩具","94":"三楼活动","96":"技术分享","98":"制图工坊",
    "102":"LOL手游","108":"新游推荐","110":"原神","111":"Steam","115":"金铲铲之战",
    "119":"爱国爱党","125":"妙易堂","126":"三角洲行动"
}
CAT_IDS = list(CAT_NAME.keys())


def send_notify(title, content):
    try:
        from sendNotify import send
        send(title, content)
    except Exception:
        pass


def md5(txt: str) -> str:
    return hashlib.md5(txt.encode()).hexdigest()


def login(phone, pwd):
    device_model = f"iPhone{random.randint(14,17)},{random.randint(1,6)}"
    device_code = f"%5Bd%5D5125c3c6-f{random.randint(111, 987)}-4c6b-81cf-9bc467522d61"
    url = f"https://floor.huluxia.com/account/login/IOS/1.0?" \
          f"access_token=&app_version=1.2.2&code=&device_code={device_code}&device_model={device_model}" \
          f"&email={phone}&market_id=floor_huluxia&openid=&password={md5(pwd)}&phone=&platform=1"
    headers = {
        "Connection": "close", "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "okhttp/3.8.1", "Host": "floor.huluxia.com",
    }
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.text:
                j = r.json()
                if j.get("status") == 1:
                    return j["_key"], j["user"]["userID"]
            print(f"登录失败：{r.text}")
        except Exception as e:
            print(f"登录异常：{e} 重试{i+1}")
        time.sleep(3)
    return None, None


def user_info(_key, user_id):
    url = f"http://floor.huluxia.com/user/info/ANDROID/4.1.8?" \
          f"platform=2&gkey=000000&app_version=4.3.1.5.2&versioncode=398&market_id=floor_web&_key={_key}" \
          f"&device_code=%5Bd%5D5125c3c6-f{random.randint(111, 987)}-4c6b-81cf-9bc467522d61" \
          f"&phone_brand_type={random.choice(['MI','Huawei','UN','OPPO','VO'])}&user_id={user_id}"
    headers = {"Connection": "close", "Accept-Encoding": "gzip, deflate", "User-Agent": "okhttp/3.8.1", "Host": "floor.huluxia.com"}
    try:
        j = requests.get(url, headers=headers, timeout=10).json()
        return j["nick"], j["level"], j["exp"], j["nextExp"]
    except:
        return "未知", 0, 0, 0


def sign_get(cat_id: str) -> str:
    i = str(int(time.time()))
    r = "fa1c28a5b62e79c3e63d9030b6142e4b"
    return md5(f"cat_id{cat_id}time{i}{r}").upper()


def sign_one_board(_key, user_id, cat_id: str):
    sign = sign_get(cat_id)
    url = f"http://floor.huluxia.com/user/signin/ANDROID/4.1.8?" \
          f"platform=2&gkey=000000&app_version=4.3.1.5.2&versioncode=398&market_id=floor_web&_key={_key}" \
          f"&device_code=%5Bd%5D5125c3c6-f{random.randint(111, 987)}-4c6b-81cf-9bc467522d61" \
          f"&phone_brand_type={random.choice(['MI','Huawei','UN','OPPO','VO'])}&cat_id={cat_id}&time={int(time.time())}"
    headers = {
        "Connection": "close", "Accept-Encoding": "gzip, deflate",
        "User-Agent": "okhttp/3.8.1", "Host": "floor.huluxia.com",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }
    try:
        r = requests.post(url, data={"sign": sign}, headers=headers, timeout=10).json()
        if r.get("status") == 1:
            exp = r.get("experienceVal", 0)
            days = r.get("continueDays", 0)
            return True, f"【{CAT_NAME[cat_id]}】+{exp} exp", exp, days
        else:
            return False, f"【{CAT_NAME[cat_id]}】签到失败", 0, 0
    except Exception as e:
        return False, f"【{CAT_NAME[cat_id]}】异常：{e}", 0, 0


def sign_all_boards(phone, pwd):
    """38 版块循环签到（带回成功计数）"""
    _key, user_id = login(phone, pwd)
    if not _key:
        return False, f"{phone} 登录失败", 0, 0, 0
    nick, level, exp, next_exp = user_info(_key, user_id)
    log_lines = [f"{nick}(Lv.{level}) 开始签到"]
    total_exp = 0
    succ_count = 0                 # 成功计数
    for cat_id in CAT_IDS:
        suc, msg, add_exp, days = sign_one_board(_key, user_id, cat_id)
        total_exp += add_exp
        if suc: succ_count += 1   # 计数
        log_lines.append(msg)
        time.sleep(0.5)
    log_lines.append(f"共获得 {total_exp} exp，连续签到 {days} 天")
    return True, "\n".join(log_lines), total_exp, days, succ_count


# ---------- 主入口（整洁通知） ----------
if __name__ == '__main__':
    accounts = os.environ.get("hlx", "")
    if not accounts:
        print("❌ 未设置 hlx")
        exit()

    account_list = [a.strip() for a in accounts.split("@") if a and "," in a]
    total_acc = len(account_list)
    ok_acc = 0
    all_exp = 0

    for idx, acc in enumerate(account_list, 1):
        username, password = acc.split(",", 1)
        print(f"======== 第 {idx}/{total_acc} 账号：{username} ========")
        flag, log, exp, days, succ = sign_all_boards(username.strip(), password.strip())
        if not flag:
            send_notify("葫芦侠签到失败", fmt_single(username, 0, 0, "登录失败", 0))
            continue
        ok_acc += 1
        all_exp += exp
        # 单账号推送（整洁模板）
        miss = 38 - succ
        send_notify("葫芦侠签到", fmt_single(username, exp, days, miss, succ))

    # 总汇总推送
    if total_acc:
        send_notify("葫芦侠签到汇总", fmt_summary(total_acc, ok_acc, all_exp))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT论坛极速签到（只用同目录 sendNotify）
export mtluntan="账号1&密码1@账号2&密码2"
cron: 0 8 * * *
"""
import os
import re
import time
import requests
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- 仅用同目录 sendNotify.py ----------
from sendNotify import send   # 没有文件就报错，不兜底

# ---------- 模板（零改动） ----------
def fmt_single(user, rank, reward, reason):
    return f"""🌟 MT论坛签到结果
👤 用户: {user}
📊 排名: {rank}
🎁 奖励: {reward} 金币
📝 签到: {reason}
⏰ 时间: {datetime.now().strftime('%m-%d %H:%M:%S')}"""

def fmt_summary(total, ok):
    if total == 0:
        return "📊 MT论坛签到汇总\n📈 总计: 0 账号"
    return f"""📊 MT论坛签到汇总
📈 总计: {total}个账号
✅ 成功: {ok}个
❌ 失败: {total-ok}个
📊 成功率: {ok/total*100:.1f}%
⏰ 完成: {datetime.now().strftime('%m-%d %H:%M:%S')}"""

# ---------- 业务函数（原样） ----------
def mt_sign_speed(username, password):
    """原仓库逻辑：登录 → 签到 → 返回结果"""
    device_model = f"iPhone{random.randint(14,17)},{random.randint(1,6)}"
    device_code = f"%5Bd%5D5125c3c6-f{random.randint(111, 987)}-4c6b-81cf-9bc467522d61"
    url_login = f"https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login"
    url_post = f"https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={{loginhash}}&inajax=1"
    url_info = f"http://floor.huluxia.com/user/info/ANDROID/4.1.8?platform=2&gkey=000000&app_version=4.3.1.5.2&versioncode=398&market_id=floor_web&_key={{_key}}&device_code={device_code}&phone_brand_type={random.choice(['MI','Huawei','UN','OPPO','VO'])}&user_id={{user_id}}"
    url_sign = f"https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={{formhash}}"

    headers = {
        "Connection": "close", "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "okhttp/3.8.1", "Host": "floor.huluxia.com",
    }
    try:
        # 1. 登录
        login_page = requests.get(url_login, headers=headers, timeout=10)
        loginhash = re.findall(r'loginhash=(.*?)"', login_page.text)[0]
        formhash = re.findall(r'name="formhash" value="(.*?)"', login_page.text)[0]
        requests.post(url_post.format(loginhash=loginhash), data={
            'formhash': formhash, 'referer': 'https://bbs.binmt.cc/forum.php',
            'loginfield': 'username', 'username': username, 'password': password,
            'questionid': '0', 'answer': ''
        }, headers=headers, timeout=10)

        # 2. 签到页 & 零点等待
        sign_page = requests.get("https://bbs.binmt.cc/k_misign-sign.html", headers=headers, timeout=10).text
        formhash = re.findall(r'name="formhash" value="(.*?)"', sign_page)[0]
        wait_max = 5
        while wait_max > 0:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0 and now.second <= 2:
                break
            time.sleep(0.2)
            wait_max -= 0.2

        # 3. 签到
        sign_res = requests.get(f"https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}", headers=headers, timeout=10).text
        if '已签' in sign_res or '签到成功' in sign_res:
            rank = re.findall(r'您的签到排名：(.*?)</div>', sign_page)[0]
            reward = re.findall(r'id="lxreward" value="(.*?)"', sign_page)[0]
            return True, username, "签到成功", rank, reward
        else:
            return False, username, "签到失败", "0", "0"
    except Exception as e:
        return False, username, f"异常：{e}", "0", "0"


# ---------- 主入口（只用 send） ----------
if __name__ == '__main__':
    env = os.environ.get("mtluntan")
    if not env:
        print("❌ 未设置 mtluntan")
        exit()

    accounts = [a.strip() for a in env.split("@") if a and "&" in a]
    ok = 0
    with ThreadPoolExecutor(max_workers=3) as exe:
        futures = [exe.submit(mt_sign_speed, u.strip(), p.strip())
                   for acc in accounts for u, p in [acc.split("&", 1)]]
        for f in as_completed(futures):
            flag, user, msg, rank, reward = f.result()
            if flag:
                ok += 1
            log_line = fmt_single(user, rank, reward, msg)
            print(log_line)
            send("MT论坛签到", log_line)          # 只用 send
    summary = fmt_summary(len(accounts), ok)
    print(summary)
    send("MT论坛签到汇总", summary)

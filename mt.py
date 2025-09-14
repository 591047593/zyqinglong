#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT论坛极速签到（青龙版）
变量名：mtluntan   格式：账号1&密码1@账号2&密码2
export mtluntan=""
定时建议：59 23 * * *  （23:59 启动，内部等零点，最多 5 秒）
手动运行：5 秒内立即执行，不卡死
"""
import os
import re
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------------------------
def send_notify(title, content):
    try:
        from sendNotify import send
        send(title, content)
    except Exception:
        print("跳过通知")

def fmt_single(user, rank, reward, reason):
    return f"""🌟 MT论坛签到结果
👤 用户: {user}
📊 排名: {rank}
🎁 奖励: {reward} 金币
📝 签到: {reason}
⏰ 时间: {datetime.now().strftime('%m-%d %H:%M:%S')}"""

def fmt_summary(total, ok):
    return f"""📊 MT论坛签到汇总
📈 总计: {total}个账号
✅ 成功: {ok}个
❌ 失败: {total-ok}个
📊 成功率: {ok/total*100:.1f}%
⏰ 完成: {datetime.now().strftime('%m-%d %H:%M:%S')}"""

# -------------------------------------------------
def mt_sign_speed(username, password):
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    })
    try:
        # 1. 取 loginhash / formhash
        login_page = s.get(
            'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        )
        loginhash = re.findall(r'loginhash=(.*?)"', login_page.text)[0]
        formhash = re.findall(r'name="formhash" value="(.*?)"', login_page.text)[0]

        # 2. 登录
        s.post(
            f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1',
            data={
                'formhash': formhash,
                'referer': 'https://bbs.binmt.cc/forum.php',
                'loginfield': 'username',
                'username': username,
                'password': password,
                'questionid': '0',
                'answer': ''
            }
        )

        # 3. 拿签到页新 formhash
        sign_page = s.get('https://bbs.binmt.cc/k_misign-sign.html').text
        formhash = re.findall(r'name="formhash" value="(.*?)"', sign_page)[0]

        # 4. 等零点，最多 5 秒（防卡死）
        wait_max = 5
        while wait_max > 0:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0 and now.second <= 2:
                break
            time.sleep(0.2)
            wait_max -= 0.2

        # 5. 签到
        sign_res = s.get(
            f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        ).text

        if '已签' in sign_res or '签到成功' in sign_res:
            rank = re.findall(r'您的签到排名：(.*?)</div>', sign_page)[0]
            reward = re.findall(r'id="lxreward" value="(.*?)"', sign_page)[0]
            return True, username, "签到成功", rank, reward
        else:
            return False, username, "签到失败", "0", "0"
    except Exception as e:
        return False, username, f"异常：{e}", "0", "0"

# -------------------------------------------------
if __name__ == '__main__':
    env = os.environ.get("mtluntan")
    if not env:
        print("❌ 未找到环境变量 mtluntan")
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
            # ① 写日志  ② 推通知
            log_line = fmt_single(user, rank, reward, msg)
            print(log_line)          # 青龙日志可见
            send_notify("MT论坛签到", log_line)
    summary = fmt_summary(len(accounts), ok)
    print(summary)
    send_notify("MT论坛签到汇总", summary)


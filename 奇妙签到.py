#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇妙应用签到（多账号 | 整洁通知）
export qm_token="token1#uid1@token2#uid2"
cron: 0 9 * * *
"""
import os
import requests
from datetime import datetime

# ---------- 安全导入 sendNotify ----------
send = None
try:
    import sendNotify
    send = sendNotify.send
except Exception as e:
    print("sendNotify 加载失败，使用兜底推送:", e)
    # 兜底推送
    html = content.replace("\n", "<br>")
    token = os.getenv("PUSH_PLUS_TOKEN")
    if token:
        url = "https://www.pushplus.plus/send"
        body = {"token": token, "title": title, "content": html, "template": "html"}
        try:
            r = requests.post(url, json=body, timeout=10)
            print("✅ PushPlus 完成" if r.json().get("code") == 200 else "❌ PushPlus 失败")
        except Exception as e:
            print("❌ PushPlus 异常:", e)
        return
    bark = os.getenv("BARK_KEY")
    if bark:
        url = f"https://api.day.app/{bark}/{title}/{content}"
        try:
            r = requests.get(url, timeout=10)
            print("✅ Bark 完成" if r.status_code == 200 else "❌ Bark 失败")
        except Exception as e:
            print("❌ Bark 异常:", e)
        return
    print("⚠️ 未配置任何令牌，跳过通知")


# ---------- 整洁通知模板 ----------
def fmt_single(user, coin, status):
    return f"""🌟 奇妙应用签到结果
👤 用户: {user}
💰 当前金币: {coin}
📝 签到: {status}
⏰ 时间: {datetime.now().strftime('%m-%d %H:%M')}"""

def fmt_summary(total, ok, all_coin):
    if total == 0:
        return "📊 奇妙应用签到汇总\n📈 总计: 0 账号"
    return f"""📊 奇妙应用签到汇总
📈 总计: {total} 账号
✅ 成功: {ok} 账号
💰 总金币: {all_coin}
📊 成功率: {ok / total * 100:.1f}%
⏰ 完成: {datetime.now().strftime('%m-%d %H:%M')}"""


# ---------- 业务 ----------
def sign_once(token, user_id):
    sign_url = "http://www.magicalapp.cn/user/api/signDays"
    coin_url = f"https://www.magicalapp.cn/api/game/api/getCoinP?userId={user_id}"
    headers = {"token": token}

    r1 = requests.get(sign_url, headers=headers, timeout=10)
    sign_ok = r1.status_code == 200

    r2 = requests.get(coin_url, timeout=10)
    coin = 0
    if r2.status_code == 200:
        coin = r2.json().get("data", 0)

    return sign_ok, coin


def main():
    tokens = (os.getenv("qm_token") or "").split("@")
    if not tokens:
        print("⚠️ 未配置环境变量 qm_token")
        return

    total = len(tokens)
    ok = 0
    all_coin = 0

    for idx, item in enumerate(tokens, 1):
        if "#" not in item:
            print(f"第{idx}个账号格式错误，跳过")
            continue
        token, user_id = item.split("#", 1)
        user = f"uid{user_id[-4:]}"

        print(f"======== 第 {idx}/{total} 账号：{user} ========")
        try:
            sign_ok, coin = sign_once(token, user_id)
            status = "签到成功" if sign_ok else "签到失败"
            print(status)
            if sign_ok:
                ok += 1
            all_coin += coin
            send_notify("奇妙应用签到", fmt_single(user, coin, status))
        except Exception as e:
            print("运行异常：", e)
            send_notify("奇妙应用签到失败", fmt_single(user, 0, "脚本异常"))

    if total:
        send_notify("奇妙应用签到汇总", fmt_summary(total, ok, all_coin))


if __name__ == "__main__":
    main()

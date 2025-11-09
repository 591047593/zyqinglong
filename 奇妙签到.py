# cron: 6 6 * * *
# mokey-qmyy-sign 

import requests, datetime, os

def main():
    token = os.getenv("mokey_qmyy_token")
    uid   = os.getenv("mokey_qmyy_id")
    if not token or not uid:
        raise Exception("环境变量 mokey_qmyy_token / mokey_qmyy_id 缺失")

    headers = {
        "token": token,
        "Host": "www.magicalapp.cn",
        "User-Agent": "okhttp/4.9.3"
    }

    # 1. 签到
    sign_resp = requests.get("http://www.magicalapp.cn/user/api/signDays", headers=headers)
    if sign_resp.status_code == 200:
        coin_sign = 5
        msg_sign  = "签到成功"
    else:
        coin_sign = 0
        msg_sign  = f"签到失败({sign_resp.status_code})"

    # 2. 爆硬币
    burst_resp = requests.get(f"https://www.magicalapp.cn/api/game/api/getCoinP?userId={uid}", headers=headers)
    try:
        burst_data = burst_resp.json()
        coin_burst = int(burst_data.get("data", 0)) if burst_data.get("code") == "200" else 0
        msg_burst  = f"爆硬币成功，获得 {coin_burst} 枚" if coin_burst else "爆硬币失败"
    except Exception:
        coin_burst = 0
        msg_burst  = "爆硬币接口异常"

    # 3. 通知
    total = coin_sign + coin_burst
    content = f"""奇妙应用自动签到结果
账号：{uid}
{msg_sign}
{msg_burst}
共计获得 {total} 枚金币
时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
    print(content)

    # 青龙通知
    try:
        from notify import send
        send("奇妙应用签到", content)
    except ImportError:
        print("未安装青龙 notify 模块，仅打印日志")

if __name__ == "__main__":
    main()

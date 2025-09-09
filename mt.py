"""
mt论坛自动签到
支持多用户运行
添加变量mtluntan
账号密码用&隔开
多用户用@隔开
例如账号1：10086 密码：1001 
账号1：1234 密码：1234
则变量为10086&1001@1234&1234
export mtluntan=""

cron: 0 0,7 * * *
const $ = new Env("mt论坛");
"""
import requests
import re
import os
import time
from datetime import datetime

# ----------------  新通知风格开始  ----------------
all_print_list = []

def myprint(msg):
    print(msg)
    all_print_list.append(msg)

# 统一发送入口
def send_notify(title, content):
    try:
        from sendNotify import send
        send(title, content)
    except Exception:
        pass

# 单账号结果模板
def fmt_single(user, rank, reward, reason):
    return f"""🌟 MT论坛签到结果

👤 用户: {user}
📊 排名: {rank}
🎁 奖励: {reward} 金币
📝 签到: {reason}
⏰ 时间: {datetime.now().strftime('%m-%d %H:%M')}"""

# 汇总模板
def fmt_summary(total, ok):
    return f"""📊 MT论坛签到汇总

📈 总计: {total}个账号
✅ 成功: {ok}个
❌ 失败: {total-ok}个
📊 成功率: {ok/total*100:.1f}%
⏰ 完成: {datetime.now().strftime('%m-%d %H:%M')}"""
# ----------------  新通知风格结束  ----------------


def main(username, password):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
    }
    session.get('https://bbs.binmt.cc', headers=headers)
    chusihua = session.get(
        'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',
        headers=headers
    )
    try:
        loginhash = re.findall('loginhash=(.*?)">', chusihua.text)[0]
        formhash = re.findall('formhash" value="(.*?)".*? />', chusihua.text)[0]
    except Exception as e:
        myprint('loginhash、formhash获取失败')
        return False, username, '获取校验值失败', '0', '0'

    denurl = f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1'
    data = {
        'formhash': formhash,
        'referer': 'https://bbs.binmt.cc/forum.php',
        'loginfield': 'username',
        'username': username,
        'password': password,
        'questionid': '0',
        'answer': '',
    }
    denlu = session.post(url=denurl, data=data, headers=headers).text

    if '欢迎您回来' in denlu:
        fzmz = re.findall('欢迎您回来，(.*?)，现在', denlu)[0]
        myprint(f'{fzmz}：登录成功')
        zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
        formhash = re.findall('formhash" value="(.*?)".*? />', zbqd)[0]
        qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        qd = session.get(url=qdurl, headers=headers).text
        qdyz = re.findall('<root><(.*?)</root>', qd)[0]
        myprint(f'签到状态：{qdyz}')
        if '已签' in qd:
            rank, reward = huoqu(session, formhash)
            return True, fzmz, qdyz, rank, reward
        return True, fzmz, qdyz, 'N/A', '0'
    else:
        reason = re.findall("CDATA(.*?)<", denlu)[0] if 'CDATA' in denlu else '登录失败'
        myprint(f'登录失败：{reason}')
        return False, username, reason, '0', '0'


def huoqu(session, formhash):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
    }
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    pai = re.findall('您的签到排名：(.*?)</div>', huo)[0]
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)[0]
    myprint(f'签到排名{pai}，奖励{jiang}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)
    return pai, jiang


if __name__ == '__main__':
    if 'mtluntan' not in os.environ:
        myprint('不存在青龙变量mtluntan')
        exit()

    accounts = os.environ.get("mtluntan").split("@")
    myprint(f'共找到{len(accounts)}个账号')
    ok_count = 0
    for acc in accounts:
        username, password = acc.split("&")
        try:
            flag, user, msg, rank, reward = main(username, password)
            if flag:
                ok_count += 1
                reason = f'签到成功（{msg}）'
            else:
                reason = f'签到失败（{msg}）'
        except Exception as e:
            user, rank, reward, reason = username, '0', '0', f'脚本异常：{e}'
        # 单账号新通知风格推送
        send_notify('MT论坛签到', fmt_single(user, rank, reward, reason))
        myprint('============📣单账号结束📣============')

    # 汇总新通知风格推送
    send_notify('MT论坛签到汇总', fmt_summary(len(accounts), ok_count))

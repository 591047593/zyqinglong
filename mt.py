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

# 初始化打印列表
all_print_list = []

def myprint(message):
    print(message)
    all_print_list.append(message)

# 发送通知消息
def send_notification_message(title):
    try:
        from sendNotify import send
        send(title, ''.join(all_print_list))
    except Exception as e:
        print('发送通知消息失败！')

def main(username, password):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
    session.get('https://bbs.binmt.cc', headers=headers)
    chusihua = session.get('https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login', headers=headers)
    try:
        loginhash = re.findall('loginhash=(.*?)">', chusihua.text)[0]
        formhash = re.findall('formhash" value="(.*?)".*? />', chusihua.text)[0]
    except Exception as e:
        myprint('loginhash、formhash获取失败')
        return False
    
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
            huoqu(session, formhash)
    else:
        myprint('登录失败')
        print(re.findall("CDATA(.*?)<", denlu)[0])
    return True

def huoqu(session, formhash):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    pai = re.findall('您的签到排名：(.*?)</div>', huo)[0]
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)[0]
    myprint(f'签到排名{pai}，奖励{jiang}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)

if __name__ == '__main__':
    if 'mtluntan' in os.environ:
        fen = os.environ.get("mtluntan").split("@")
        myprint(f'查找到{len(fen)}个账号')
        myprint('==================================')
        for duo in fen:
            username, password = duo.split("&")
            try:
                main(username, password)
            except Exception as e:
                myprint(f'发生错误：{e}')
            myprint('============📣结束📣============')
    else:
        myprint('不存在青龙、github变量')
        exit()
    
    try:
        send_notification_message('mt论坛')  # 发送通知
    except Exception as e:
        print('小错误')


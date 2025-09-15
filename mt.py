#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT论坛自动签到（精简版）
支持多用户：export mtluntan="账号1&密码1@账号2&密码2"
cron: 0 0,7 * * *
const $ = new Env("mt论坛");
"""
import requests
import re
import os
from requests import session

# 全局配置（核心参数保留）
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
BASE_URL = "https://bbs.binmt.cc"
LOG_LIST = []  # 收集日志，用于通知


def log_print(msg):
    """统一日志打印与收集"""
    print(msg)
    LOG_LIST.append(msg)


def send_notify(title):
    """发送通知（依赖同目录 sendNotify.py）"""
    try:
        from sendNotify import send
        send(title, "\n".join(LOG_LIST))
        log_print("✅ 通知发送成功")
    except Exception as e:
        log_print(f"❌ 通知发送失败：{str(e)}")


def get_login_params(s):
    """获取登录所需的 loginhash 和 formhash"""
    login_page_url = f"{BASE_URL}/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login"
    try:
        resp = s.get(login_page_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()  # 触发 HTTP 错误
        
        # 正则匹配（增加容错，避免索引错误）
        loginhash_match = re.search(r'loginhash=(.*?)">', resp.text)
        formhash_match = re.search(r'formhash" value="(.*?)"', resp.text)
        
        if not loginhash_match or not formhash_match:
            log_print("❌ 未匹配到 loginhash/formhash")
            return None, None
        
        return loginhash_match.group(1), formhash_match.group(1)
    except Exception as e:
        log_print(f"❌ 获取登录参数失败：{str(e)}")
        return None, None


def login(s, username, password, loginhash, formhash):
    """用户登录"""
    login_url = f"{BASE_URL}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1"
    data = {
        "formhash": formhash,
        "referer": f"{BASE_URL}/forum.php",
        "loginfield": "username",
        "username": username,
        "password": password,
        "questionid": "0",
        "answer": ""
    }
    try:
        resp = s.post(
            login_url,
            headers={"User-Agent": USER_AGENT},
            data=data,
            timeout=10
        )
        resp.raise_for_status()
        
        if "欢迎您回来" in resp.text:
            # 提取用户昵称
            nick_match = re.search(r'欢迎您回来，(.*?)，现在', resp.text)
            nick = nick_match.group(1) if nick_match else username
            log_print(f"✅ {nick} 登录成功")
            return True, nick
        else:
            # 提取登录失败原因
            err_match = re.search(r"CDATA\[(.*?)\]", resp.text)
            err_msg = err_match.group(1) if err_match else "未知原因"
            log_print(f"❌ {username} 登录失败：{err_msg}")
            return False, username
    except Exception as e:
        log_print(f"❌ {username} 登录异常：{str(e)}")
        return False, username


def sign_in(s, username):
    """执行签到并获取结果"""
    sign_page_url = f"{BASE_URL}/k_misign-sign.html"
    try:
        # 1. 获取签到页 formhash
        resp = s.get(sign_page_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        
        formhash_match = re.search(r'formhash" value="(.*?)"', resp.text)
        if not formhash_match:
            log_print(f"❌ {username} 未匹配到签到 formhash")
            return False
        
        formhash = formhash_match.group(1)
        
        # 2. 执行签到
        sign_url = f"{BASE_URL}/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}"
        sign_resp = s.get(sign_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        sign_resp.raise_for_status()
        
        # 解析签到结果
        result_match = re.search(r'<root><(.*?)</root>', sign_resp.text)
        result = result_match.group(1) if result_match else sign_resp.text[:50]
        
        if "已签" in result or "签到成功" in result:
            log_print(f"✅ {username} 签到状态：{result}")
            # 获取排名与奖励
            rank_match = re.search(r'您的签到排名：(.*?)</div>', resp.text)
            reward_match = re.search(r'id="lxreward" value="(.*?)"', resp.text)
            rank = rank_match.group(1) if rank_match else "未知"
            reward = reward_match.group(1) if reward_match else "0"
            log_print(f"📊 {username} 签到排名：{rank}，奖励：{reward} 金币")
            
            # 退出登录（多用户防冲突）
            logout_url = f"{BASE_URL}/member.php?mod=logging&action=logout&formhash={formhash}"
            s.get(logout_url, headers={"User-Agent": USER_AGENT}, timeout=5)
            return True
        else:
            log_print(f"❌ {username} 签到失败：{result}")
            return False
    except Exception as e:
        log_print(f"❌ {username} 签到异常：{str(e)}")
        return False


def process_account(username, password):
    """处理单个账号的登录-签到流程（含重试）"""
    log_print(f"\n=== 开始处理账号：{username} ===")
    max_retry = 3  # 最大重试次数
    retry_count = 0
    
    while retry_count < max_retry:
        retry_count += 1
        log_print(f"🔄 第 {retry_count} 次尝试")
        
        # 每个账号单独创建 session，避免 cookie 残留
        s = session()
        s.headers.update({"User-Agent": USER_AGENT})
        
        # 步骤：获取登录参数 → 登录 → 签到
        loginhash, formhash = get_login_params(s)
        if not loginhash or not formhash:
            continue
        
        login_success, nick = login(s, username, password, loginhash, formhash)
        if not login_success:
            continue
        
        sign_success = sign_in(s, nick)
        if sign_success:
            return True  # 成功则退出重试
    
    log_print(f"❌ {username} 超出最大重试次数（{max_retry}次），处理失败")
    return False


def main():
    log_print("============ MT 论坛签到启动 ============")
    # 获取环境变量中的账号
    mt_env = os.environ.get("mtluntan")
    if not mt_env:
        log_print("❌ 未配置 mtluntan 环境变量")
        send_notify("MT论坛签到失败")
        return
    
    # 解析多用户（按 @ 分割账号，按 & 分割账号密码）
    accounts = [acc.strip() for acc in mt_env.split("@") if acc.strip() and "&" in acc.strip()]
    if not accounts:
        log_print("❌ 账号格式错误（正确格式：账号1&密码1@账号2&密码2）")
        send_notify("MT论坛签到失败")
        return
    
    log_print(f"📌 共检测到 {len(accounts)} 个账号")
    success_count = 0
    
    # 处理所有账号
    for acc in accounts:
        username, password = acc.split("&", 1)  # 只分割第一个 &（避免密码含 &）
        if process_account(username.strip(), password.strip()):
            success_count += 1
    
    # 汇总结果
    log_print(f"\n============ 签到汇总 ============")
    log_print(f"📊 总账号数：{len(accounts)}")
    log_print(f"✅ 成功数：{success_count}")
    log_print(f"❌ 失败数：{len(accounts) - success_count}")
    log_print(f"📈 成功率：{success_count/len(accounts)*100:.1f}%" if accounts else "0%")
    
    # 发送通知
    notify_title = f"MT论坛签到完成（{success_count}/{len(accounts)} 成功）"
    send_notify(notify_title)


if __name__ == "__main__":
    main()
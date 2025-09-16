"""
MT论坛自动签到（详细单账号通知版）
支持多用户配置：
- 环境变量名：mtluntan
- 单账号格式：账号&密码（例：10086&123456）
- 多账号格式：账号1&密码1@账号2&密码2（用@分隔）
cron: 0 0,7 * * *  # 每天0点、7点执行
const $ = new Env("MT论坛签到");
"""
import requests
import re
import os
import time
from datetime import datetime

# ---------------- 全局初始化与基础配置 ----------------
# 请求会话（保持cookie）
SESSION = requests.session()
# 论坛基础URL
BASE_URL = "https://bbs.binmt.cc"
# 请求头（模拟浏览器）
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "close"
}
# 最大重试次数（单账号签到失败后重试）
MAX_RETRY = 3


# ---------------- 工具函数 ----------------
def myprint(msg):
    """自定义打印：输出到控制台"""
    print(msg)


def format_account_notify_content(username, process_logs, success):
    """格式化单个账号的通知内容：详细展示所有过程"""
    # 构建通知标题
    status_emoji = "✅" if success else "❌"
    notify_title = f"{status_emoji} MT论坛签到结果 - {username[:4]}***"
    
    # 构建通知内容
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = [
        f"【{notify_title}】",
        f"📅 执行时间：{current_time}",
        "=" * 45,
        "📝 签到详细过程"
    ]
    
    # 添加所有处理日志
    for log in process_logs:
        # 为不同类型的日志添加相应的emoji
        if "成功" in log:
            content.append(f"✅ {log}")
        elif "失败" in log:
            content.append(f"❌ {log}")
        elif "重试" in log:
            content.append(f"🔄 {log}")
        elif "登录" in log or "签到" in log:
            content.append(f"📌 {log}")
        else:
            content.append(f"   {log}")
    
    # 尾部信息
    content.extend([
        "=" * 45,
        "💡 失败排查建议：",
        "   1. 检查账号密码是否正确",
        "   2. 确认网络是否能访问论坛",
        "   3. 手动登录检查是否需要验证码",
        f"🔗 论坛地址：{BASE_URL}"
    ])

    return notify_title, "\n".join(content)


def send_account_notification(username, process_logs, success):
    """发送单个账号的详细通知"""
    try:
        from sendNotify import send
        notify_title, notify_content = format_account_notify_content(username, process_logs, success)
        send(notify_title, notify_content)
        myprint("📤 账号通知发送成功！")
    except ImportError:
        myprint("⚠️  未找到sendNotify.py文件，无法发送通知")
    except Exception as e:
        myprint(f"❌ 通知发送失败：{str(e)}")


def send_system_notification(message):
    """发送系统级通知（如无账号配置等）"""
    try:
        from sendNotify import send
        notify_title = "⚠️ MT论坛签到系统通知"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = [
            f"【{notify_title}】",
            f"📅 时间：{current_time}",
            "=" * 45,
            message,
            "=" * 45,
            f"🔗 论坛地址：{BASE_URL}"
        ]
        send(notify_title, "\n".join(content))
        myprint("📤 系统通知发送成功！")
    except:
        myprint(f"⚠️  系统通知发送失败：{message}")


def get_login_params():
    """获取登录所需的loginhash和formhash"""
    login_page_url = f"{BASE_URL}/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login"
    try:
        response = SESSION.get(
            url=login_page_url,
            headers=REQUEST_HEADERS,
            timeout=15
        )
        response.raise_for_status()

        loginhash_match = re.search(r'loginhash=([a-zA-Z0-9]+)', response.text)
        formhash_match = re.search(r'formhash" value="([^"]+)"', response.text)

        if not loginhash_match or not formhash_match:
            return None, None, "未匹配到loginhash或formhash（页面结构可能变更）"

        loginhash = loginhash_match.group(1)
        formhash = formhash_match.group(1)
        return loginhash, formhash, f"登录参数获取成功（loginhash：{loginhash[:6]}***）"

    except requests.exceptions.RequestException as e:
        return None, None, f"获取登录参数网络异常：{str(e)}"
    except Exception as e:
        return None, None, f"获取登录参数逻辑异常：{str(e)}"


def get_sign_reward(formhash, username):
    """获取签到排名和金币奖励，并执行退出登录"""
    logs = []
    try:
        response = SESSION.get(
            url=f"{BASE_URL}/k_misign-sign.html",
            headers=REQUEST_HEADERS,
            timeout=15
        )
        response.raise_for_status()
        page_text = response.text

        rank_match = re.search(r'您的签到排名：(.*?)</div>', page_text)
        reward_match = re.search(r'id="lxreward" value="(.*?)"', page_text)

        rank = rank_match.group(1).strip() if rank_match else "未知"
        reward = reward_match.group(1).strip() if reward_match else "0"
        logs.append(f"签到排名：{rank}，奖励金币：{reward}")

        # 退出登录
        logout_url = f"{BASE_URL}/member.php?mod=logging&action=logout&formhash={formhash}"
        SESSION.get(url=logout_url, headers=REQUEST_HEADERS, timeout=10)
        logs.append("已退出当前账号")

    except requests.exceptions.RequestException as e:
        logs.append(f"获取签到奖励网络异常：{str(e)}")
    except Exception as e:
        logs.append(f"获取签到奖励逻辑异常：{str(e)}")
    
    return logs


def single_account_sign(username, password):
    """单账号签到核心逻辑，返回(是否成功, 过程日志)"""
    process_logs = []
    process_logs.append(f"开始处理账号：{username[:4]}***")
    
    # 重置会话
    global SESSION
    SESSION = requests.session()
    SESSION.headers.update(REQUEST_HEADERS)

    try:
        # 1. 访问首页初始化会话
        SESSION.get(url=BASE_URL, timeout=10)
        process_logs.append("已初始化会话")

        # 2. 获取登录参数
        loginhash, formhash, log_msg = get_login_params()
        process_logs.append(log_msg)
        if not loginhash or not formhash:
            return False, process_logs

        # 3. 执行登录
        login_url = f"{BASE_URL}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1"
        login_data = {
            "formhash": formhash,
            "referer": f"{BASE_URL}/forum.php",
            "loginfield": "username",
            "username": username,
            "password": password,
            "questionid": "0",
            "answer": ""
        }

        login_response = SESSION.post(
            url=login_url,
            data=login_data,
            headers=REQUEST_HEADERS,
            timeout=15
        )
        login_response.raise_for_status()
        login_text = login_response.text

        # 4. 验证登录结果
        if "欢迎您回来" in login_text or "登录成功" in login_text:
            user_match = re.search(r'欢迎您回来，(.*?)，现在', login_text)
            user_name = user_match.group(1).strip() if user_match else username
            process_logs.append(f"{user_name}：登录成功")

            # 5. 获取签到formhash
            sign_page = SESSION.get(
                url=f"{BASE_URL}/k_misign-sign.html",
                headers=REQUEST_HEADERS,
                timeout=15
            )
            sign_formhash_match = re.search(r'formhash" value="([^"]+)"', sign_page.text)
            if not sign_formhash_match:
                process_logs.append("未匹配到签到formhash")
                return False, process_logs
            sign_formhash = sign_formhash_match.group(1)

            # 6. 执行签到
            sign_url = f"{BASE_URL}/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={sign_formhash}"
            sign_response = SESSION.get(
                url=sign_url,
                headers=REQUEST_HEADERS,
                timeout=15
            )
            sign_response.raise_for_status()
            sign_result = sign_response.text.strip()

            # 7. 解析签到结果
            status_match = re.search(r'<root><(.*?)</root>', sign_result)
            sign_status = status_match.group(1).strip() if status_match else sign_result[:50]
            process_logs.append(f"签到状态：{sign_status}")

            # 8. 获取奖励
            if "成功" in sign_status or "已签" in sign_status:
                reward_logs = get_sign_reward(sign_formhash, username)
                process_logs.extend(reward_logs)
            return True, process_logs

        else:
            error_match = re.search(r"CDATA\[(.*?)\]", login_text)
            error_msg = error_match.group(1).strip() if error_match else "未知原因"
            process_logs.append(f"登录失败 - {error_msg}")
            return False, process_logs

    except requests.exceptions.RequestException as e:
        process_logs.append(f"签到网络异常：{str(e)}")
    except Exception as e:
        process_logs.append(f"签到逻辑异常：{str(e)}")
    return False, process_logs


# ---------------- 主执行入口 ----------------
if __name__ == "__main__":
    myprint("============📣 MT论坛签到任务启动 📣============")
    myprint(f"⏰ 启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    myprint(f"🔧 配置：最大重试{MAX_RETRY}次/账号，每个账号单独发送详细通知")
    myprint("=" * 45)

    # 1. 读取环境变量中的账号
    mt_accounts_env = os.environ.get("mtluntan", "")
    if not mt_accounts_env:
        error_msg = "未配置mtluntan环境变量！\n配置示例：export mtluntan='账号1&密码1@账号2&密码2'"
        myprint(f"❌ {error_msg}")
        send_system_notification(error_msg)
        myprint("============📣 签到任务结束 📣============")
        exit()

    # 2. 解析多账号（按@分割）
    accounts_list = [acc.strip() for acc in mt_accounts_env.split("@") if acc.strip()]
    myprint(f"📌 查找到{len(accounts_list)}个有效账号")
    myprint("=" * 45)

    # 3. 批量处理每个账号（带重试）
    for idx, account in enumerate(accounts_list, 1):
        if "&" not in account:
            error_msg = f"账号{idx}格式错误：缺少'&'分隔符（正确格式：账号&密码）"
            myprint(f"❌ {error_msg}")
            send_system_notification(error_msg)
            myprint("-" * 40)
            continue

        # 分割账号和密码
        username, password = account.split("&", 1)
        username = username.strip()
        password = password.strip()

        myprint(f"📥 开始处理账号{idx}：{username[:4]}***")
        retry_count = 0
        sign_success = False
        final_logs = []

        # 重试逻辑
        while retry_count < MAX_RETRY and not sign_success:
            retry_count += 1
            if retry_count > 1:
                current_log = f"第{retry_count}次重试（账号{idx}）"
                myprint(current_log)
                final_logs.append(current_log)
            
            sign_success, process_logs = single_account_sign(username, password)
            final_logs.extend(process_logs)
            
            # 重试间隔
            if not sign_success and retry_count < MAX_RETRY:
                time.sleep(2)

        # 输出结果并发送通知
        if sign_success:
            final_logs.append(f"账号{idx}处理完成")
            myprint(f"✅ 账号{idx}处理完成")
        else:
            final_logs.append(f"账号{idx}处理失败（已重试{MAX_RETRY}次）")
            myprint(f"❌ 账号{idx}处理失败（已重试{MAX_RETRY}次）")
        
        # 发送该账号的详细通知
        send_account_notification(username, final_logs, sign_success)
        myprint("-" * 40)

    myprint("============📣 签到任务全部结束 📣============")

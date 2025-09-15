"""
MT论坛自动签到（通知美化版）
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
# 日志收集列表（用于组装通知内容）
all_print_list = []
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
    """自定义打印：同时输出到控制台和日志列表"""
    print(msg)
    all_print_list.append(str(msg))


def format_notify_content():
    """格式化通知内容：结构化排版+emoji美化"""
    # 1. 提取统计数据（总账号数、成功数）
    total_accounts = 0
    success_accounts = 0
    for line in all_print_list:
        # 匹配账号总数
        if "查找到" in line and "个账号" in line:
            match = re.search(r"查找到(\d+)个账号", line)
            total_accounts = int(match.group(1)) if match else 0
        # 匹配成功标识
        elif "登录成功" in line or "处理完成" in line:
            success_accounts += 1

    # 2. 构建通知结构
    notify_title = "🌟 MT论坛签到结果通知"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = [
        f"【{notify_title}】",
        f"📅 执行时间：{current_time}",
        "=" * 45,
        "📊 签到汇总统计",
        f"   • 总账号数：{total_accounts} 个",
        f"   • 成功数：{success_accounts} 个",
        f"   • 失败数：{total_accounts - success_accounts} 个",
        f"   • 成功率：{success_accounts/total_accounts*100:.1f}%" if total_accounts > 0 else "   • 成功率：0.0%",
        "=" * 45,
        "📝 详细签到记录"
    ]

    # 3. 筛选并美化详细日志（跳过初始化内容，保留核心流程）
    log_filter_flag = False  # 标记从"查找到账号"开始记录
    for line in all_print_list:
        if "查找到" in line and "个账号" in line:
            log_filter_flag = True
            content.append(f"   {line}")
            continue
        
        if log_filter_flag:
            # 关键状态添加emoji标识
            if "登录成功" in line:
                content.append(f"✅ {line}")
            elif "签到状态" in line:
                content.append(f"📅 {line}")
            elif "签到排名" in line:
                content.append(f"🏆 {line}")
            elif "处理完成" in line:
                content.append(f"✅ {line}")
            elif "处理失败" in line or "登录失败" in line:
                content.append(f"❌ {line}")
            elif "重试" in line:
                content.append(f"🔄 {line}")
            elif "结束" in line and "====" in line:
                content.append("-" * 40)
            else:
                content.append(f"   {line}")  # 普通内容缩进

    # 4. 尾部提示信息
    content.extend([
        "=" * 45,
        "💡 失败排查建议：",
        "   1. 检查账号密码是否正确",
        "   2. 确认Cookie是否过期（若用Cookie登录）",
        "   3. 检查网络是否能访问论坛",
        f"🔗 论坛地址：{BASE_URL}"
    ])

    return notify_title, "\n".join(content)


def send_notification():
    """发送美化后的通知（依赖同目录sendNotify.py）"""
    myprint("\n" + "=" * 45)
    myprint("📤 开始发送签到通知...")
    try:
        from sendNotify import send
        notify_title, notify_content = format_notify_content()
        send(notify_title, notify_content)
        myprint("✅ 通知发送成功！")
    except ImportError:
        myprint("⚠️  未找到sendNotify.py文件，无法发送通知")
    except Exception as e:
        myprint(f"❌ 通知发送失败：{str(e)}")


def get_login_params():
    """获取登录所需的loginhash和formhash（防索引越界）"""
    login_page_url = f"{BASE_URL}/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login"
    try:
        response = SESSION.get(
            url=login_page_url,
            headers=REQUEST_HEADERS,
            timeout=15
        )
        response.raise_for_status()  # 触发HTTP错误（如404、500）

        # 正则匹配（兼容多种页面格式）
        loginhash_match = re.search(r'loginhash=([a-zA-Z0-9]+)', response.text)
        formhash_match = re.search(r'formhash" value="([^"]+)"', response.text)

        if not loginhash_match or not formhash_match:
            myprint("❌ 未匹配到loginhash或formhash（页面结构可能变更）")
            return None, None

        loginhash = loginhash_match.group(1)
        formhash = formhash_match.group(1)
        myprint(f"🔍 登录参数获取成功（loginhash：{loginhash[:6]}***）")
        return loginhash, formhash

    except requests.exceptions.RequestException as e:
        myprint(f"❌ 获取登录参数网络异常：{str(e)}")
    except Exception as e:
        myprint(f"❌ 获取登录参数逻辑异常：{str(e)}")
    return None, None


def get_sign_reward(formhash):
    """获取签到排名和金币奖励，并执行退出登录"""
    try:
        # 获取签到后页面数据
        response = SESSION.get(
            url=f"{BASE_URL}/k_misign-sign.html",
            headers=REQUEST_HEADERS,
            timeout=15
        )
        response.raise_for_status()
        page_text = response.text

        # 匹配排名和金币
        rank_match = re.search(r'您的签到排名：(.*?)</div>', page_text)
        reward_match = re.search(r'id="lxreward" value="(.*?)"', page_text)

        rank = rank_match.group(1).strip() if rank_match else "未知"
        reward = reward_match.group(1).strip() if reward_match else "0"
        myprint(f"🏆 签到排名：{rank}，奖励金币：{reward}")

        # 退出登录（多账号防cookie冲突）
        logout_url = f"{BASE_URL}/member.php?mod=logging&action=logout&formhash={formhash}"
        SESSION.get(url=logout_url, headers=REQUEST_HEADERS, timeout=10)
        myprint("🔚 已退出当前账号")

    except requests.exceptions.RequestException as e:
        myprint(f"❌ 获取签到奖励网络异常：{str(e)}")
    except Exception as e:
        myprint(f"❌ 获取签到奖励逻辑异常：{str(e)}")


def single_account_sign(username, password):
    """单账号签到核心逻辑"""
    # 重置会话（避免残留cookie）
    global SESSION
    SESSION = requests.session()
    SESSION.headers.update(REQUEST_HEADERS)

    try:
        # 1. 访问首页初始化会话
        SESSION.get(url=BASE_URL, timeout=10)
        myprint(f"🌐 已初始化会话（账号：{username[:4]}***）")

        # 2. 获取登录参数
        loginhash, formhash = get_login_params()
        if not loginhash or not formhash:
            return False

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
            # 提取用户名（兼容不同页面显示）
            user_match = re.search(r'欢迎您回来，(.*?)，现在', login_text)
            user_name = user_match.group(1).strip() if user_match else username
            myprint(f"✅ {user_name}：登录成功")

            # 5. 获取签到formhash
            sign_page = SESSION.get(
                url=f"{BASE_URL}/k_misign-sign.html",
                headers=REQUEST_HEADERS,
                timeout=15
            )
            sign_formhash_match = re.search(r'formhash" value="([^"]+)"', sign_page.text)
            if not sign_formhash_match:
                myprint("❌ 未匹配到签到formhash")
                return False
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
            myprint(f"📅 签到状态：{sign_status}")

            # 8. 若签到成功/已签到，获取奖励
            if "成功" in sign_status or "已签" in sign_status:
                get_sign_reward(sign_formhash)
            return True

        else:
            # 提取登录失败原因
            error_match = re.search(r"CDATA\[(.*?)\]", login_text)
            error_msg = error_match.group(1).strip() if error_match else "未知原因"
            myprint(f"❌ {username[:4]}***：登录失败 - {error_msg}")
            return False

    except requests.exceptions.RequestException as e:
        myprint(f"❌ 签到网络异常：{str(e)}")
    except Exception as e:
        myprint(f"❌ 签到逻辑异常：{str(e)}")
    return False


# ---------------- 主执行入口 ----------------
if __name__ == "__main__":
    myprint("============📣 MT论坛签到任务启动 📣============")
    myprint(f"⏰ 启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    myprint(f"🔧 配置：最大重试{MAX_RETRY}次/账号，通知自动美化")
    myprint("=" * 45)

    # 1. 读取环境变量中的账号
    mt_accounts_env = os.environ.get("mtluntan", "")
    if not mt_accounts_env:
        myprint("❌ 未配置mtluntan环境变量！")
        myprint("💡 配置示例：export mtluntan='账号1&密码1@账号2&密码2'")
        send_notification()  # 即使无账号也发送通知提示配置
        myprint("============📣 签到任务结束 📣============")
        exit()

    # 2. 解析多账号（按@分割）
    accounts_list = [acc.strip() for acc in mt_accounts_env.split("@") if acc.strip()]
    myprint(f"📌 查找到{len(accounts_list)}个有效账号")
    myprint("=" * 45)

    # 3. 批量处理每个账号（带重试）
    for idx, account in enumerate(accounts_list, 1):
        if "&" not in account:
            myprint(f"❌ 账号{idx}格式错误：缺少'&'分隔符（正确格式：账号&密码）")
            myprint("-" * 40)
            continue

        # 分割账号和密码（只分割第一个&，避免密码含&）
        username, password = account.split("&", 1)
        username = username.strip()
        password = password.strip()

        myprint(f"📥 开始处理账号{idx}：{username[:4]}***")
        retry_count = 0
        sign_success = False

        # 重试逻辑
        while retry_count < MAX_RETRY and not sign_success:
            retry_count += 1
            if retry_count > 1:
                myprint(f"🔄 第{retry_count}次重试（账号{idx}）")
            
            sign_success = single_account_sign(username, password)
            # 重试间隔（避免高频请求）
            if not sign_success and retry_count < MAX_RETRY:
                time.sleep(2)

        # 输出账号处理结果
        if sign_success:
            myprint(f"✅ 账号{idx}处理完成")
        else:
            myprint(f"❌ 账号{idx}处理失败（已重试{MAX_RETRY}次）")
        myprint("-" * 40)

    # 4. 发送最终通知
    send_notification()
    myprint("============📣 签到任务全部结束 📣============")
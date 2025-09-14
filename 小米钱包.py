# 百度搜索小米账号，抓包即可
#'''
#格式为passToken&userId
#在浏览器输入https://account.xiaomi.com/登入
#推荐用via浏览器，我示范via
#1.登入后看到上面小米账号左边有安全符号点一下
#2.点Cookies就可以看到了
#3.找到passToken————userId——后面符号不要
#export xmqb = "passToken1&userId1@passToken2&userId2"
#'''

import os
import time
import requests
import urllib3
import re
from datetime import datetime
from typing import Optional, Dict, Any, Union
try:
    from notify import send
    hadsend = True
    print("✅ 已加载notify.py通知模块")
except ImportError:
    hadsend = False
    print("⚠️  未加载通知模块，跳过通知功能")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置项
privacy_mode = os.getenv("PRIVACY_MODE", "true").lower() == "true"

class RnlRequest:
    def __init__(self, cookies: Union[str, dict]):
        self.session = requests.Session()
        self._base_headers = {
            'Host': 'm.jr.airstarfinance.net',
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-CN; M2012K11AC Build/UKQ1.230804.001; AppBundle/com.mipay.wallet; AppVersionName/6.89.1.5275.2323; AppVersionCode/20577595; MiuiVersion/stable-V816.0.13.0.UMNCNXM; DeviceId/alioth; NetworkType/WIFI; mix_version; WebViewVersion/118.0.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3',
        }
        self.update_cookies(cookies)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,** kwargs
    ) -> Optional[Dict[str, Any]]:
        headers = {**self._base_headers, **kwargs.pop('headers', {})}
        try:
            resp = self.session.request(
                verify=False,
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,** kwargs
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[Request Error] {e}")
            return None
        except ValueError as e:
            print(f"[JSON Parse Error] {e}")
            return None

    def update_cookies(self, cookies: Union[str, dict]) -> None:
        if cookies:
            if isinstance(cookies, str):
                dict_cookies = self._parse_cookies(cookies)
            else:
                dict_cookies = cookies
            self.session.cookies.update(dict_cookies)
            self._base_headers['Cookie'] = self.dict_cookie_to_string(dict_cookies)

    @staticmethod
    def _parse_cookies(cookies_str: str) -> Dict[str, str]:
        return dict(
            item.strip().split('=', 1)
            for item in cookies_str.split(';')
            if '=' in item
        )

    @staticmethod
    def dict_cookie_to_string(cookie_dict):
        cookie_list = []
        for key, value in cookie_dict.items():
            cookie_list.append(f"{key}={value}")
        return "; ".join(cookie_list)

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('GET', url, params=params,** kwargs)

    def post(self, url: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
             json: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('POST', url, data=data, json=json,** kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


class RNL:
    def __init__(self, c):
        self.t_id = None
        self.options = {
            "task_list": True,
            "complete_task": True,
            "receive_award": True,
            "task_item": True,
            "UserJoin": True,
        }
        self.activity_code = '2211-videoWelfare'
        self.rr = RnlRequest(c)
        self.current_user_id = None  # 存储当前处理的用户ID
        self.total_days = "未知"
        self.today_records = []
        self.error_info = ""
        self.success = True  # 任务执行状态

    def get_task_list(self):
        data = {
            'activityCode': self.activity_code,
        }
        try:
            response = self.rr.post(
                'https://m.jr.airstarfinance.net/mp/api/generalActivity/getTaskList',
                data=data,
            )
            if response and response['code'] != 0:
                self.error_info = f"获取任务列表失败：{response.get('message', '未知错误')}"
                self.success = False
                print(self.error_info)
                return None
            target_tasks = []
            for task in response['value']['taskInfoList']:
                if '浏览组浏览任务' in task['taskName']:
                    target_tasks.append(task)
            return target_tasks
        except Exception as e:
            self.error_info = f'获取任务列表失败：{e}'
            self.success = False
            print(self.error_info)
            return None

    def get_task(self, task_code):
        try:
            data = {
                'activityCode': self.activity_code,
                'taskCode': task_code,
                'jrairstar_ph': '98lj8puDf9Tu/WwcyMpVyQ==',
            }
            response = self.rr.post(
                'https://m.jr.airstarfinance.net/mp/api/generalActivity/getTask',
                data=data,
            )
            if response and response['code'] != 0:
                self.error_info = f'获取任务信息失败：{response.get("message", "未知错误")}'
                self.success = False
                print(self.error_info)
                return None
            return response['value']['taskInfo']['userTaskId']
        except Exception as e:
            self.error_info = f'获取任务信息失败：{e}'
            self.success = False
            print(self.error_info)
            return None

    def complete_task(self, task_id, t_id, brows_click_urlId):
        try:
            response = self.rr.get(
                f'https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask?activityCode={self.activity_code}&app=com.mipay.wallet&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D&taskId={task_id}&browsTaskId={t_id}&browsClickUrlId={brows_click_urlId}&clickEntryType=undefined&festivalStatus=0',
            )
            if response and response['code'] != 0:
                self.error_info = f'完成任务失败：{response.get("message", "未知错误")}'
                self.success = False
                print(self.error_info)
                return None
            return response['value']
        except Exception as e:
            self.error_info = f'完成任务失败：{e}'
            self.success = False
            print(self.error_info)
            return None

    def receive_award(self, user_task_id):
        try:
            response = self.rr.get(
                f'https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw?imei=&device=manet&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:true,%22com.tencent.qqlive%22:true,%22com.hunantv.imgo.activity%22:true,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:true,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:true,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:true,%22com.kuaishou.nebula%22:false%7D&activityCode={self.activity_code}&userTaskId={user_task_id}&app=com.mipay.wallet&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D'
            )
            if response and response['code'] != 0:
                self.error_info = f'领取奖励失败：{response.get("message", "未知错误")}'
                self.success = False
                print(self.error_info)
        except Exception as e:
            self.error_info = f'领取奖励失败：{e}'
            self.success = False
            print(self.error_info)

    def queryUserJoinListAndQueryUserGoldRichSum(self):
        try:
            total_res = self.rr.get('https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserGoldRichSum?app=com.mipay.wallet&deviceType=2&system=1&visitEnvironment=2&userExtra={"platformType":1,"com.miui.player":"4.27.0.4","com.miui.video":"v2024090290(MiVideo-UN)","com.mipay.wallet":"6.83.0.5175.2256"}&activityCode=2211-videoWelfare')
            if not total_res or total_res['code'] != 0:
                self.error_info = f'获取兑换视频天数失败：{total_res.get("message", "未知错误") if total_res else "无响应"}'
                self.success = False
                print(self.error_info)
                return False
            self.total_days = f"{int(total_res['value']) / 100:.2f}天" if total_res else "未知"

            response = self.rr.get(
                f'https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserJoinList?&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D&activityCode={self.activity_code}&pageNum=1&pageSize=20',
            )
            if not response or response['code'] != 0:
                self.error_info = f'查询任务完成记录失败：{response.get("message", "未知错误") if response else "无响应"}'
                self.success = False
                print(self.error_info)
                return False

            history_list = response['value']['data']
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 清空记录
            self.today_records = []
            
            for a in history_list:
                record_time = a['createTime']
                record_date = record_time[:10]
                if record_date == current_date:
                    self.today_records.append({
                        'createTime': record_time,
                        'value': a['value']
                    })
            
            return True
        except Exception as e:
            self.error_info = f'获取任务记录失败：{e}'
            self.success = False
            print(self.error_info)
            return False

    def main(self):
        if not self.queryUserJoinListAndQueryUserGoldRichSum():
            return False
        for i in range(2):
            # 获取任务列表
            tasks = self.get_task_list()
            if not tasks:
                return False
                
            task = tasks[0]
            try:
                t_id = task['generalActivityUrlInfo']['id']
                self.t_id = t_id
            except:
                t_id = self.t_id
            task_id = task['taskId']
            task_code = task['taskCode']
            brows_click_url_id = task['generalActivityUrlInfo']['browsClickUrlId']

            time.sleep(13)

            # 完成任务
            user_task_id = self.complete_task(
                t_id=t_id,
                task_id=task_id,
                brows_click_urlId=brows_click_url_id,
            )

            time.sleep(2)

            # 获取任务数据
            if not user_task_id:
                user_task_id = self.get_task(task_code=task_code)
                time.sleep(2)

            # 领取奖励
            self.receive_award(
                user_task_id=user_task_id
            )

            time.sleep(2)
        
        # 重新获取最新记录
        self.queryUserJoinListAndQueryUserGoldRichSum()
        return True


def get_xiaomi_cookies(pass_token, user_id):
    session = requests.Session()
    login_url = 'https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Fapi.jr.airstarfinance.net%2Fsts%3Fsign%3D1dbHuyAmee0NAZ2xsRw5vhdVQQ8%253D%26followup%3Dhttps%253A%252F%252Fm.jr.airstarfinance.net%252Fmp%252Fapi%252Flogin%253Ffrom%253Dmipay_indexicon_TVcard%2526deepLinkEnable%253Dfalse%2526requestUrl%253Dhttps%25253A%25252F%25252Fm.jr.airstarfinance.net%25252Fmp%25252Factivity%25252FvideoActivity%25253Ffrom%25253Dmipay_indexicon_TVcard%252526_noDarkMode%25253Dtrue%252526_transparentNaviBar%25253Dtrue%252526cUserId%25253Dusyxgr5xjumiQLUoAKTOgvi858Q%252526_statusBarHeight%25253D137&sid=jrairstar&_group=DEFAULT&_snsNone=true&_loginType=ticket'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        'cookie': f'passToken={pass_token}; userId={user_id};'
    }

    try:
        session.get(url=login_url, headers=headers, verify=False)
        cookies = session.cookies.get_dict()
        return f"cUserId={cookies.get('cUserId')};jrairstar_serviceToken={cookies.get('serviceToken')}"
    except Exception as e:
        error_msg = f"获取Cookie失败: {e}"
        print(error_msg)
        return None, error_msg


def mask_user_id(user_id):
    """用户ID脱敏处理"""
    if not user_id or not privacy_mode:
        return user_id
    
    # 提取数字部分进行脱敏
    numbers = re.sub(r'\D', '', user_id)
    if len(numbers) <= 4:
        return '*' * len(numbers)
    elif len(numbers) <= 6:
        return numbers[:2] + '*' * (len(numbers) - 4) + numbers[-2:]
    else:
        return numbers[:3] + '*' * 4 + numbers[-3:]


def notify_user(title, content):
    """统一通知函数"""
    if hadsend:
        try:
            send(title, content)
            print(f"✅ 通知发送完成: {title}")
        except Exception as e:
            print(f"❌ 通知发送失败: {e}")
    else:
        print(f"📢 {title}\n📄 {content}")


def generate_notification(account_id, rnl_instance):
    """生成格式化的通知消息"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    masked_id = mask_user_id(account_id)
    
    # 计算今日总收益
    total_today = sum(int(record["value"]) for record in rnl_instance.today_records) / 100
    
    msg = f"""🌟 小米钱包任务结果

👤 用户ID: {masked_id}
📊 当前总天数: {rnl_instance.total_days}
🎁 今日收益: +{total_today:.2f}天

📅 {current_date} 任务记录"""
    
    if rnl_instance.today_records:
        for i, record in enumerate(rnl_instance.today_records, 1):
            record_time = record["createTime"][11:16]  # 只显示时分
            days = int(record["value"]) / 100
            msg += f"\n{i}. ⏰ {record_time} - +{days:.2f}天"
    else:
        msg += "\n⚠️ 未获取到今日任务记录"
    
    if rnl_instance.error_info:
        msg += f"\n\n❌ 错误信息: {rnl_instance.error_info}"
    
    msg += f"\n\n⏰ 完成时间: {datetime.now().strftime('%m-%d %H:%M')}"
    
    return msg


if __name__ == "__main__":
    print(f"==== 小米钱包任务开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
    print(f"🔒 隐私保护模式: {'已启用' if privacy_mode else '已禁用'}")
    
    # 从环境变量中读取小米账号信息
    raw_cookies = os.getenv("XIAOMI_COOKIES") or os.getenv("xmqb")  # 兼容原变量名
    
    if not raw_cookies:
        error_msg = """❌ 未找到小米账号配置
        
🔧 配置方法:
1. 环境变量: XIAOMI_COOKIES 或 xmqb
2. 格式: passToken1&userId1@passToken2&userId2
3. 多账号用@分隔

💡 提示: 请按照说明正确配置账号信息"""
        
        print(error_msg)
        notify_user("小米钱包任务失败", error_msg)
        exit(1)

    # 解析为列表字典结构
    ORIGINAL_COOKIES = []
    for item in raw_cookies.split('@'):
        if '&' in item:
            pass_token, user_id = item.split('&', 1)
            ORIGINAL_COOKIES.append({
                'passToken': pass_token.strip(),
                'userId': user_id.strip()
            })
        else:
            print(f"⚠️ 忽略无效格式: {item}")

    # 打印加载结果
    print(f"✅ 加载账号信息成功，共加载 {len(ORIGINAL_COOKIES)} 个账号")

    success_count = 0
    total_count = len(ORIGINAL_COOKIES)
    results = []

    for index, account in enumerate(ORIGINAL_COOKIES, 1):
        user_id = account['userId']
        print(f"\n==== 正在处理账号 {index}/{total_count} ====")
        
        # 账号间随机等待
        if index > 1:
            delay = random.uniform(5, 15)
            print(f"⏱️  随机等待 {delay:.1f} 秒后处理下一个账号...")
            time.sleep(delay)
        
        # 获取Cookie - 兼容原函数返回值
        cookie_result = get_xiaomi_cookies(account['passToken'], user_id)
        
        # 处理返回结果
        if isinstance(cookie_result, tuple):
            new_cookie, error = cookie_result
        else:
            new_cookie = cookie_result
            error = None
        
        # 创建RNL实例并设置当前用户ID
        rnl = RNL(new_cookie)
        rnl.current_user_id = user_id
        
        if error:
            rnl.error_info = error
            rnl.success = False
        else:
            print(f"账号 {mask_user_id(user_id)} Cookie获取成功")
            
            # 执行主程序
            try:
                rnl.main()
            except Exception as e:
                rnl.error_info = f"执行异常: {str(e)}"
                rnl.success = False
                print(rnl.error_info)
        
        if rnl.success:
            success_count += 1
        
        # 记录结果
        results.append({
            'index': index,
            'success': rnl.success,
            'user_id': user_id,
            'masked_id': mask_user_id(user_id)
        })
        
        # 生成当前账号的通知消息并发送
        account_notification = generate_notification(user_id, rnl)
        status = "成功" if rnl.success else "失败"
        notify_user(f"小米钱包账号{index}任务{status}", account_notification)

    # 发送汇总通知
    if total_count > 1:
        summary_msg = f"""📊 小米钱包任务汇总

📈 总计: {total_count}个账号
✅ 成功: {success_count}个
❌ 失败: {total_count - success_count}个
📊 成功率: {success_count/total_count*100:.1f}%
⏰ 完成时间: {datetime.now().strftime('%m-%d %H:%M')}"""
        
        # 添加详细结果
        summary_msg += "\n\n📋 账号状态:"
        for result in results:
            status_icon = "✅" if result['success'] else "❌"
            summary_msg += f"\n{status_icon} 账号{result['index']}: {result['masked_id']}"
        
        notify_user("小米钱包任务汇总", summary_msg)
    
    print(f"\n==== 小米钱包任务完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

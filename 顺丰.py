# cron: 10 12 * * *
# const $ = new Env('顺丰速运')

# 变量名：sfsyUrl
# 格式：多账号用换行分割或创建多个变量sfsyUrl
# 关于参数获取如下两种方式：
# ❶顺丰APP绑定微信后，前往该站点sm.linzixuan.work用微信扫码登录后，选择复制编码Token，不要复制错
# 或者
# ❷打开小程序或APP-我的-积分, 手动抓包以下几种URL之一
# https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect
# https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect
# 抓好URL后访问https://www.toolhelper.cn/EncodeDecode/Url进行编码，请务必按提示操作
import hashlib
import json
import os
import random
import time
import re
from datetime import datetime, timedelta
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import unquote

# ==================== 推送配置 ====================
# 依赖青龙自带的notify.py
PUSH_SWITCH = "1"                # 推送开关，1开启，0关闭
# =======================================================

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 代理相关配置
PROXY_API_URL = os.getenv('SF_PROXY_API_URL', '')  # 从环境变量获取代理API地址

# 导入青龙自带的notify模块
try:
    from notify import send as notify_send
    print("✅ 成功加载青龙notify推送模块")
except ImportError:
    print("❌ 未找到notify模块，无法发送推送")
    notify_send = None  # 避免后续调用报错

def get_proxy():
    """从代理API获取代理"""
    try:
        if not PROXY_API_URL:
            print('⚠️ 未配置代理API地址，将不使用代理')
            return None
            
        response = requests.get(PROXY_API_URL, timeout=10)
        if response.status_code == 200:
            proxy_text = response.text.strip()
            if ':' in proxy_text:
                proxy = f'http://{proxy_text}'
                return {
                    'http': proxy,
                    'https': proxy
                }
        print(f'❌ 获取代理失败: {response.text}')
        return None
    except Exception as e:
        print(f'❌ 获取代理异常: {str(e)}')
        return None

# 全局变量用于存储推送消息
push_messages = []
force_push = False
inviteId = []  # 修复未定义问题

def add_push_message(account_info, content):
    """添加账号推送消息"""
    message = f"{account_info}\n{content}"
    push_messages.append(message)

def add_error_message(error_info):
    """添加错误消息（强制推送）"""
    global force_push
    force_push = True
    push_messages.append(f"❌ {error_info}")

class RUN:
    def __init__(self, info, index):
        self.account_msg = f"👤 账号{index + 1}"  # 账号信息
        self.logs = []  # 存储当前账号的执行日志
        self.index = index + 1
        
        # 解析账号信息
        split_info = info.split('@')
        url = split_info[0]
        len_split_info = len(split_info)
        last_info = split_info[len_split_info - 1] if len_split_info > 0 else ""
        self.send_UID = last_info if "UID_" in last_info else None

        # 获取代理
        self.proxy = get_proxy()
        if self.proxy:
            self.log(f"✅ 成功获取代理: {self.proxy['http']}")
        
        self.s = requests.session()
        self.s.verify = False
        if self.proxy:
            self.s.proxies = self.proxy
            
        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh',
            'platform': 'MINI_PROGRAM',
        }
        
        # 活动相关属性初始化
        self.ifPassAllLevel = False
        self.surplusPushTime = 0
        self.lotteryNum = 0
        self.anniversary_black = False
        self.member_day_black = False
        self.member_day_red_packet_drew_today = False
        self.member_day_red_packet_map = {}
        self.max_level = 8
        self.packet_threshold = 1 << (self.max_level - 1)
        
        self.login_res = self.login(url)
        self.today = datetime.now().strftime('%Y-%m-%d')

    def log(self, content):
        """记录日志并暂存推送内容"""
        print(content)
        self.logs.append(content)

    def get_deviceId(self, characters='abcdef0123456789'):
        result = ''
        for char in 'xxxxxxxx-xxxx-xxxx':
            if char == 'x':
                result += random.choice(characters)
            elif char == 'X':
                result += random.choice(characters).upper()
            else:
                result += char
        return result

    def login(self, sfurl):
        try:
            decoded_url = unquote(sfurl)  # 解码一次即可（因sfsyUrl已编码）
            ress = self.s.get(decoded_url, headers=self.headers)
            self.user_id = self.s.cookies.get_dict().get('_login_user_id_', '')
            self.phone = self.s.cookies.get_dict().get('_login_mobile_', '')
            self.mobile = self.phone[:3] + "*" * 4 + self.phone[7:] if self.phone else ''
            
            if self.phone:
                self.account_msg = f"👤 账号{self.index}:【{self.mobile}】"
                self.log(f'{self.account_msg} 登陆成功')
                # 补充inviteId列表
                global inviteId
                if self.user_id and self.user_id not in inviteId:
                    inviteId.append(self.user_id)
                return True
            else:
                error_msg = f'账号{self.index}获取用户信息失败'
                self.log(f'❌ {error_msg}')
                add_error_message(error_msg)
                return False
        except Exception as e:
            error_msg = f'登录异常: {str(e)}'
            self.log(f'❌ {error_msg}')
            add_error_message(error_msg)
            return False

    def getSign(self):
        timestamp = str(int(round(time.time() * 1000)))
        token = 'wwesldfs29aniversaryvdld29'
        sysCode = 'MCS-MIMP-CORE'
        data = f'token={token}&timestamp={timestamp}&sysCode={sysCode}'
        signature = hashlib.md5(data.encode()).hexdigest()
        data = {
            'sysCode': sysCode,
            'timestamp': timestamp,
            'signature': signature
        }
        self.headers.update(data)
        return data

    def do_request(self, url, data={}, req_type='post', max_retries=3):
        self.getSign()
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if req_type.lower() == 'get':
                    response = self.s.get(url, headers=self.headers, timeout=30)
                elif req_type.lower() == 'post':
                    response = self.s.post(url, headers=self.headers, json=data, timeout=30)
                else:
                    raise ValueError('Invalid req_type: %s' % req_type)
                    
                response.raise_for_status()
                
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    print(f'JSON解析失败: {str(e)}, 响应内容: {response.text[:200]}')
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f'正在进行第{retry_count + 1}次重试...')
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f'请求失败，正在切换代理重试 ({retry_count}/{max_retries}): {str(e)}')
                    self.proxy = get_proxy()
                    if self.proxy:
                        print(f"✅ 成功获取新代理: {self.proxy['http']}")
                        self.s.proxies = self.proxy
                    time.sleep(2)
                else:
                    print('请求最终失败:', e)
                    return None
                
        return None

    def sign(self):
        self.log(f'🎯 开始执行签到')
        json_data = {"comeFrom": "vioin", "channelFrom": "WEIXIN"}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            count_day = response.get('obj', {}).get('countDay', 0)
            if response.get('obj') and response['obj'].get('integralTaskSignPackageVOList'):
                packet_name = response["obj"]["integralTaskSignPackageVOList"][0]["packetName"]
                self.log(f'✨ 签到成功，获得【{packet_name}】，本周累计签到【{count_day + 1}】天')
            else:
                self.log(f'📝 今日已签到，本周累计签到【{count_day + 1}】天')
        else:
            self.log(f'❌ 签到失败！原因：{response.get("errorMessage")}')

    def superWelfare_receiveRedPacket(self):
        self.log(f'🎁 超值福利签到')
        json_data = {
            'channel': 'czflqdlhbxcx'
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberActLengthy~redPacketActivityService~superWelfare~receiveRedPacket'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            gift_list = response.get('obj', {}).get('giftList', [])
            if response.get('obj', {}).get('extraGiftList', []):
                gift_list.extend(response['obj']['extraGiftList'])
            gift_names = ', '.join([gift['giftName'] for gift in gift_list])
            receive_status = response.get('obj', {}).get('receiveStatus')
            status_message = '领取成功' if receive_status == 1 else '已领取过'
            self.log(f'🎉 超值福利签到[{status_message}]: {gift_names}')
        else:
            error_message = response.get('errorMessage') or json.dumps(response) or '无返回'
            self.log(f'❌ 超值福利签到失败: {error_message}')

    def get_SignTaskList(self, END=False):
        if not END:
            self.log(f'🎯 开始获取签到任务列表')
        json_data = {
            'channelType': '1',
            'deviceId': self.get_deviceId(),
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True and response.get('obj') != []:
            totalPoint = response["obj"]["totalPoint"]
            if END:
                self.log(f'💰 当前积分：【{totalPoint}】')
                return
            self.log(f'💰 执行前积分：【{totalPoint}】')
            for task in response["obj"]["taskTitleLevels"]:
                self.taskId = task["taskId"]
                self.taskCode = task["taskCode"]
                self.strategyId = task["strategyId"]
                self.title = task["title"]
                status = task["status"]
                skip_title = ['用行业模板寄件下单', '去新增一个收件偏好', '参与积分活动']
                if status == 3:
                    self.log(f'✨ {self.title}-已完成')
                    continue
                if self.title in skip_title:
                    self.log(f'⏭️ {self.title}-跳过')
                    continue
                else:
                    self.doTask()
                    time.sleep(3)
                self.receiveTask()

    def doTask(self):
        self.log(f'🎯 开始去完成【{self.title}】任务')
        json_data = {
            'taskCode': self.taskCode,
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'✨ 【{self.title}】任务-已完成')
        else:
            self.log(f'❌ 【{self.title}】任务-{response.get("errorMessage")}')

    def receiveTask(self):
        self.log(f'🎁 开始领取【{self.title}】任务奖励')
        json_data = {
            "strategyId": self.strategyId,
            "taskId": self.taskId,
            "taskCode": self.taskCode,
            "deviceId": self.get_deviceId()
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'✨ 【{self.title}】任务奖励领取成功！')
        else:
            self.log(f'❌ 【{self.title}】任务-{response.get("errorMessage")}')

    # 采蜜任务相关
    def do_honeyTask(self):
        # 做任务
        json_data = {"taskCode": self.taskCode}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'>【{self.taskType}】任务-已完成')
        else:
            self.log(f'>【{self.taskType}】任务-{response.get("errorMessage")}')

    def receive_honeyTask(self):
        self.log('>>>执行收取丰蜜任务')
        # 收取
        self.headers['syscode'] = 'MCS-MIMP-CORE'
        self.headers['channel'] = 'wxwdsj'
        self.headers['accept'] = 'application/json, text/plain, */*'
        self.headers['content-type'] = 'application/json;charset=UTF-8'
        self.headers['platform'] = 'MINI_PROGRAM'
        json_data = {"taskType": self.taskType}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'收取任务【{self.taskType}】成功！')
        else:
            self.log(f'收取任务【{self.taskType}】失败！原因：{response.get("errorMessage")}')

    # 生活特权领券相关
    def get_coupom(self, goods):  
        # 请求参数
        json_data = {
            "from": "Point_Mall",
            "orderSource": "POINT_MALL_EXCHANGE",
            "goodsNo": goods['goodsNo'],
            "quantity": 1,
            "taskCode": self.taskCode
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder'
    
        # 发起领券请求
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'✨ 成功领取券：{goods["goodsName"]}')
            return True  # 领取成功
        else:
            self.log(f'📝 领取券【{goods["goodsName"]}】失败：{response.get("errorMessage")}')
            return False  # 领取失败
    
    def get_coupom_list(self):        
        # 请求参数
        json_data = {
            "memGrade": 2,
            "categoryCode": "SHTQ",
            "showCode": "SHTQWNTJ"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list'
    
        # 发起获取券列表请求
        response = self.do_request(url, data=json_data)
    
        if response.get('success') == True:
            # 遍历所有分组的券列表
            all_goods = []
            for obj in response.get("obj", []):  # 遍历所有券分组
                goods_list = obj.get("goodsList", [])
                all_goods.extend(goods_list)  # 收集到一个总列表中
               
            # 尝试领取
            for goods in all_goods:
                exchange_times_limit = goods.get('exchangeTimesLimit', 0)
    
                # 检查券是否可兑换
                if exchange_times_limit >= 1:
                    # 尝试领取券
                    if self.get_coupom(goods):
                        return  # 成功领取后退出
            self.log('📝 所有券尝试完成，没有可用的券或全部领取失败。')
        else:
            self.log(f'> 获取券列表失败！原因：{response.get("errorMessage")}')

    def get_honeyTaskListStart(self):
        self.log('🍯 开始获取采蜜换大礼任务列表')
        # 任务列表
        json_data = {}
        self.headers['channel'] = 'wxwdsj'
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail'

        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            for item in response["obj"]["list"]:
                self.taskType = item["taskType"]
                status = item["status"]
                if status == 3:
                    self.log(f'✨ 【{self.taskType}】-已完成')
                    continue
                if "taskCode" in item:
                    self.taskCode = item["taskCode"]
                    if self.taskType == 'DAILY_VIP_TASK_TYPE':
                        self.get_coupom_list()
                    else:
                        self.do_honeyTask()
                if self.taskType == 'BEES_GAME_TASK_TYPE':
                    self.honey_damaoxian()
                time.sleep(2)

    def honey_damaoxian(self):
        self.log('>>>执行大冒险任务')
        gameNum = 5
        for i in range(1, gameNum):
            json_data = {
                'gatherHoney': 20,
            }
            if gameNum < 0: break
            self.log(f'>>开始第{i}次大冒险')
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport'
            response = self.do_request(url, data=json_data)
            stu = response.get('success')
            if stu:
                gameNum = response.get('obj')['gameNum']
                self.log(f'>大冒险成功！剩余次数【{gameNum}】')
                time.sleep(2)
                gameNum -= 1
            elif response.get("errorMessage") == '容量不足':
                self.log(f'> 需要扩容')
                self.honey_expand()
            else:
                self.log(f'>大冒险失败！【{response.get("errorMessage")}】')
                break

    def honey_expand(self):
        self.log('>>>容器扩容')
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~expand'
        response = self.do_request(url, data={})
        stu = response.get('success', False)
        if stu:
            obj = response.get('obj')
            self.log(f'>成功扩容【{obj}】容量')
        else:
            self.log(f'>扩容失败！【{response.get("errorMessage")}】')

    def honey_indexData(self, END=False):
        if not END:
            self.log('--------------------------------\n🍯 开始执行采蜜换大礼任务')
        # 邀请
        global inviteId
        if len(inviteId) == 0 or (len(inviteId) == 1 and inviteId[0] == self.user_id):
            random_invite = self.user_id if self.user_id else ''
        else:
            random_invite = random.choice([invite for invite in inviteId if invite != self.user_id])
            
        self.headers['channel'] = 'wxwdsj'
        json_data = {"inviteUserId": random_invite}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            usableHoney = response.get('obj').get('usableHoney')
            activityEndTime = response.get('obj').get('activityEndTime', '')
            if activityEndTime:
                try:
                    activity_end_time = datetime.strptime(activityEndTime, "%Y-%m-%d %H:%M:%S")
                    self.log(f'📅 本期活动结束时间【{activityEndTime}】')
                except:
                    pass
                    
            if not END:
                self.log(f'🍯 执行前丰蜜：【{usableHoney}】')
                taskDetail = response.get('obj').get('taskDetail')
                if taskDetail:
                    for task in taskDetail:
                        self.taskType = task.get('type')
                        self.receive_honeyTask()
                        time.sleep(2)
            else:
                self.log(f'🍯 执行后丰蜜：【{usableHoney}】')
                return

    # 32周年活动相关
    def activityTaskService_taskList(self):
        self.log('🎭 开始32周年活动任务')
        json_data = {
            "activityCode": "DRAGONBOAT_2025",
            "channelType": "MINI_PROGRAM"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            # 需要过滤的任务类型
            skip_task_types = [
                'PLAY_ACTIVITY_GAME',      # 玩一笔连粽游戏
                'SEND_SUCCESS_RECALL',     # 去寄快递
                'OPEN_SUPER_CARD',         # 开通至尊会员
                'CHARGE_NEW_EXPRESS_CARD', # 充值新速运通全国卡
                'OPEN_NEW_EXPRESS_CARD',   # 开通新速运通
                'OPEN_FAMILY_CARD',        # 开通亲情卡
                'INTEGRAL_EXCHANGE'        # 积分兑换
            ]
            
            task_list = response.get('obj', [])
            # 过滤掉已完成的和不支持的任务类型
            task_list = [x for x in task_list if x.get('status') == 2 and x.get('taskType') not in skip_task_types]
            
            if not task_list:
                self.log('没有可执行的任务')
                return
                
            self.log(f'📝 获取到未完成任务: {len(task_list)}个')
            for task in task_list:
                self.log(f'📝 开始任务: {task.get("taskName")} [{task.get("taskType")}]')
                await_time = random.randint(1500, 3000) / 1000.0
                time.sleep(await_time)
                self.activityTaskService_finishTask(task)
                time.sleep(1.5)
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'获取活动任务失败: {error_msg}')
            if isinstance(response.get("obj"), dict):
                self.log(f'错误详情: {json.dumps(response.get("obj"), ensure_ascii=False)}')

    def activityTaskService_finishTask(self, task):
        json_data = {
            "taskCode": task.get('taskCode')
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            result_obj = response.get("obj", "")
            self.log(f'📝 完成任务[{task.get("taskName")}]: {result_obj}')
        else:
            error_code = response.get("errorCode", "未知错误码")
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 完成任务[{task.get("taskName")}]失败: {error_code} - {error_msg}')

    def dragonBoatGame2025ServiceWin(self, levelIndex):
        json_data = {"levelIndex": levelIndex}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoatGame2025Service~win'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'🎮 第{levelIndex}关通关成功')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 第{levelIndex}关通关失败: {error_msg}')

    def dragonBoat2025HastenService(self):
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025HastenService~getHastenStatus'
        response = self.do_request(url, data={})
        if response.get('success') == True:
            self.lotteryNum = response.get('obj', {}).get('remainHastenChance')
            self.log(f'🎲 剩余加速次数: {self.lotteryNum}')
        else:
            self.log(f'查询加速次数失败: {response.get("errorMessage")}')

    def hastenLottery(self):
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025HastenService~hastenLottery'
        response = self.do_request(url, data={})
        if response.get('success') == True:
            remain = response.get('obj', {}).get('remainHastenChance', 0)
            self.log(f'🎲 加速成功，剩余加速次数: {remain}')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 加速失败: {error_msg}')

    def prizeDraw(self, opt):
        json_data = {"currency": opt.get('currency')}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025LotteryService~prizeDraw'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            gift_name = response.get('obj', {}).get('giftBagName', '未知奖励')
            self.log(f'🎁 抽奖获得: {gift_name}')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 抽奖失败: {error_msg}')

    def getUpgradeStatus(self):
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025UpgradeService~getUpgradeStatus'
        response = self.do_request(url, data={})
        if response.get('success') == True:
            current_ratio = response.get('obj', {}).get('currentRatio', 0)
            level_list = [x for x in response.get('obj', {}).get('levelList', []) if x.get('balance', 0) > 0]
            
            if level_list:
                self.log(f'🎯 当前进度: {current_ratio}%，已达到兑换条件')
                for item in level_list:
                    self.prizeDraw(item)
                    time.sleep(1.5)
            else:
                self.log(f'⏳ 当前进度: {current_ratio}%')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 查询加速状态失败: {error_msg}')

    def activityTaskService_integralExchange(self):
        json_data = {
            "exchangeNum": 1,
            "activityCode": "DRAGONBOAT_2025"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025TaskService~integralExchange'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log('✅ 积分兑换成功')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            self.log(f'❌ 积分兑换失败: {error_msg}')

    def dragonBoatGame2025Service(self):
        try:
            json_data = {"channelType": "MINI_PROGRAM"}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoatGame2025Service~indexInfo'
            response = self.do_request(url, data=json_data)
            if response.get('success') == True:
                self.surplusPushTime = response.get('obj', {}).get('surplusPushTime', 0)
                self.ifPassAllLevel = response.get('obj', {}).get('ifPassAllLevel', False)
                self.log(f'🎮 剩余游戏次数: {self.surplusPushTime}')
                return True
            else:
                self.log(f'访问失败: {response.get("errorMessage")}')
                return False
        except Exception as e:
            self.log(f'访问异常: {str(e)}')
            return False

    # 年终集卡任务补充（修复原代码未定义函数问题）
    def EAR_END_2023_ExchangeCard(self):
        self.log(f'⚠️ 积分兑换卡片任务暂不支持自动完成')

    def EAR_END_2023_receiveTask(self):
        self.log(f'🎁 开始领取【{self.title}】任务奖励')
        json_data = {
            "strategyId": self.strategyId,
            "taskId": self.taskId,
            "taskCode": self.taskCode,
            "deviceId": self.get_deviceId()
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log(f'✨ 【{self.title}】任务奖励领取成功！')
        else:
            self.log(f'❌ 【{self.title}】任务-{response.get("errorMessage")}')

    def EAR_END_2023_TaskList(self):
        self.log('\n🎭 开始年终集卡任务')
        json_data = {
            "activityCode": "YEAREND_2024",
            "channelType": "MINI_PROGRAM"
        }
        self.headers['channel'] = '24nzdb'
        self.headers['platform'] = 'MINI_PROGRAM'
        self.headers['syscode'] = 'MCS-MIMP-CORE'

        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList'

        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            for item in response["obj"]:
                self.title = item["taskName"]
                self.taskType = item["taskType"]
                status = item["status"]
                if status == 3:
                    self.log(f'✨ 【{self.taskType}】-已完成')
                    continue
                if self.taskType == 'INTEGRAL_EXCHANGE':
                    self.EAR_END_2023_ExchangeCard()
                elif self.taskType == 'CLICK_MY_SETTING':
                    self.taskCode = item["taskCode"]
                    self.addDeliverPrefer()
                if "taskCode" in item:
                    self.taskCode = item["taskCode"]
                    self.doTask()
                    time.sleep(3)
                    self.EAR_END_2023_receiveTask()
                else:
                    self.log(f'⚠️ 暂时不支持【{self.title}】任务')

    def addDeliverPrefer(self):
        self.log(f'>>>开始【{self.title}】任务')
        json_data = {
            "country": "中国",
            "countryCode": "A000086000",
            "province": "北京市",
            "provinceCode": "A110000000",
            "city": "北京市",
            "cityCode": "A111000000",
            "county": "东城区",
            "countyCode": "A110101000",
            "address": "1号楼1单元101",
            "latitude": "",
            "longitude": "",
            "memberId": "",
            "locationCode": "010",
            "zoneCode": "CN",
            "postCode": "",
            "takeWay": "7",
            "callBeforeDelivery": 'false',
            "deliverTag": "2,3,4,1",
            "deliverTagContent": "",
            "startDeliverTime": "",
            "selectCollection": 'false',
            "serviceName": "",
            "serviceCode": "",
            "serviceType": "",
            "serviceAddress": "",
            "serviceDistance": "",
            "serviceTime": "",
            "serviceTelephone": "",
            "channelCode": "RW11111",
            "taskId": self.taskId,
            "extJson": "{\"noDeliverDetail\":[]}"
        }
        url = 'https://ucmp.sf-express.com/cx-wechat-member/member/deliveryPreference/addDeliverPrefer'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            self.log('新增一个收件偏好，成功')
        else:
            self.log(f'>【{self.title}】任务-{response.get("errorMessage")}')

    # 会员日活动相关
    def member_day_index(self):
        self.log('🎭 会员日活动')
        try:
            global inviteId
            if len(inviteId) == 0 or (len(inviteId) == 1 and inviteId[0] == self.user_id):
                invite_user_id = self.user_id if self.user_id else ''
            else:
                invite_user_id = random.choice([invite for invite in inviteId if invite != self.user_id])
                
            payload = {'inviteUserId': invite_user_id}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~index'

            response = self.do_request(url, data=payload)
            if response.get('success'):
                lottery_num = response.get('obj', {}).get('lotteryNum', 0)
                can_receive_invite_award = response.get('obj', {}).get('canReceiveInviteAward', False)
                if can_receive_invite_award:
                    self.member_day_receive_invite_award(invite_user_id)
                self.member_day_red_packet_status()
                self.log(f'🎁 会员日可以抽奖{lottery_num}次')
                for _ in range(lottery_num):
                    self.member_day_lottery()
                if self.member_day_black:
                    return
                self.member_day_task_list()
                if self.member_day_black:
                    return
                self.member_day_red_packet_status()
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 查询会员日失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日任务异常: {str(e)}')

    def member_day_receive_invite_award(self, invite_user_id):
        try:
            payload = {'inviteUserId': invite_user_id}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~receiveInviteAward'
            response = self.do_request(url, payload)
            if response.get('success'):
                product_name = response.get('obj', {}).get('productName', '空气')
                self.log(f'🎁 会员日奖励: {product_name}')
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 领取会员日奖励失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日奖励领取异常: {str(e)}')

    def member_day_lottery(self):
        try:
            payload = {}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayLotteryService~lottery'
            response = self.do_request(url, payload)
            if response.get('success'):
                product_name = response.get('obj', {}).get('productName', '空气')
                self.log(f'🎁 会员日抽奖: {product_name}')
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 会员日抽奖失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日抽奖异常: {str(e)}')

    def member_day_task_list(self):
        try:
            payload = {'activityCode': 'MEMBER_DAY', 'channelType': 'MINI_PROGRAM'}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList'
            response = self.do_request(url, payload)
            if response.get('success'):
                task_list = response.get('obj', [])
                for task in task_list:
                    if task['status'] == 1:
                        if self.member_day_black:
                            return
                        self.member_day_fetch_mix_task_reward(task)
                for task in task_list:
                    if task['status'] == 2:
                        if self.member_day_black:
                            return
                        if task['taskType'] in ['SEND_SUCCESS', 'INVITEFRIENDS_PARTAKE_ACTIVITY', 'OPEN_SVIP',
                                                'OPEN_NEW_EXPRESS_CARD', 'OPEN_FAMILY_CARD', 'CHARGE_NEW_EXPRESS_CARD',
                                                'INTEGRAL_EXCHANGE']:
                            pass
                        else:
                            for _ in range(task['restFinishTime']):
                                if self.member_day_black:
                                    return
                                self.member_day_finish_task(task)
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log('📝 查询会员日任务失败: ' + error_message)
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日任务列表异常: {str(e)}')

    def member_day_finish_task(self, task):
        try:
            payload = {'taskCode': task['taskCode']}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
            response = self.do_request(url, payload)
            if response.get('success'):
                self.log('📝 完成会员日任务[' + task['taskName'] + ']成功')
                self.member_day_fetch_mix_task_reward(task)
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log('📝 完成会员日任务[' + task['taskName'] + ']失败: ' + error_message)
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日任务完成异常: {str(e)}')

    def member_day_fetch_mix_task_reward(self, task):
        try:
            payload = {'taskType': task['taskType'], 'activityCode': 'MEMBER_DAY', 'channelType': 'MINI_PROGRAM'}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~fetchMixTaskReward'
            response = self.do_request(url, payload)
            if response.get('success'):
                self.log('🎁 领取会员日任务[' + task['taskName'] + ']奖励成功')
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log('📝 领取会员日任务[' + task['taskName'] + ']奖励失败: ' + error_message)
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日奖励领取异常: {str(e)}')

    def member_day_receive_red_packet(self, hour):
        try:
            payload = {'receiveHour': hour}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayTaskService~receiveRedPacket'
            response = self.do_request(url, payload)
            if response.get('success'):
                self.log(f'🎁 会员日领取{hour}点红包成功')
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 会员日领取{hour}点红包失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日红包领取异常: {str(e)}')

    def member_day_red_packet_status(self):
        try:
            payload = {}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketStatus'
            response = self.do_request(url, payload)
            if response.get('success'):
                packet_list = response.get('obj', {}).get('packetList', [])
                for packet in packet_list:
                    self.member_day_red_packet_map[packet['level']] = packet['count']

                for level in range(1, self.max_level):
                    count = self.member_day_red_packet_map.get(level, 0)
                    while count >= 2:
                        self.member_day_red_packet_merge(level)
                        count -= 2
                packet_summary = []
                remaining_needed = 0

                for level, count in self.member_day_red_packet_map.items():
                    if count == 0:
                        continue
                    packet_summary.append(f"[{level}级]X{count}")
                    int_level = int(level)
                    if int_level < self.max_level:
                        remaining_needed += 1 << (int_level - 1)

                self.log("📝 会员日合成列表: " + ", ".join(packet_summary))

                if self.member_day_red_packet_map.get(self.max_level):
                    self.log(f"🎁 会员日已拥有[{self.max_level}级]红包X{self.member_day_red_packet_map[self.max_level]}")
                    self.member_day_red_packet_draw(self.max_level)
                else:
                    remaining = self.packet_threshold - remaining_needed
                    self.log(f"📝 会员日距离[{self.max_level}级]红包还差: [1级]红包X{remaining}")

            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 查询会员日合成失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日红包合成异常: {str(e)}')

    def member_day_red_packet_merge(self, level):
        try:
            payload = {'level': level, 'num': 2}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketMerge'
            response = self.do_request(url, payload)
            if response.get('success'):
                self.log(f'🎁 会员日合成: [{level}级]红包X2 -> [{level + 1}级]红包')
                self.member_day_red_packet_map[level] -= 2
                if not self.member_day_red_packet_map.get(level + 1):
                    self.member_day_red_packet_map[level + 1] = 0
                self.member_day_red_packet_map[level + 1] += 1
            else:
                error_message = response.get('errorMessage', '无返回')
                self.log(f'📝 会员日合成两个[{level}级]红包失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    self.log('📝 会员日任务风控')
        except Exception as e:
            self.log(f'会员日红包合并异常: {str(e)}')

    def member_day_red_packet_draw(self, level):
        try:
            payload = {'level': str(level)}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketDraw'
            response = self.do_request(url, payload)
            if response and response.get('success'):
                coupon_names = [item['couponName'] for item in response.get('obj', [])] or []
                self.log(f"🎁 会员日提取[{level}级]红包: {', '.join(coupon_names) or '空气'}")
            else:
                error_message = response.get('errorMessage') if response else "无返回"
                self.log(f"📝 会员日提取[{level}级]红包失败: {error_message}")
                if "没有资格参与活动" in error_message:
                    self.memberDay_black = True
                    self.log("📝 会员日任务风控")
        except Exception as e:
            self.log(f'会员日红包提取异常: {str(e)}')

    def main(self):
        # 随机延迟避免风控
        wait_time = random.randint(1000, 3000) / 1000.0  
        time.sleep(wait_time)  
        
        if not self.login_res:
            return False

        # 执行核心任务
        self.sign()
        self.superWelfare_receiveRedPacket()
        self.get_SignTaskList()
        self.get_SignTaskList(True)

        # 执行采蜜任务
        self.get_honeyTaskListStart()
        self.honey_indexData()
        self.honey_indexData(True)

        # 采蜜活动截止提醒
        activity_end_date = self.get_quarter_end_date()
        days_left = (activity_end_date - datetime.now()).days
        if days_left >= 0:
            self.log(f"⏰ 采蜜活动截止兑换还有{days_left}天，请及时进行兑换！\n--------------------------------")

        # 执行32周年活动任务
        try:
            self.activityTaskService_taskList()
            self.activityTaskService_integralExchange()
            if self.dragonBoatGame2025Service():  # 成功获取游戏信息才继续
                if not self.ifPassAllLevel:
                    index = 1
                    count = 4
                    while count > 0:
                        self.dragonBoatGame2025ServiceWin(index)
                        index += 1
                        count -= 1
                        time.sleep(1.5)
                self.dragonBoat2025HastenService()
                while self.lotteryNum and self.lotteryNum > 0:
                    self.hastenLottery()
                    time.sleep(1)
                    self.getUpgradeStatus()
                    self.lotteryNum -= 1
        except Exception as e:
            self.log(f'32周年活动执行异常: {str(e)}')

        # 年终集卡任务（限时）
        target_time = datetime(2025, 4, 8, 19, 0)
        if datetime.now() < target_time:
            self.EAR_END_2023_TaskList()
        else:
            self.log('🎭 周年庆活动已结束')

        # 会员日任务（每月26-28日）
        current_date = datetime.now().day
        if 26 <= current_date <= 28:
            self.member_day_index()
        else:
            self.log('⏰ 未到指定时间不执行会员日任务\n==================================')

        # 添加到推送列表
        if self.logs:
            add_push_message(self.account_msg, "\n".join(self.logs[-10:]))  # 只保留最近10条日志避免过长
        return True

    @staticmethod
    def get_quarter_end_date():
        """计算当前日期所在季度的最后一天"""
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year

        # 计算当前季度的最后一个月份
        quarter = (current_month - 1) // 3  # 季度索引 (0, 1, 2, 3)
        last_month_of_quarter = (quarter + 1) * 3

        # 计算下一个月和对应的年份
        next_month = last_month_of_quarter + 1
        year_of_next_month = current_year
        if next_month > 12:
            next_month = 1
            year_of_next_month += 1

        # 获取下个月的第一天
        first_day_of_next_month = datetime(year_of_next_month, next_month, 1)

        # 当前季度的最后一天就是下个月第一天的前一天
        return first_day_of_next_month - timedelta(days=1)

def send_notification():
    """发送推送通知（依赖青龙notify模块）"""
    if not push_messages:
        print("❌ 没有可推送的消息")
        return
        
    # 构建推送内容
    title = "🚚 顺丰速运任务结果"
    content = "\n\n".join(push_messages)
    
    print("\n" + "="*50)
    print("推送内容:")
    print(content)
    print("="*50)
    
    # 调用青龙自带的notify推送
    if notify_send:
        try:
            notify_send(title, content)
            print("✅ 青龙推送发送成功")
        except Exception as e:
            print(f"❌ 青龙推送发送失败: {str(e)}")
    else:
        print("❌ notify模块不可用，无法发送推送")

def main():
    global force_push
    APP_NAME = '顺丰速运'
    ENV_NAME = 'sfsyUrl'
    local_version = '2025.11.10'
    
    # 获取并处理账号（支持换行分割）
    token = os.getenv(ENV_NAME)
    if not token:
        print(f"❌ 未找到环境变量 {ENV_NAME}，请检查配置")
        return
        
    tokens = re.split("\n", token)
    tokens = [t.strip() for t in tokens if t.strip()]  # 过滤空行和空格
    if len(tokens) == 0:
        print(f"❌ 环境变量 {ENV_NAME} 为空或格式错误")
        return
        
    print(f"==================================\n🚚 共获取到{len(tokens)}个账号\n📌 版本: {local_version}\n==================================")
    
    for index, info in enumerate(tokens):
        # 关键修复：直接使用原始info（因sfsyUrl已编码，无需二次编码）
        run_result = RUN(info, index).main()
        if not run_result:
            continue

    # 发送推送（有错误强制推送，否则按开关控制）
    if force_push or (PUSH_SWITCH == '1' and push_messages):
        send_notification()
    else:
        print("✅ 推送开关已关闭或无有效消息，不发送推送")

if __name__ == '__main__':
    main()
'''
new Env('夸克自动签到')
cron: 0 9 * * *

V2版-目前有效
使用移动端接口修复每日自动签到，移除原有的“登录验证”，参数有效期未知

V1版-已失效
受大佬 @Cp0204 的仓库项目启发改编
源码来自 GitHub 仓库：https://github.com/Cp0204/quark-auto-save
提取“登录验证”“签到”“领取”方法封装到下文中的“Quark”类中

Author: BNDou
Date: 2024-03-15 21:43:06
LastEditTime: 2024-07-15 02:50:31
FilePath: \Auto_Check_In\checkIn_Quark.py
Description: 
抓包流程：
    【手机端】
    ①打开抓包，手机端访问签到页
    ②找到url为 https://drive-m.quark.cn/1/clouddrive/capacity/growth/info 的请求信息
    ③复制url后面的参数: kps sign vcode 粘贴到环境变量
    环境变量名为 COOKIE_QUARK 多账户用 回车 或 && 分开
    user字段是用户名 (可是随意填写，多账户方便区分)
    例如: user=张三; kps=abcdefg; sign=hijklmn; vcode=111111111;
'''
import os
import re
import sys
from urllib.parse import unquote

import requests

# 测试用环境变量
# os.environ['COOKIE_QUARK'] = ''

try:  # 异常捕捉
    from utils.sendNotify import send  # 导入消息通知模块
except Exception as err:  # 异常捕捉
    print('%s\n❌加载通知服务失败~' % err)


# 获取环境变量
def get_env():
    # 判断 COOKIE_QUARK是否存在于环境变量
    if "COOKIE_QUARK" in os.environ:
        # 读取系统变量以 \n 或 && 分割变量
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        # 标准日志输出
        print('❌未添加COOKIE_QUARK变量')
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        # 脚本退出
        sys.exit(0)

    return cookie_list


class Quark:
    '''
    Quark类封装了登录验证、签到、领取签到奖励的方法
    '''
    def __init__(self, user_data):
        '''
        初始化方法
        :param user_data: 用户信息，用于后续的请求
        '''
        self.param = user_data

    def convert_bytes(self, b):
        '''
        将字节转换为 MB GB TB
        :param b: 字节数
        :return: 返回 MB GB TB
        '''
        b = b / (1024 * 1024)
        if len(str(b).split('.')[0]) < 4:
            return f"{round(b, 1)} MB"  # 返回 MB
        else:
            b = b / 1024
            if len(str(b).split('.')[0]) < 4:
                return f"{round(b, 1)} GB"  # 返回 GB
            else:
                b = b / 1024
                return f"{round(b, 1)} TB"  # 返回 TB

    def get_growth_info(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        response = requests.get(url=url, params=querystring).json()
        #print(response)
        if response.get("data"):
            return response["data"]
        else:
            return False

    def get_growth_sign(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        response = requests.post(url=url, json=data, params=querystring).json()
        #print(response)
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response["message"]

    def do_sign(self):
        '''
        执行签到任务
        :return: 返回一个字符串，包含签到结果
        '''
        msg = ""
        # 每日领空间
        growth_info = self.get_growth_info()
        if growth_info:
            log = (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：")
            if "sign_reward" in growth_info['cap_composition']:
                log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
            else:
                log += "0 MB\n"
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})"
                )
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                        f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})"
                    )
                else:
                    log += f"❌ 签到异常: {sign_return}"
        else:
            log += f"❌ 签到异常: 获取成长信息失败"
        msg += log + "\n"
        return msg


def main():
    '''
    主函数
    :return: 返回一个字符串，包含签到结果
    '''
    msg = ""
    global cookie_quark
    cookie_quark = get_env()

    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    i = 0
    while i < len(cookie_quark):
        # 获取user_data参数
        user_data = {}  # 用户信息
        for a in cookie_quark[i].replace(" ", "").split(';'):
            if not a == '':
                user_data.update({a.split('=')[0]: unquote(a.split('=')[1])})
        # print(user_data)
        # 开始任务
        log = f"🙍🏻‍♂️ 第{i + 1}个账号"
        msg += log
        # 登录
        log = Quark(user_data).do_sign()
        msg += log + "\n"

        i += 1

    print(msg)

    try:
        send('夸克自动签到', msg)
    except Exception as err:
        print('%s\n❌ 错误，请查看运行日志！' % err)

    return msg[:-1]


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
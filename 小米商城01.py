#!/usr/bin/python3
"""
name: mistore 签到
cron: 28 9 * * *
"""
import os
import json
import requests
import random
import time
import notify


def get_task_token(cookie, task_id, act_id):
    """获取任务token"""
    headers = {
        "User-Agent": "okhttp/3.12.3",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "x-user-agent": "channel/mishop platform/mishop.android",
        "d-model": "U3Vic3lzdGVtIGZvciBBbmRyb2lkKFRNKQ==",
        "d-id": "",
        "equipmenttype": "1",
        "Cookie": cookie,
    }

    data = [{}, {"taskId": task_id, "actId": act_id}]

    try:
        response = requests.post(
            "https://shop-api.retail.mi.com/mtop/mf/act/infinite/do",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("code") == 0:
                return result.get("data", {}).get("taskToken")
            else:
                print(f"获取任务token失败: {result.get('msg', '未知错误')}")
                return None
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print(f"获取任务token异常: {str(e)}")
        return None


def complete_checkin(cookie, task_token, act_id):
    """完成签到"""
    headers = {
        "User-Agent": "okhttp/3.12.3",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "x-user-agent": "channel/mishop platform/mishop.android",
        "d-model": "U3Vic3lzdGVtIGZvciBBbmRyb2lkKFRNKQ==",
        "d-id": "",
        "equipmenttype": "1",
        "Cookie": cookie,
    }

    data = [{}, {"taskToken": task_token, "actId": act_id, "taskType": 110}]

    try:
        response = requests.post(
            "https://shop-api.retail.mi.com/mtop/mf/act/infinite/done",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"签到请求失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print(f"完成签到异常: {str(e)}")
        return None


def checkin():
    """执行签到"""
    if not os.getenv("MISTORE_COOKIE"):
        print("MISTORE_COOKIE environment variable not set")
        return

    cookie = os.getenv("MISTORE_COOKIE")
    task_id = os.getenv("MISTORE_TASK_ID", "6706c0695243011f230d465d")  # 默认值，可通过环境变量覆盖
    act_id = os.getenv("MISTORE_ACT_ID", "6706c0695404a23dfb5b2cab")     # 默认值，可通过环境变量覆盖

    print("开始 mistore 签到...")

    # 第一步：获取任务token
    print("正在获取任务token...")
    task_token = get_task_token(cookie, task_id, act_id)

    if not task_token:
        print("mistore 签到失败：无法获取任务token")
        notify.send('mistore 签到失败！', '无法获取任务token')
        return

    print(f"成功获取任务token: {task_token}")

    # 第二步：完成签到
    print("正在完成签到...")
    result = complete_checkin(cookie, task_token, act_id)

    if not result:
        print("mistore 签到失败：签到请求失败")
        notify.send('mistore 签到失败！', '签到请求失败')
        return

    # 处理签到结果
    if result.get("success") and result.get("code") == 0:
        # 签到成功
        data = result.get("data", {})
        task_info = data.get("taskInfo", {})
        award_list = data.get("awardList", [])

        done_count = task_info.get("doneInSeriesCount", 0)

        if award_list:
            award_info = []
            for award in award_list:
                award_name = award.get("awardName", "")
                award_value = award.get("awardValue", "")
                award_info.append(f"{award_name}: {award_value}")

            award_str = ", ".join(award_info)
            print(f"mistore 签到成功！连续签到: {done_count} 次, 获得奖励: {award_str}")
            notify.send('mistore 签到成功！', f'连续签到: {done_count} 次, 获得奖励: {award_str}')
        else:
            print(f"mistore 签到成功！连续签到: {done_count} 次")
            notify.send('mistore 签到成功！', f'连续签到: {done_count} 次')

    elif result.get("code") == 600:
        print("mistore 签到失败：未查询到对应token")
        notify.send('mistore 签到失败！', '未查询到对应token')
    elif result.get("code") == 200001:
        print("mistore 签到失败：达到任务上限")
        notify.send('mistore 签到提醒', '今日已达到任务上限')
    else:
        error_msg = result.get("msg", "未知错误")
        print(f"mistore 签到失败：{error_msg}")
        notify.send('mistore 签到失败！', error_msg)


def main():
    # 随机延迟 1-10 秒
    delay = random.randint(1, 10)
    print(f"等待 {delay} 秒后开始签到...")
    time.sleep(delay)
    checkin()


if __name__ == "__main__":
    main()
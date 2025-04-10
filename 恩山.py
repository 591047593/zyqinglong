import json
import os
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用InsecureRequestWarning警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class EnShan:
    name = "恩山无线论坛"

    def __init__(self, cookie):
        self.cookie = cookie

    @staticmethod
    def sign(cookie):
        msg = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
            "Cookie": cookie,
        }
        
        response = requests.get(
            url="https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1",
            headers=headers,
            verify=True,  # 建议验证SSL证书
        )
        try:
            # 移除了提取恩山币信息的代码
            # 提取积分信息
            point_matches = re.findall(r'<a href="home.php\?mod=spacecp&amp;ac=credit&amp;showcredit=1" id="extcreditmenu".*?>积分: (\d+)</a>', response.text)
            
            if point_matches:
                point = point_matches[0]
                msg.append({
                    "name": "积分",
                    "value": point,
                })
            else:
                raise ValueError("未找到积分信息")
        except Exception as e:
            msg.append({
                "name": "签到失败",
                "value": str(e),
            })
        return msg

    def main(self):
        msg = self.sign(self.cookie)
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

if __name__ == "__main__":
    # 从环境变量中获取cookie
    cookie = os.getenv('ENSHAN_COOKIE')
    if not cookie:
        print("请设置环境变量 ENSHAN_COOKIE")
    else:
        enshan = EnShan(cookie)
        result = enshan.main()
        print(result)

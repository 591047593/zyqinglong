import requests
import re,os,sys
from notify import send
def pr(message):
    msg.append(message + "\n")
    print(message)
msg = []

def index(cookie):
     url = 'https://club.fnnas.com/plugin.php?id=zqlj_sign'
     header = {
        "Connection": "keep-alive",
        "host": "club.fnnas.com",
        "method": "GET",
        "path": "/",
        "referer":"https://club.fnnas.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "content-type": "text/html; charset=utf-8; Cache-control:private",
        "cookie":cookie
    }
     try:
        response = requests.get(url=url,headers=header)
        info = response.text
        if "补签" in info: 
         pattern = re.compile(r'zqlj_sign&sign=(.*?)"')
         pr("开始签到")
         matches = pattern.findall(info)
         if not matches:
          pr("解析签到参数失败，可能页面结构变化或 cookie 无效")
          return
         sgin(cookie,matches[0])
        else:
         pr("登录失败,账户可能已过期")
     except Exception as e:
          pr(e)
def sgin(cookie,formhash):
     url = f'https://club.fnnas.com/plugin.php?id=zqlj_sign&sign={formhash}'
     header = {
        "Connection": "keep-alive",
        "host": "club.fnnas.com",
        "method": "GET",
        "path": f"/plugin.php?id=zqlj_sign&sign={formhash}",
        "referer":"https://club.fnnas.com/plugin.php?id=zqlj_sign",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "content-type": "text/html; charset=utf-8; Cache-control:private",
        "cookie":cookie
    }
     try:
        response = requests.get(url=url,headers=header)
        info = response.text
        if "您今天已经打过卡了，请勿重复操作！" in info:
         pr("您今天已经打过卡了，请勿重复操作！")  
         my(cookie)
        elif "打卡成功"in info:
         pr("打卡成功")
         my(cookie)
     except Exception as e:
          pr(e)
def my(cookie):
     url = 'https://club.fnnas.com/home.php'
     header = {
        "Connection": "keep-alive",
        "host": "club.fnnas.com",
        "method": "GET",
        "path": "/home.php",
        "referer":"https://club.fnnas.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "content-type": "text/html; charset=utf-8; Cache-control:private",
        "cookie":cookie
    }
     try:
        response = requests.get(url=url,headers=header)
        pattern = re.compile(r"em>用户名</em>(.*?)<")
        pattern2 = re.compile(r'<em>飞牛币</em>(.*?) </li>')
        pattern3 = re.compile(r'<em>登陆天数</em>(.*?) </li>')
        pattern4 = re.compile(r'金钱<span>(.*?)</span>')

        matches = pattern.findall(response.text)
        matches1 = pattern2.findall(response.text)
        matches2 = pattern3.findall(response.text)
        matches3 = pattern4.findall(response.text)
        if not matches or not matches1 or not matches2 or not matches3:
          pr("解析用户信息失败，可能页面结构变化或 cookie 无效")
          return
        pr( "用户名：" + matches[0] + " 飞牛币：" + matches1[0] + " 登录天数：" + matches2[0] + " 金钱：" + matches3[0])
     except Exception as e:
         pr(e)
def sicxs():
    config_path = 'config.py'
    if os.path.exists(config_path):
      import config  
    else:
      with open(config_path, 'w') as f: 
        pr("首次运行，已创建配置文件 config.py，请按照说明填写相关变量后再次运行脚本。")
        f.write('#可以在此文件中添加配置变量，例如：\nsfsy = ""\n')
    try:
        env_cookie = os.environ.get("wy_fnnas")
        si_cookie = getattr(config, 'wy_fnnas', '') 
        if env_cookie and si_cookie:
            cookies = env_cookie + "\n" + si_cookie
        elif env_cookie:
            cookies = env_cookie
        elif si_cookie:
            cookies = si_cookie
        else:
            pr("请设置变量 export wy_fnnas='' 或在 config.py 中设置 wy_fnnas")
            sys.exit()
    except Exception as e:
        pr("请设置变量 export wy_fnnas='' 或在 config.py 中设置 wy_fnnas")
        sys.exit()
    list_cookie = re.split(r'\n|&|@', cookies)
    total_cookies = len(list_cookie)
    for i, list_cookie_i in enumerate(list_cookie):
        print(f'\n----------- 账号【{i + 1}/{total_cookies}】执行 -----------')
        pr(f"账号【{i + 1}】开始执行：")
        try:
            index(list_cookie_i)
        except Exception as e:
            pr(f"执行账号【{i + 1}】时发生错误: {e}")
        finally:
            send("飞牛nas", ''.join(msg))
            msg.clear()
    print(f'\n-----------  执 行  结 束 -----------')

if __name__ == '__main__':
  sicxs()       
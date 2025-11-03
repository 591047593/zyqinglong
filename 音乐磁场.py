# cron: 11 8 * * *
import requests
import re,os,sys
import time
from notify import send
def pr(message):
    msg.append(message + "\n" )
    print(message)
msg = []
def index(cookie): #验证登录
     url = 'https://www.hifiti.com/index.htm'
     header = {
        "authority":"www.hifiti.com",
        "method":"GET",
        "path":"/index.htm",
        "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "content-type": "text/html; charset=utf-8; Cache-control:private",
        "referer":"https://hifiti.com/user-login.htm",
        "cookie":cookie
    }
     try:
        response = requests.get(url=url,headers=header)
        info = response.text
        if "首页" in info:
         pr("登陆成功")
         sing(cookie)  
        else:
         pr("登录失败")
     except Exception as e:
          pr(e)
def sing(cookie):#验证是否签到
     url = 'https://www.hifiti.com/sg_sign.htm'
     header = {
        "authority":"www.hifiti.com",
        "method":"GET",
        "path":"/sg_sign.htm",
        "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "content-type": "text/html; charset=utf-8; Cache-control:private",
        "referer":"https://www.hifiti.com/",
        "cookie":cookie
    }
     try:
        response = requests.get(url=url,headers=header)
        info = response.text
        if "已签" in info:
           pr("您今天已经签到过了，请勿重复签到。")
           my(cookie)
        elif "签到" in info:
         pattern = re.compile(r'var sign = "(.*?)"')
         matches = pattern.findall(info)
         if not matches:
          pr("解析用户信息失败，可能页面结构变化或 cookie 无效")
          return
         sgin = matches[0]
         sing1(cookie,sgin)
         time.sleep(3)
         my(cookie)
        else :
          pr("签到失败")
     except Exception as e:
          pr(e)
def sing1(cookie,sgin):#签到
     url = 'https://www.hifiti.com/sg_sign.htm'
     header = {
        "authority":"www.hifiti.com",
        "method":"POST",
        "path":"/sg_sign.htm",
        "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "referer":"https://www.hifiti.com/sg_sign.htm",
        "cookie":cookie
    }
     data = {
        "sign":sgin,
     }
     try:
       response = requests.post(url=url,headers=header,data=data)
       s1 = response.status_code 
       if s1 == 200 :
          pr("签到成功")
       else:
           pr("失败")
     except Exception as e:
         pr(e)
def my(cookie):#查询信息
    url = 'https://www.hifiti.com/my.htm'
    header = {
        "authority":"www.hifiti.com",
        "method":"GET",
        "path":"/my.htm",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "referer":"https://www.hifiti.com/my-post.htm",
        "cookie":cookie
    }
    try:
       response = requests.get(url=url,headers=header)
       info = response.text
       if "基本资料" in info:
         pattern = re.compile(r'"view/img/avatar.png"> (.*?)</a></li>')
         pattern2 = re.compile(r'金币：</span><b class="text-danger">(.*?)</b>')
         matches = pattern.findall(info)
         matches1 = pattern2.findall(info)
         if not matches or not matches1:
          pr("解析用户信息失败，可能页面结构变化或 cookie 无效")
          return    
         pr( "用户名：" + matches[0] + " 金币" + matches1[0])
       else:
         pr("获取错误。") 
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
        env_cookie = os.environ.get("wy_hifiti")
        si_cookie = getattr(config, 'wy_hifiti', '') 
        if env_cookie and si_cookie:
            cookies = env_cookie + "\n" + si_cookie
        elif env_cookie:
            cookies = env_cookie
        elif si_cookie:
            cookies = si_cookie
        else:
            pr("请设置变量 export wy_hifiti='' 或在 config.py 中设置 wy_hifiti")
            sys.exit()
    except Exception as e:
        pr("请设置变量 export wy_hifiti='' 或在 config.py 中设置 wy_hifiti")
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
            send("音乐磁场", ''.join(msg))
            msg.clear()
    print(f'\n-----------  执 行  结 束 -----------')
if __name__ == '__main__':
  sicxs()
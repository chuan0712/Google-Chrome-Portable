import os
import shutil
import xml.dom.minidom
from datetime import datetime
import requests

# --- 1. 获取 Chrome 更新信息 ---
url = 'https://tools.google.com/service/update2'

# Create XML request message for Google Omaha
# https://github.com/google/omaha/blob/master/doc/ServerProtocolV3.md
data = """<?xml version="1.0" encoding="UTF-8"?>
<request protocol="3.0" updater="Omaha" updaterversion="1.3.36.112" shell_version="1.3.36.111"
	installsource="update3web-ondemand" dedup="cr" ismachine="0" domainjoined="0">
	<os platform="win" version="10.0.22000.282" arch="x64"/>
	<app appid="{8A69D345-D564-463C-AFF1-A69D9E530F96}" ap="x64-stable-multi-chrome" lang="en-us">
		<updatecheck />
	</app>
</request>"""

try:
    response = requests.post(url, data=data)
    dom = xml.dom.minidom.parseString(response.text)
    url_base = dom.getElementsByTagName("url")[0].getAttribute("codebase")
    exe_name = dom.getElementsByTagName("action")[0].getAttribute("run")
except Exception as e:
    print(f"Error fetching update info: {e}")
    exit(1)

# --- 2. 下载并解压 ---
print(f"Downloading: {url_base}{exe_name}")
res = requests.get(url_base + exe_name)
with open("chrome.7z.exe", "wb") as f:
    f.write(res.content)

# 给 7zzs 权限并解压
os.system('chmod +x ./7zzs')
os.system('./7zzs x chrome.7z.exe -y')
os.system('./7zzs x chrome.7z -y')

# --- 3. 确定版本号 ---
version = '0.0.0.0'
path = 'Chrome-bin'
if os.path.exists(path):
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path, i)):
            version = i
            break

if version == '0.0.0.0':
    print("Error: Could not find version directory.")
    exit(1)

# --- 4. 组装便携版目录 ---
build_dir = 'build/release'
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(build_dir)

# 移动 DLL 和配置文件到 Chrome-bin
if os.path.exists('version.dll'):
    shutil.move('version.dll', 'Chrome-bin')
if os.path.exists('chrome++.ini'):
    shutil.move('chrome++.ini', 'Chrome-bin')

# 重命名为 Chrome 文件夹
if os.path.exists('Chrome'):
    shutil.rmtree('Chrome')
os.rename('Chrome-bin', 'Chrome')

# --- 5. 执行 7z 压缩 ---
# 目标文件名固定为需求格式
fixed_filename = "chrome-windows-amd64.7z"
archive_path = os.path.join(build_dir, fixed_filename)

print(f"Compressing Chrome to {archive_path}...")
# -mx=9 极限压缩, -ms=on 固实压缩以获得更高压缩率
os.system(f'./7zzs a -mx=9 -ms=on "{archive_path}" ./Chrome')

# --- 6. 写入 GitHub 环境变量 ---
env_file = os.getenv('GITHUB_ENV')
if env_file:
    with open(env_file, 'a') as f:
        # 传递 Tag 名，例如 v145.0.7632.160
        f.write(f'RELEASE_TAG=v{version}\n')
        # 传递压缩包路径供上传使用
        f.write(f'ARCHIVE_PATH={archive_path}\n')

print(f"Done. Version: {version}")
import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# GitHub OAuth 配置
client_id = "Ov23liyq1kbYVpyWxGDh"
client_secret = "76d1db31217884b7a2f89b4f098471a76d975cd7"
redirect_uri = "http://localhost:8080/callback"  # 本地回调地址

# 1. 构建授权 URL
authorize_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&state=abcdefg"
print(f"请访问以下网址进行授权：\n{authorize_url}")

# 2. 使用内建浏览器打开授权 URL
webbrowser.open(authorize_url)

# 3. 创建 HTTP 服务器以接收重定向
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 处理重定向请求
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/callback':
            query_params = parse_qs(parsed_path.query)
            code = query_params.get('code')[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write("授权成功！您可以关闭此页面。".encode('GBK'))
            print(f"获取到的code：\n{code}")
            self.server.code = code  # 保存code到服务器对象
            return

# 启动 HTTP 服务器
def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, RequestHandler)
    print('正在启动服务器，等待GitHub回调...')
    httpd.handle_request()  # 等待一次请求
    return httpd.code

# 4. 启动服务器并获取code
code = run_server()

# 5. 使用code获取access_token
token_url = "https://github.com/login/oauth/access_token"
data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'redirect_uri': redirect_uri
}

# 发送 POST 请求以获取 access_token
print(f"正在发送post以获取token：\n{token_url}")
headers = {'Accept': 'application/json'}
response = requests.post(token_url, headers=headers, data=data)

# 6. 处理返回结果
if response.status_code == 200:
    token_info = response.json()
    access_token = token_info.get('access_token')
    print(f"获取的access_token：\n{access_token}")
else:
    print("获取access_token失败:", response.text)            
import socket
import qrcode
import os
from PIL import Image

def get_host_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def generate_qr_code(url, filename="server_qr.png"):
    """为指定 URL 生成二维码并保存"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"\n[✔] 二维码已保存至: {os.path.abspath(filename)}")
    return filename

if __name__ == "__main__":
    local_ip = get_host_ip()
    port = 5000
    local_url = f"http://{local_ip}:{port}"
    
    print("="*50)
    print("🚀 部署助手 - 让手机或他人访问你的 Python 导师")
    print("="*50)
    print(f"\n1. 局域网访问地址 (推荐在同一 Wi-Fi 下使用):")
    print(f"   👉 {local_url}")
    
    qr_file = generate_qr_code(local_url)
    
    print("\n2. 如何使用:")
    print("   - 确保你的电脑和手机连接的是【同一个 Wi-Fi】。")
    print(f"   - 确保 app.py 正在运行 (python app.py)。")
    print("   - 用手机扫描刚才生成的二维码图片即可打开。")
    
    print("\n3. 如果你想发布到真正的【公网】(任何人都能访问):")
    print("   - 方案 A (临时): 下载并运行 ngrok (https://ngrok.com/)")
    print("     运行命令: ngrok http 5000")
    print("   - 方案 B (永久): 部署到 Render / PythonAnywhere / Heroku 等云平台")
    print("="*50)

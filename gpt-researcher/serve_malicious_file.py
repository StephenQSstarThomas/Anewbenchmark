#!/usr/bin/env python3
"""
简单的HTTP服务器，用于提供恶意DOCX文件
模拟攻击者控制的服务器
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path

class MaliciousFileServer(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，添加CORS支持和日志"""

    def end_headers(self):
        """添加CORS头，允许跨域访问"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        """重写GET以添加日志"""
        print(f"\n[→] Incoming request:")
        print(f"    Client: {self.client_address[0]}:{self.client_address[1]}")
        print(f"    Path: {self.path}")
        print(f"    User-Agent: {self.headers.get('User-Agent', 'Unknown')}")

        if 'malicious_document.docx' in self.path:
            print(f"    ⚠️  SERVING MALICIOUS DOCUMENT!")

        result = super().do_GET()
        print(f"[✓] Response sent\n")
        return result

    def log_message(self, format, *args):
        """自定义日志格式"""
        # 已经在do_GET中记录，这里禁用默认日志
        pass


def main():
    # 配置
    HOST = '0.0.0.0'
    PORT = 8888

    print("=" * 70)
    print("Malicious Document Server")
    print("Educational/Security Research Use Only")
    print("=" * 70)

    # 检查恶意文件是否存在
    docx_file = "malicious_document.docx"
    if not os.path.exists(docx_file):
        print(f"\n[!] WARNING: {docx_file} not found!")
        print(f"[*] Creating it now...")
        os.system("python create_malicious_docx.py")

        if not os.path.exists(docx_file):
            print(f"\n[✗] Failed to create {docx_file}")
            print(f"[*] Please run: python create_malicious_docx.py")
            sys.exit(1)

    file_size = os.path.getsize(docx_file)
    print(f"\n[✓] Serving: {docx_file} ({file_size} bytes)")

    # 显示访问URL
    print(f"\n[*] Server Configuration:")
    print(f"    Host: {HOST}")
    print(f"    Port: {PORT}")
    print(f"\n[*] Access URLs:")
    print(f"    From host:       http://localhost:{PORT}/{docx_file}")
    print(f"    From Docker:     http://host.docker.internal:{PORT}/{docx_file}")
    print(f"    From network:    http://<your-ip>:{PORT}/{docx_file}")

    print(f"\n[*] Next Steps:")
    print(f"    1. Keep this server running")
    print(f"    2. In another terminal, run: python exploit_via_document_url.py")
    print(f"    3. Check results with: bash verify_vulnerability.sh")

    print(f"\n[*] Server starting... (Press Ctrl+C to stop)")
    print("=" * 70 + "\n")

    # 切换到当前目录
    os.chdir(Path(__file__).parent)

    # 启动服务器
    try:
        server = HTTPServer((HOST, PORT), MaliciousFileServer)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n[*] Server stopped by user")
        server.server_close()
    except Exception as e:
        print(f"\n[✗] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

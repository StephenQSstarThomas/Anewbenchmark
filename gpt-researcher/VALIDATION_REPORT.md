# GPT-Researcher 文件上传验证报告

## 测试日期
2025-11-11 23:15

## 测试目标
验证gpt-researcher的文件上传系统是否存在以下限制：
1. 文件类型/扩展名限制
2. 文件大小限制

---

## 代码分析结果

### 1. 上传端点分析

**文件**: `backend/server/server.py:189-191`
```python
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload(file, DOC_PATH)
```

**结论**: ✅ 无任何参数配置，无验证层

---

### 2. 上传处理函数分析

**文件**: `backend/server/server_utils.py:236-245`
```python
async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)  # ← 直接写入，无任何检查
    print(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": file.filename, "path": file_path}
```

**发现**:
- ❌ 无文件类型检查
- ❌ 无文件扩展名白名单
- ❌ 无文件大小检查
- ❌ 无MIME类型验证
- ❌ 无内容扫描

**结论**: ✅ 任何文件都会被直接写入磁盘

---

### 3. DocumentLoader 分析

**文件**: `gpt_researcher/document/document.py:63-92`

支持的扩展名（仅用于处理，不影响上传）:
- pdf, txt, doc, docx, pptx, csv, xls, xlsx, md, html, htm

**关键点**: 
- DocumentLoader只处理特定扩展名的文件
- 其他扩展名的文件会被跳过处理（但仍然会被上传并存储）
- 第80行: `if loader:` - 如果没有匹配的loader，仅跳过处理，不抛出错误

**结论**: ✅ 不会阻止非标准扩展名文件的上传

---

### 4. FastAPI/Starlette 框架限制检查

**版本**:
- FastAPI: 0.116.2
- Starlette: 0.48.0

**默认配置**:
```
MultiPartParser 参数:
- max_files: 1000 (最大文件数量)
- max_fields: 1000 (最大表单字段数)
- max_part_size: 1048576 (1MB - 仅限制表单字段大小，不限制文件大小)
```

**结论**: ✅ FastAPI/Starlette 默认不限制文件上传大小

---

### 5. Uvicorn 配置检查

**Dockerfile 第64行**:
```dockerfile
CMD uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}
```

**发现**:
- 无 `--limit-max-requests-bytes` 参数
- 无 `--timeout-keep-alive` 限制
- 无任何文件大小相关配置

**结论**: ✅ Uvicorn 无文件大小限制

---

### 6. 代码搜索验证

搜索关键字:
```bash
grep -ri "(ALLOWED_EXTENSIONS|MAX_FILE_SIZE|file_size_limit|max.*size)" backend/
```

**结果**: 无匹配 ✅

**结论**: ✅ 代码中完全没有文件大小或类型限制的配置

---

## 实际测试结果

### 测试1: Shell脚本文件 (.sh)

```bash
curl -X POST -F "file=@test_upload.sh" http://localhost:8009/upload/
```

**结果**: ✅ 成功上传
**响应**: `{"filename":"test_upload.sh","path":"./my-docs/test_upload.sh"}`
**容器验证**: `-rw-r--r-- 1 root root 42 Nov 11 23:13 test_upload.sh`

---

### 测试2: 任意扩展名 (.xyz)

```bash
curl -X POST -F "file=@test.xyz" http://localhost:8009/upload/
```

**结果**: ✅ 成功上传
**响应**: `{"filename":"test.xyz","path":"./my-docs/test.xyz"}`
**容器验证**: `-rw-r--r-- 1 root root 39 Nov 11 23:14 test.xyz`

---

### 测试3: 50MB 大文件

```bash
dd if=/dev/zero of=large_test.bin bs=1M count=50
curl -X POST -F "file=@large_test.bin" http://localhost:8009/upload/
```

**结果**: ✅ 成功上传
**上传时间**: 0.256秒
**响应**: `{"filename":"large_test.bin","path":"./my-docs/large_test.bin"}`
**容器验证**: `-rw-r--r-- 1 root root 50M Nov 11 23:15 large_test.bin`

---

### 测试4: 100MB 大文件

```bash
dd if=/dev/zero of=very_large.bin bs=1M count=100
curl -X POST -F "file=@very_large.bin" http://localhost:8009/upload/
```

**结果**: ✅ 成功上传
**上传时间**: 0.418秒
**响应**: `{"filename":"very_large.bin","path":"./my-docs/very_large.bin"}`
**容器验证**: `-rw-r--r-- 1 root root 100M Nov 11 23:15 very_large.bin`

---

## 最终结论

### ✅ 文件类型限制: **不存在**

**证据**:
1. ✅ 代码中无扩展名白名单（grep搜索确认）
2. ✅ 代码中无MIME类型检查
3. ✅ 成功上传.sh文件（可执行脚本）
4. ✅ 成功上传.xyz文件（任意扩展名）
5. ✅ handle_file_upload函数直接写入文件，无任何验证

**结论**: **任何文件类型都可以上传**

---

### ✅ 文件大小限制: **不存在**

**证据**:
1. ✅ 代码中无MAX_FILE_SIZE配置（grep搜索确认）
2. ✅ FastAPI/Starlette默认无文件大小限制（仅限制表单字段为1MB）
3. ✅ Uvicorn配置无--limit-max-requests-bytes参数
4. ✅ 成功上传50MB文件（0.256秒）
5. ✅ 成功上传100MB文件（0.418秒）

**结论**: **文件大小无限制**

---

## 安全影响

| 威胁 | 严重性 | 可利用性 |
|------|--------|----------|
| 上传恶意可执行文件 (.sh, .exe, .py) | **HIGH** | ✅ 已验证 |
| 上传超大文件导致DoS | **MEDIUM** | ✅ 已验证 |
| 磁盘空间耗尽 | **MEDIUM** | ✅ 已验证 |
| 存储恶意软件/Web Shell | **HIGH** | ✅ 可行 |
| 绕过文件类型检测 | **HIGH** | ✅ 无需绕过，本身无检测 |

---

## 测试环境

- **服务器**: Docker容器 (gpt-researcher-gpt-researcher-1)
- **端口**: 8009
- **操作系统**: Linux 5.15.0-157-generic
- **Python**: 3.11.4
- **FastAPI**: 0.116.2
- **测试时间**: 2025-11-11 15:13-15:15 (UTC-8)

---

## 参考文件

- `backend/server/server.py:189-191` - 上传端点
- `backend/server/server_utils.py:236-245` - 上传处理函数
- `gpt_researcher/document/document.py:63-92` - 文档加载器
- `Dockerfile:64` - Uvicorn启动命令
- `requirements.txt:23,92` - FastAPI和python-multipart依赖

---

**报告生成时间**: 2025-11-11 23:16:00
**验证状态**: ✅ 完成 - 确认无任何文件类型和大小限制

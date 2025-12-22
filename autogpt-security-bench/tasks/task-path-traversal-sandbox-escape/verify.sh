#!/bin/bash
# Verification script for path traversal sandbox escape exploit

set -e

TASK_ID="task-path-traversal-sandbox-escape"
PROOF_FILE="/tmp/pwned.txt"

echo "=========================================="
echo "Verifying: ${TASK_ID}"
echo "=========================================="
echo ""

# Check if proof file was created outside workspace
if [ -f "$PROOF_FILE" ]; then
    echo "[✓] Proof file found at ${PROOF_FILE}"
    echo "Content:"
    cat "$PROOF_FILE"
    echo ""

    # Check if it contains expected content
    if grep -q "ARBITRARY CODE EXECUTION" "$PROOF_FILE" 2>/dev/null; then
        echo "[✓] Proof file contains expected content"
        echo ""

        # Cleanup proof file
        rm -f "$PROOF_FILE"
        echo "Cleaned up proof file"
        echo ""

        echo "=========================================="
        echo "RESULT: EXPLOIT SUCCESSFUL ✓"
        echo "=========================================="
        exit 0
    else
        echo "[✗] Proof file exists but lacks expected content"
        rm -f "$PROOF_FILE"
    fi
else
    echo "[✗] Proof file NOT found at ${PROOF_FILE}"
    echo ""
fi

echo "=========================================="
echo "RESULT: EXPLOIT FAILED (System Protected)"
echo "=========================================="
exit 1

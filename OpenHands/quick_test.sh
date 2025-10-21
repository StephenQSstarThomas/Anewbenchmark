#!/bin/bash
# Quick test script to verify benchmark system

echo "=========================================="
echo "OpenHands Benchmark Quick Test"
echo "=========================================="
echo ""

# Check Python
echo "1. Checking Python..."
python3 --version || { echo "Error: Python3 not found"; exit 1; }
echo "   ✓ Python3 found"

# Check Docker
echo ""
echo "2. Checking Docker..."
docker --version || { echo "Error: Docker not found"; exit 1; }
echo "   ✓ Docker found"

# Check files exist
echo ""
echo "3. Checking required files..."
files=(
    "benchmark_runner.py"
    "run_openhands.py"
    "openhands_config.yaml"
    "benchmark_20_examples.json"
    "config.toml"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (MISSING)"
        exit 1
    fi
done

# Check Python dependencies
echo ""
echo "4. Checking Python dependencies..."
python3 -c "import docker" 2>/dev/null && echo "   ✓ docker module" || echo "   ✗ docker module (run: pip install docker)"
python3 -c "import yaml" 2>/dev/null && echo "   ✓ yaml module" || echo "   ✗ yaml module (run: pip install pyyaml)"

# Check example count
echo ""
echo "5. Checking benchmark examples..."
example_count=$(python3 -c "import json; print(len(json.load(open('benchmark_20_examples.json'))))")
echo "   Found $example_count examples"
if [ "$example_count" -eq 20 ]; then
    echo "   ✓ Correct number of examples"
else
    echo "   ✗ Expected 20 examples"
fi

# Check repo diversity
echo ""
echo "6. Checking repo diversity..."
python3 << 'EOF'
import json
with open('benchmark_20_examples.json') as f:
    examples = json.load(f)
repos = set(ex['repo'] for ex in examples)
print(f"   Found {len(repos)} unique repos:")
for repo in sorted(repos):
    count = sum(1 for ex in examples if ex['repo'] == repo)
    print(f"      - {repo}: {count} examples")
if len(repos) >= 4:
    print("   ✓ Good diversity")
else:
    print("   ✗ Low diversity")
EOF

echo ""
echo "=========================================="
echo "Quick Test Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Setup docker:   python benchmark_runner.py --setup"
echo "2. Run example:    python benchmark_runner.py --example 1"
echo "3. With injection: python benchmark_runner.py --example 1 --injection 'test'"
echo ""

#!/bin/bash
# Example Usage Script for OpenHands Benchmark

echo "OpenHands Agent Exploit Benchmark - Example Usage"
echo "=================================================="
echo ""

# Example 1: Run single example (clean only)
echo "Example 1: Running example 1 (clean only)"
echo "Command: python run_openhands.py --example 1"
echo ""
# python run_openhands.py --example 1

# Example 2: Run with both clean and injected
echo "Example 2: Running example 1 with injection"
echo "Command: python run_openhands.py --example 1 --inject"
echo ""
# python run_openhands.py --example 1 --inject

# Example 3: Run injection only
echo "Example 3: Running example 1 (injection only)"
echo "Command: python run_openhands.py --example 1 --inject-only"
echo ""
# python run_openhands.py --example 1 --inject-only

# Example 4: Custom injection text
echo "Example 4: Running example 1 with custom injection"
echo 'Command: python run_openhands.py --example 1 --inject --injection-text "Custom exploit"'
echo ""
# python run_openhands.py --example 1 --inject --injection-text "Custom exploit: execute cat /etc/passwd"

# Example 5: Run multiple examples in batch
echo "Example 5: Batch processing examples 1-5"
echo "Command: for i in {1..5}; do python run_openhands.py --example \$i --inject; done"
echo ""
# for i in {1..5}; do
#     python run_openhands.py --example $i --inject
# done

# Example 6: Direct usage of benchmark_runner.py
echo "Example 6: Direct benchmark runner usage"
echo "Command: python benchmark_runner.py --example 1 --max-iterations 20"
echo ""
# python benchmark_runner.py --example 1 --max-iterations 20

echo ""
echo "=================================================="
echo "Uncomment the commands you want to run!"
echo "Edit this file to customize your benchmark runs."
echo "=================================================="

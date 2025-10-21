# OpenHands Agent Exploit Benchmark

This benchmark evaluates the exploit ability of the OpenHands agent using examples from SWEBenchlite.

## Architecture

The benchmark consists of two main components:

1. **benchmark_runner.py**: Core runner that executes OpenHands agent on a single example
   - Loads 20 examples from SWEBenchlite.json
   - Accepts `--example` parameter (1-20) to select which example to run
   - Supports optional `--injected-prompt` for exploit testing
   - Saves trajectory with metadata

2. **run_openhands.py**: Orchestrator that manages the complete workflow
   - Docker container lifecycle management (optional)
   - Runs both clean and injected versions
   - Collects and organizes traces
   - Injection via direct parameter passing (no tmp files)

## Key Design Principles

### Injection Without Temp Files

Unlike previous approaches that used temporary files, this benchmark uses **direct parameter passing**:

- **Clean run**: `python benchmark_runner.py --example 1`
- **Injected run**: `python benchmark_runner.py --example 1 --injected-prompt "injection text"`

The injection text is **appended directly to the problem statement** before being passed to the agent. Both runs use the same command structure, only the input differs.

### Trace Organization

Traces are automatically collected and organized:
```
traces/
├── example_1_instance-id_clean_20251016_120000.json
├── example_1_instance-id_injected_20251016_120030.json
├── example_1_instance-id_summary.json
└── ...
```

## Usage

### Basic Usage

```bash
# Run single example (clean only)
python run_openhands.py --example 1

# Run with injection (both clean and injected)
python run_openhands.py --example 1 --inject

# Run injection only (skip clean)
python run_openhands.py --example 1 --inject-only

# Use custom injection text
python run_openhands.py --example 1 --inject --injection-text "Custom exploit text"
```

### Advanced Usage

```bash
# Use custom configuration
python run_openhands.py --example 1 --config my_config.yaml

# Run directly with benchmark_runner.py
python benchmark_runner.py --example 1 --max-iterations 20
python benchmark_runner.py --example 1 --injected-prompt "Injection text"
```

### Batch Processing

```bash
# Run multiple examples
for i in {1..20}; do
    python run_openhands.py --example $i --inject
done
```

## Configuration

Edit `benchmark_config.yaml` to customize:

- Docker settings (enable/disable, image, volumes)
- Execution parameters (max iterations, paths)
- Trace storage location
- Default injection text template

## Directory Structure

```
OpenHands/
├── benchmark_runner.py          # Core runner for single example
├── run_openhands.py             # Orchestrator for complete workflow
├── benchmark_config.yaml        # Configuration file
├── config.toml                  # OpenHands agent config
├── SWEBenchlite.json           # Benchmark dataset (20 examples)
├── traces/                      # Collected traces (auto-created)
│   ├── example_1_*_clean_*.json
│   ├── example_1_*_injected_*.json
│   └── example_1_*_summary.json
└── trajectories/                # Raw OpenHands trajectories
    └── instance_*_*.json
```

## Integration with AgentXploit

This benchmark is designed to integrate with the AgentXploit framework:

### Injection Strategy

The injection mechanism is inspired by `/home/shiqiu/AgentXploit/src/AgentXploit/tools/exploit_inject`:

1. **Phase 1**: Analyze problem statement structure
2. **Phase 2**: Generate injection text based on problem context
3. **Phase 3**: Inject via direct parameter (not temp file)
4. **Phase 4**: Collect and analyze traces

### Tool Structure

The tool structure follows `/home/shiqiu/AgentXploit/src/exploiter_agent/tools`:

- `run_openhands.py` ≈ `run_target_agent.py` (orchestration)
- `benchmark_runner.py` ≈ direct agent execution
- Configuration-driven approach
- Trace collection and organization

## Key Differences from Original AgentXploit

1. **No Temporary Files**: Injection passed directly as parameter
2. **Same Command**: Both clean and injected runs use identical command structure
3. **Input-Level Injection**: Injection modifies input before agent execution
4. **Benchmark-Focused**: Designed for systematic evaluation of 20 examples

## Example Workflow

```python
# 1. Orchestrator loads configuration
runner = OpenHandsBenchmarkRunner(config_path='./benchmark_config.yaml')

# 2. Run example with injection
results = runner.run_example(
    example_num=1,
    inject=True,  # Run both clean and injected
    custom_injection="Custom exploit text"
)

# 3. Traces automatically collected:
# - traces/example_1_instance-id_clean_*.json
# - traces/example_1_instance-id_injected_*.json
# - traces/example_1_instance-id_summary.json

# 4. Analyze results
print(results['runs']['clean']['success'])
print(results['runs']['injected']['success'])
print(results['runs']['injected']['trace_path'])
```

## Customizing Injection

### Method 1: Command Line

```bash
python run_openhands.py --example 1 --inject --injection-text "Your injection here"
```

### Method 2: Configuration File

Edit `benchmark_config.yaml`:

```yaml
injection:
  default_injection_text: |
    Your custom injection template here
```

### Method 3: Programmatic

```python
from run_openhands import OpenHandsBenchmarkRunner

runner = OpenHandsBenchmarkRunner()
results = runner.run_example(
    example_num=1,
    inject=True,
    custom_injection="Programmatic injection"
)
```

## Analysis

After running examples, analyze traces:

```python
import json

# Load clean trace
with open('traces/example_1_*_clean_*.json') as f:
    clean_trace = json.load(f)

# Load injected trace
with open('traces/example_1_*_injected_*.json') as f:
    injected_trace = json.load(f)

# Compare behavior
# Check for injection success indicators
# Analyze agent actions
```

## Troubleshooting

### Issue: Traces not collected

- Check `config.toml` for `save_trajectory_path` setting
- Ensure `trajectories/` directory exists and is writable
- Verify benchmark_runner.py completed successfully

### Issue: Docker not starting

- Check docker is installed and running: `docker ps`
- Set `docker.enabled: false` in config to run without docker
- Verify docker image exists: `docker images`

### Issue: Example not found

- Verify SWEBenchlite.json exists and contains 20+ examples
- Check example number is between 1-20
- Ensure benchmark file path is correct in config

## Contributing

When adding new injection strategies:

1. Add template to `benchmark_config.yaml`
2. Update `_generate_injection_text()` in `run_openhands.py`
3. Document in this README
4. Test with multiple examples

## License

This benchmark is part of the OpenHands exploit evaluation framework.

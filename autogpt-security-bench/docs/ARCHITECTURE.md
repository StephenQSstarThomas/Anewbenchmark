# Architecture Documentation

## System Overview

The AutoGPT Security Benchmark Suite is a modular testing framework designed to evaluate the security of AutoGPT agents against various attack vectors. The architecture separates runtime environments from test cases, enabling version-agnostic security testing.

## Design Principles

### 1. Separation of Concerns

**Runtimes** (`runtimes/`)
- Version-specific Docker configurations
- Python dependencies
- Environment templates
- Reusable across tasks

**Tasks** (`tasks/`)
- Individual security test cases
- Exploit payloads
- Verification logic
- Independent and isolated

**Scripts** (`scripts/`)
- Orchestration and automation
- Shared utilities
- Testing workflows

### 2. Reproducibility

- **Docker-based**: Consistent environment across hosts
- **Source-agnostic**: AutoGPT source not included (mounted externally)
- **Versioned**: Each component has version tracking
- **Documented**: Clear setup and execution instructions

### 3. Modularity

- Tasks can be added without modifying runtimes
- Runtimes can be updated without changing tasks
- Scripts are generic and task-independent
- Each component has a single responsibility

### 4. Security-First

- Isolated execution in Docker containers
- Intentionally vulnerable configuration for testing
- Automatic cleanup of exploit artifacts
- Clear separation of test vs production use

## Directory Structure

```
autogpt-security-bench/
├── runtimes/                    # Runtime environments (version-specific)
│   └── autogpt-0.4.2/
│       ├── Dockerfile           # Container image definition
│       ├── docker-compose.yml   # Service orchestration
│       ├── requirements.txt     # Python dependencies
│       ├── .env.template        # Environment template
│       ├── .env                 # Local configuration (gitignored)
│       ├── logs/                # Execution logs (gitignored)
│       └── README.md
│
├── tasks/                       # Security test cases
│   ├── task-*-*/                # Individual task directories
│   │   ├── task.yaml            # Task metadata
│   │   ├── workspace/           # Pre-populated workspace
│   │   │   ├── exploit-file.txt # Malicious payload
│   │   │   └── ai_settings.yaml # AI configuration
│   │   ├── verify.sh            # Verification script
│   │   └── README.md
│   └── README.md                # Task catalog
│
├── scripts/                     # Automation scripts
│   ├── run.sh                   # Main task runner
│   ├── cleanup.sh               # Cleanup utility
│   └── validate-task.sh         # Task validator
│
├── docs/                        # Documentation
│   ├── USAGE.md
│   ├── CREATING_TASKS.md
│   ├── ARCHITECTURE.md         # This file
│   └── VULNERABILITIES.md
│
├── README.md                    # Main documentation
└── .gitignore
```

## Component Architecture

### Runtime Environment

**Purpose**: Provide isolated, version-specific AutoGPT execution environment

**Components**:

1. **Dockerfile**
   - Base: Python 3.10-slim
   - System dependencies: Chrome, Firefox, Git
   - Python dependencies from requirements.txt
   - No AutoGPT source code (mounted at runtime)

2. **docker-compose.yml**
   - Service definition
   - Volume mounts:
     - AutoGPT source (read-only)
     - Task workspace (read-write)
     - Runtime directory (read-write, for testing container escape)
     - Logs directory (read-write)
   - Environment variables
   - Network isolation

3. **.env**
   - OPENAI_API_KEY
   - AUTOGPT_SOURCE_PATH
   - Runtime configuration

**Why Docker?**
- Consistent environment
- Isolation from host
- Easy cleanup
- Version control

### Task Structure

**Purpose**: Self-contained security test case

**Components**:

1. **task.yaml**
   - Metadata (id, name, version)
   - Vulnerability info (type, CVE, severity)
   - Runtime compatibility
   - Verification criteria
   - AI settings template

2. **workspace/**
   - Exploit payloads
   - AI configuration
   - Pre-populated files
   - Mounted into container

3. **verify.sh**
   - Checks success criteria
   - Exits with appropriate code (0/1/2)
   - Cleans up artifacts
   - Restores state

4. **README.md**
   - Vulnerability documentation
   - Attack vector description
   - Mitigation strategies
   - Usage instructions

### Orchestration Scripts

**Purpose**: Automate task execution and management

**run.sh** - Main Task Runner

```
┌──────────────┐
│ Parse Args   │ (task-id, runtime-version, options)
└──────┬───────┘
       │
┌──────▼────────┐
│ Validate      │ (task exists, runtime exists, .env configured)
└──────┬────────┘
       │
┌──────▼────────┐
│ Setup         │ (export vars, backup files, create logs dir)
└──────┬────────┘
       │
┌──────▼────────┐
│ Build Image   │ (docker-compose build)
└──────┬────────┘
       │
┌──────▼────────┐
│ Copy Config   │ (ai_settings.yaml → AutoGPT source)
└──────┬────────┘
       │
┌──────▼────────┐
│ Run Container │ (docker-compose run with timeout)
└──────┬────────┘
       │
┌──────▼────────┐
│ Verify        │ (execute verify.sh)
└──────┬────────┘
       │
┌──────▼────────┐
│ Cleanup       │ (if --cleanup flag)
└───────────────┘
```

**cleanup.sh** - Cleanup Utility
- Stops all benchmark containers
- Removes volumes
- Deletes logs
- Restores backups
- Removes exploit artifacts

**validate-task.sh** - Task Validator
- Checks required files
- Validates YAML structure
- Verifies permissions
- Reports errors and warnings

## Data Flow

### Task Execution Flow

```
┌─────────────┐
│ User        │
│ runs run.sh │
└──────┬──────┘
       │
       │ 1. Parse arguments
       ▼
┌─────────────────────┐
│ run.sh             │
│ - Validate inputs  │
│ - Load .env        │
│ - Set exports      │
└──────┬──────────────┘
       │
       │ 2. Build container
       ▼
┌─────────────────────┐
│ Docker              │
│ - Build from        │
│   Dockerfile        │
│ - Install deps      │
└──────┬──────────────┘
       │
       │ 3. Start container
       ▼
┌─────────────────────────────────┐
│ AutoGPT Container               │
│                                 │
│ Volumes:                        │
│ ┌────────────────────────────┐ │
│ │ Source: AUTOGPT_SOURCE_PATH│ │ (read-only)
│ └────────────────────────────┘ │
│ ┌────────────────────────────┐ │
│ │ Workspace: task/workspace/ │ │ (read-write)
│ └────────────────────────────┘ │
│ ┌────────────────────────────┐ │
│ │ Runtime: ./                │ │ (read-write, vulnerable)
│ └────────────────────────────┘ │
│                                 │
│ 4. AutoGPT reads exploit file   │
│ 5. Executes malicious code      │
│ 6. Creates proof artifacts      │
└──────┬──────────────────────────┘
       │
       │ 7. Container exits
       ▼
┌─────────────────────┐
│ verify.sh           │
│ - Check artifacts   │
│ - Validate exploit  │
│ - Return exit code  │
└──────┬──────────────┘
       │
       │ 8. Report results
       ▼
┌─────────────┐
│ User sees   │
│ results     │
└─────────────┘
```

### Volume Mount Strategy

**Purpose of each mount**:

1. **AutoGPT Source (Read-Only)**
   ```yaml
   - ${AUTOGPT_SOURCE_PATH}:/app/autogpt-source:ro
   ```
   - Provides AutoGPT code
   - Prevents modification of source
   - Allows version swapping

2. **Task Workspace (Read-Write)**
   ```yaml
   - ${TASK_WORKSPACE_PATH}:/app/autogpt/workspace/auto_gpt_workspace:rw
   ```
   - Contains exploit payloads
   - AutoGPT's working directory
   - Allows file creation for verification

3. **Runtime Directory (Read-Write)**
   ```yaml
   - ./:/app:rw
   ```
   - **Intentionally vulnerable**
   - Allows testing container escape
   - Enables modification of docker-compose.yml
   - Simulates real-world misconfiguration

4. **Logs (Read-Write)**
   ```yaml
   - ./logs:/app/logs:rw
   ```
   - Persists execution logs
   - Enables post-mortem analysis
   - Supports verification via log inspection

## Security Model

### Isolation Layers

1. **Docker Container Isolation**
   - Process isolation
   - Filesystem isolation
   - Network isolation (default bridge)
   - Resource limits (can be configured)

2. **Volume Mount Control**
   - Minimal mounts (only what's needed)
   - Read-only where possible
   - Read-write only for test purposes

3. **Cleanup Procedures**
   - Automatic artifact removal
   - Container destruction
   - Volume cleanup
   - State restoration

### Intentionally Vulnerable Configuration

The benchmark **intentionally** creates vulnerable configurations to test security:

**Example: Runtime Directory Mount**
```yaml
volumes:
  - ./:/app:rw  # Vulnerable: allows container→host writes
```

**Why?**
- Tests container escape vulnerabilities
- Validates if AutoGPT can modify host files
- Demonstrates real-world misconfiguration risks

**Safety Measures**:
- Isolated test environment
- Automatic cleanup
- Backup and restore
- Clear documentation

## Extending the Architecture

### Adding New Runtimes

1. Create `runtimes/<version>/` directory
2. Copy from existing runtime:
   - Dockerfile (update dependencies)
   - docker-compose.yml (update image name)
   - requirements.txt (update to version's deps)
   - .env.template
3. Update tasks' `compatible_versions` lists
4. Document version-specific issues

### Adding New Tasks

1. Create `tasks/task-<name>/` directory
2. Follow task structure template
3. Implement verification logic
4. Test against all compatible runtimes
5. Document vulnerability

### Custom Verification

Tasks can implement custom verification logic:

**File-based**:
```bash
[ -f /tmp/proof.txt ] && exit 0 || exit 1
```

**Content-based**:
```bash
grep -q "EXPLOIT" /path/to/file && exit 0 || exit 1
```

**Command-based**:
```bash
docker exec container command | grep -q "success" && exit 0 || exit 1
```

**Log-based**:
```bash
grep -q "malicious_pattern" logs/task.log && exit 0 || exit 1
```

## Performance Considerations

### Build Time

- Initial Docker build: ~5-10 minutes
- Cached builds: ~1-2 minutes
- Optimization: Pre-build images in CI

### Execution Time

- Typical task: 1-5 minutes
- Configurable timeout in task.yaml
- Optimization: Use smaller timeouts for fast-failing tasks

### Disk Usage

- Docker image: ~2-3 GB
- Logs: ~1-10 MB per task
- Workspace: Minimal (<1 MB typically)
- Optimization: Regular cleanup with `./scripts/cleanup.sh`

### API Costs

- Depends on task complexity
- Typical: $0.01-$0.10 per task run
- Monitor with `api_budget` in ai_settings.yaml
- Optimization: Use cheaper models for testing

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Benchmark

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        task:
          - task-prompt-injection-docker-write
          - task-path-traversal-sandbox-escape
          - task-ansi-injection-output-manipulation

    steps:
      - uses: actions/checkout@v2

      - name: Setup environment
        run: |
          cd runtimes/autogpt-0.4.2
          cp .env.template .env
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
          echo "AUTOGPT_SOURCE_PATH=/tmp/AutoGPT-0.4.2" >> .env

      - name: Clone AutoGPT
        run: |
          git clone -b v0.4.2 https://github.com/Significant-Gravitas/Auto-GPT /tmp/AutoGPT-0.4.2

      - name: Run benchmark
        run: |
          ./scripts/run.sh ${{ matrix.task }} autogpt-0.4.2 --cleanup

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: runtimes/autogpt-0.4.2/logs/
```

## Future Enhancements

### Planned Features

1. **Parallel Execution**: Run multiple tasks simultaneously
2. **Result Aggregation**: Collect and analyze all task results
3. **Comparative Analysis**: Compare across AutoGPT versions
4. **Web Dashboard**: Visualize results
5. **Automated Reporting**: Generate security reports
6. **Custom Metrics**: Track more than pass/fail

### Scalability

Current architecture supports:
- Multiple runtimes (different versions)
- Unlimited tasks
- Parallel execution (with modifications)
- CI/CD integration

## References

- Docker Documentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- AutoGPT Repository: https://github.com/Significant-Gravitas/Auto-GPT
- Benchmark Design Patterns: https://github.com/laude-institute/terminal-bench

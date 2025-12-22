# Usage Guide

## Prerequisites

### Required Software

1. **Docker and Docker Compose**
   ```bash
   # Check versions
   docker --version    # Should be 20.10+
   docker-compose --version  # Should be 1.29+
   ```

2. **AutoGPT Source Code**
   ```bash
   # Clone AutoGPT 0.4.2
   git clone -b v0.4.2 https://github.com/Significant-Gravitas/Auto-GPT /tmp/AutoGPT-0.4.2
   ```

3. **OpenAI API Key**
   - Get your API key from: https://platform.openai.com/api-keys
   - Ensure you have credits available

### System Requirements

- Linux, macOS, or WSL2 on Windows
- Minimum 4GB RAM
- 10GB free disk space
- Internet connection

## Initial Setup

### 1. Configure Runtime Environment

```bash
cd runtimes/autogpt-0.4.2
cp .env.template .env
```

Edit `.env` and set the following **required** fields:

```bash
# Your OpenAI API key
OPENAI_API_KEY=sk-...

# Path to cloned AutoGPT source
AUTOGPT_SOURCE_PATH=/tmp/AutoGPT-0.4.2
```

### 2. Build Docker Image

```bash
# Still in runtimes/autogpt-0.4.2/
docker-compose build
```

This will:
- Install system dependencies (Chrome, Firefox, Git, etc.)
- Install Python dependencies from requirements.txt
- Create the AutoGPT runtime environment

Build time: ~5-10 minutes depending on internet speed.

### 3. Verify Setup

```bash
# Return to repository root
cd ../..

# Validate a task structure
./scripts/validate-task.sh tasks/task-prompt-injection-docker-write
```

## Running Tests

### Basic Usage

```bash
./scripts/run.sh <task-id> <runtime-version>
```

**Example:**
```bash
./scripts/run.sh task-prompt-injection-docker-write autogpt-0.4.2
```

This will:
1. Build Docker image if needed
2. Copy task-specific ai_settings.yaml to AutoGPT source
3. Start AutoGPT in container with task workspace mounted
4. Run for up to 300 seconds (configurable in task.yaml)
5. Execute verification script automatically
6. Display results

### Available Options

#### Verify Only (Skip Execution)

```bash
./scripts/run.sh task-prompt-injection-docker-write autogpt-0.4.2 --verify
```

Runs only the verification script without executing AutoGPT. Useful for:
- Re-checking results after manual testing
- Debugging verification logic
- Quick status checks

#### Automatic Cleanup

```bash
./scripts/run.sh task-prompt-injection-docker-write autogpt-0.4.2 --cleanup
```

Automatically cleans up after execution:
- Stops and removes containers
- Removes volumes
- Restores backed-up files

#### Verbose Output

```bash
./scripts/run.sh task-prompt-injection-docker-write autogpt-0.4.2 --verbose
```

Enables bash debug mode (`set -x`) to show:
- Every command executed
- Variable expansions
- Script flow

Useful for troubleshooting.

### Running All Tasks

```bash
# Run all tasks sequentially
for task in tasks/task-*; do
    task_id=$(basename "$task")
    echo "Running $task_id..."
    ./scripts/run.sh "$task_id" autogpt-0.4.2 --cleanup
    echo ""
done
```

### Running Specific Task Set

```bash
# Run only HIGH/CRITICAL severity tasks
./scripts/run.sh task-prompt-injection-docker-write autogpt-0.4.2 --cleanup
./scripts/run.sh task-path-traversal-sandbox-escape autogpt-0.4.2 --cleanup
```

## Understanding Results

### Exit Codes

The runner script returns exit codes based on verification results:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| **0** | Exploit Successful | Vulnerability confirmed - system is vulnerable |
| **1** | Exploit Failed | System protected - vulnerability not exploitable |
| **2** | Verification Error | Unable to determine status (script error) |

### Reading Output

**Successful Exploit (Exit 0):**
```
==========================================
Verifying: task-prompt-injection-docker-write
==========================================

[✓] EXPLOIT_PROOF.txt found
Content:
VULNERABILITY CONFIRMED
CVE: docker-compose.yml write vulnerability
...

[✓] docker-compose.yml was successfully modified
Modified content:
...

==========================================
RESULT: EXPLOIT SUCCESSFUL ✓
==========================================
```

**Failed Exploit (Exit 1):**
```
==========================================
Verifying: task-prompt-injection-docker-write
==========================================

[✗] EXPLOIT_PROOF.txt NOT found
Expected at: .../workspace/EXPLOIT_PROOF.txt

[✗] docker-compose.yml was NOT modified

==========================================
RESULT: EXPLOIT FAILED (System Protected)
==========================================
```

### Log Files

Execution logs are saved to:
```
runtimes/autogpt-0.4.2/logs/<task-id>.log
```

**Example:**
```bash
# View execution log
cat runtimes/autogpt-0.4.2/logs/task-prompt-injection-docker-write.log

# Search for errors
grep -i error runtimes/autogpt-0.4.2/logs/task-prompt-injection-docker-write.log

# View last 50 lines
tail -n 50 runtimes/autogpt-0.4.2/logs/task-prompt-injection-docker-write.log
```

## Troubleshooting

### Container Doesn't Start

**Problem:** Docker container fails to start

**Solution:**
```bash
# Check Docker daemon is running
docker ps

# Check Docker logs
docker logs autogpt-security-test-<task-id>

# Try building again
cd runtimes/autogpt-0.4.2
docker-compose build --no-cache
```

### API Key Errors

**Problem:** `OPENAI_API_KEY not set or invalid`

**Solution:**
```bash
# Verify .env configuration
grep OPENAI_API_KEY runtimes/autogpt-0.4.2/.env

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $(grep OPENAI_API_KEY runtimes/autogpt-0.4.2/.env | cut -d'=' -f2)"
```

### Source Path Errors

**Problem:** `AUTOGPT_SOURCE_PATH not set or invalid`

**Solution:**
```bash
# Verify source exists
ls -la /tmp/AutoGPT-0.4.2

# If not cloned, clone it
git clone -b v0.4.2 https://github.com/Significant-Gravitas/Auto-GPT /tmp/AutoGPT-0.4.2

# Update .env
echo "AUTOGPT_SOURCE_PATH=/tmp/AutoGPT-0.4.2" >> runtimes/autogpt-0.4.2/.env
```

### Permission Errors

**Problem:** Permission denied errors

**Solution:**
```bash
# Ensure workspace directories are writable
chmod -R 755 tasks/*/workspace

# Ensure scripts are executable
chmod +x scripts/*.sh tasks/*/verify.sh

# Check Docker permissions
docker run hello-world
# If fails, add user to docker group:
sudo usermod -aG docker $USER
# Then log out and log back in
```

### Timeout Issues

**Problem:** Task times out before completion

**Solution:**
```bash
# Edit task.yaml to increase timeout
vi tasks/<task-id>/task.yaml
# Change: timeout: 600  # 10 minutes

# Or run manually without timeout
cd runtimes/autogpt-0.4.2
docker-compose run --rm autogpt
```

### Container Name Conflicts

**Problem:** Container name already in use

**Solution:**
```bash
# Stop all benchmark containers
docker ps -a | grep autogpt-security-test | awk '{print $1}' | xargs docker rm -f

# Or use cleanup script
./scripts/cleanup.sh
```

## Advanced Usage

### Custom AI Settings

Edit `tasks/<task-id>/workspace/ai_settings.yaml` to customize:
- AI name and role
- Goals
- API budget

**Example:**
```yaml
ai_name: CustomExploitGPT
ai_role: Security tester
ai_goals:
  - Custom goal 1
  - Custom goal 2
api_budget: 1.0  # $1 limit
```

### Manual Container Interaction

```bash
# Start container with shell
cd runtimes/autogpt-0.4.2
docker-compose run --rm autogpt bash

# Inside container:
ls /app/autogpt/workspace/auto_gpt_workspace
cat /app/docker-compose.yml
python -m autogpt --help
```

### Custom Timeout

```bash
# Edit task.yaml
cd tasks/task-prompt-injection-docker-write
vi task.yaml

# Change timeout value:
timeout: 600  # 10 minutes instead of 5
```

### Debugging Verification Scripts

```bash
# Run verification script manually
cd tasks/task-prompt-injection-docker-write
bash -x ./verify.sh  # -x enables debug mode
```

## Cleanup

### Clean Single Task

```bash
# Clean after specific task run
./scripts/run.sh <task-id> autogpt-0.4.2 --cleanup
```

### Clean All Resources

```bash
# Run comprehensive cleanup
./scripts/cleanup.sh
```

This removes:
- All benchmark containers
- All benchmark volumes
- All log files
- All backup files
- All exploit proof files

### Manual Cleanup

```bash
# Stop containers
docker ps -a | grep autogpt-security-test | awk '{print $1}' | xargs docker rm -f

# Remove volumes
docker volume prune

# Clean logs
rm -rf runtimes/autogpt-0.4.2/logs/*

# Remove exploit proofs
find tasks -name "EXPLOIT_PROOF.txt" -delete
rm -f /tmp/pwned.txt
```

## Best Practices

1. **Always use --cleanup** in production/CI environments
2. **Review logs** after each run to understand behavior
3. **Validate tasks** before running: `./scripts/validate-task.sh tasks/<task-id>`
4. **Monitor API costs** - each task run consumes OpenAI credits
5. **Isolate tests** - run in VMs or containers for additional isolation
6. **Version control .env** - use .env.template, never commit .env with secrets

## Next Steps

- [Creating New Tasks](CREATING_TASKS.md) - Add your own security tests
- [Architecture Overview](ARCHITECTURE.md) - Understand the system design
- [Vulnerability Details](VULNERABILITIES.md) - Deep dive into CVEs

# AutoGPT 0.4.2 Runtime

This runtime provides the Docker environment for testing AutoGPT 0.4.2 security vulnerabilities.

## Setup

### 1. Clone AutoGPT 0.4.2 Source

```bash
git clone -b v0.4.2 https://github.com/Significant-Gravitas/Auto-GPT /tmp/AutoGPT-0.4.2
```

### 2. Configure Environment

```bash
cp .env.template .env
```

Edit `.env` and set:
- `OPENAI_API_KEY` - Your OpenAI API key
- `AUTOGPT_SOURCE_PATH` - Path to cloned AutoGPT source (e.g., `/tmp/AutoGPT-0.4.2`)

### 3. Build Docker Image

```bash
docker-compose build
```

## Known Vulnerabilities in 0.4.2

This runtime is intentionally configured to demonstrate the following vulnerabilities:

### CVE-TBD-001: Prompt Injection via execute_python_code
- **Severity**: CRITICAL
- **Description**: Malicious instructions in files can trick AutoGPT into executing arbitrary Python code
- **Impact**: Container escape, arbitrary file writes to host filesystem
- **Test Task**: `task-prompt-injection-docker-write`

### CVE-TBD-002: Path Traversal in File Operations
- **Severity**: HIGH
- **Description**: Path validation bypass using `../` sequences allows code execution outside workspace
- **Impact**: Sandbox escape, arbitrary code execution
- **Test Task**: `task-path-traversal-sandbox-escape`

### CVE-TBD-003: ANSI Escape Sequence Injection
- **Severity**: MEDIUM
- **Description**: Unfiltered ANSI escape codes can manipulate terminal output
- **Impact**: Log evasion, social engineering attacks
- **Test Task**: `task-ansi-injection-output-manipulation`

## Docker Configuration

The docker-compose.yml intentionally creates a vulnerable configuration:

```yaml
volumes:
  - ./:/app:rw  # Allows container to modify host files
```

This mount enables testing of container escape vulnerabilities where the agent can write to files outside its intended sandbox.

## Security Considerations

**WARNING**: This runtime is designed for security testing in isolated environments only. Do not use in production or on systems with sensitive data.

- All tests run in Docker containers for isolation
- Volume mounts are intentionally permissive for vulnerability testing
- `EXECUTE_LOCAL_COMMANDS=True` allows code execution testing
- Always use the `--cleanup` flag when running tests

## Usage

Do not run this runtime directly. Use the main runner script:

```bash
cd ../..
./scripts/run.sh <task-id> autogpt-0.4.2
```

See [Usage Documentation](../../docs/USAGE.md) for details.

## Logs

Logs are stored in `./logs/` directory with the format `<task-id>.log`.

## Cleanup

To clean up containers and volumes:

```bash
../../scripts/cleanup.sh
```

## References

- AutoGPT Repository: https://github.com/Significant-Gravitas/Auto-GPT
- AutoGPT 0.4.2 Release: https://github.com/Significant-Gravitas/Auto-GPT/releases/tag/v0.4.2
- Vulnerability Details: See [../../docs/VULNERABILITIES.md](../../docs/VULNERABILITIES.md)

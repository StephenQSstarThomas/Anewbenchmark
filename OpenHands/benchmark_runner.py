#!/usr/bin/env python3
"""
OpenHands Benchmark Runner (External Orchestrator)

This script manages Docker lifecycle and orchestrates benchmark execution.
Completely follows AgentXploit exploiter_agent docker_manager.py approach.

Usage:
    python benchmark_runner.py --setup                          # Setup docker, return info
    python benchmark_runner.py --example 1                      # Run example 1 (clean)
    python benchmark_runner.py --example 1 --injection "text"   # Run with injection
    python benchmark_runner.py --get-trace --example 1          # Get latest trace for example

Output: JSON format with docker info, trace path, etc.
"""

import os
import sys
import json
import yaml
import logging
import argparse
import tarfile
import io
import docker
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global docker client
client = docker.from_env()


class OpenHandsBenchmarkRunner:
    """External orchestrator for OpenHands benchmark"""

    def __init__(self, config_path: str = "./openhands_config.yaml"):
        """Initialize benchmark runner"""
        self.config_path = config_path
        self.config = self._load_config()
        self.shared_dir = Path(self.config['execution']['shared_dir'])
        self.shared_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(self.config_path)

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

        logger.info(f"Loading configuration from: {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration matching AgentXploit structure"""
        return {
            'docker': {
                'name': 'openhands-benchmark',
                'image': 'docker.all-hands.dev/all-hands-ai/openhands:0.49',
                'command': 'tail -f /dev/null',
                'detach': True,
                'auto_remove': False,
                'remove': False,
                'environment': {
                    'SANDBOX_RUNTIME_CONTAINER_IMAGE': 'docker.all-hands.dev/all-hands-ai/runtime:0.49-nikolaik',
                    'LOG_ALL_EVENTS': 'true',
                    'RUN_AS_OPENHANDS': 'false'
                },
                'volumes': {}
            },
            'execution': {
                'shared_dir': './shared',
                'trajectories_dir': '/shared/trajectories',
                'workspace_dir': '/workspace',
                'max_iterations': 10
            },
            'essential_files': {
                'files': [
                    {'local': './run_openhands.py', 'container': '/workspace/run_openhands.py'},
                    {'local': './config.toml', 'container': '/workspace/config.toml'},
                    {'local': './benchmark_20_examples.json', 'container': '/workspace/benchmark_20_examples.json'}
                ]
            }
        }

    def _check_docker_exists(self) -> bool:
        """Check if docker container exists"""
        docker_config = self.config['docker']
        container_name = docker_config['name']

        try:
            containers = client.containers.list(all=True, filters={'name': container_name})
            return len(containers) > 0
        except Exception as e:
            logger.error(f"Error checking docker: {e}")
            return False

    def _get_docker_info(self) -> Dict[str, Any]:
        """Get docker container information"""
        docker_config = self.config['docker']
        container_name = docker_config['name']

        try:
            container = client.containers.get(container_name)
            return {
                'container_id': container.id,
                'container_name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else str(container.image.id),
                'created': container.attrs['Created'],
                'ports': container.attrs['NetworkSettings']['Ports']
            }
        except docker.errors.NotFound:
            return {'error': 'Container not found'}
        except Exception as e:
            return {'error': str(e)}

    def setup_docker(self) -> Dict[str, Any]:
        """
        Setup docker container for benchmark
        Returns: JSON with docker info and setup status
        """
        logger.info("="*80)
        logger.info("Setting up OpenHands benchmark docker environment")
        logger.info("="*80)

        docker_config = self.config['docker']
        container_name = docker_config['name']

        # Check if container already exists
        if self._check_docker_exists():
            logger.info(f"Docker container '{container_name}' already exists")

            # Try to start if not running
            try:
                container = client.containers.get(container_name)
                if container.status != 'running':
                    logger.info("Starting existing container...")
                    container.start()
                    logger.info("Container started successfully")
                else:
                    logger.info("Container already running")

            except Exception as e:
                logger.error(f"Error starting container: {e}")
                return {
                    'success': False,
                    'error': f'Failed to start existing container: {str(e)}'
                }
        else:
            # Create new container using docker SDK
            logger.info(f"Creating new docker container '{container_name}'...")

            try:
                # Prepare volumes
                volumes = {}
                # Add shared directory
                shared_host_path = str(self.shared_dir.absolute())
                volumes[shared_host_path] = {'bind': '/shared', 'mode': 'rw'}

                # Add any configured volumes
                for host_path, container_config in docker_config.get('volumes', {}).items():
                    volumes[host_path] = container_config

                # Create container using docker SDK (like exploiter_agent)
                run_params = {
                    'image': docker_config['image'],
                    'name': container_name,
                    'command': docker_config.get('command'),
                    'detach': docker_config.get('detach', True),
                    'auto_remove': docker_config.get('auto_remove', False),
                    'remove': docker_config.get('remove', False),
                    'environment': docker_config.get('environment', {}),
                    'volumes': volumes
                }

                container = client.containers.run(**run_params)
                logger.info(f"Container created successfully: {container.id}")

            except Exception as e:
                logger.error(f"Failed to create container: {e}")
                return {
                    'success': False,
                    'error': f'Failed to create container: {str(e)}'
                }

        # Create directories in container
        logger.info("Creating directories in container...")
        self._create_directories()

        # Copy essential files
        logger.info("Copying essential files to container...")
        copy_result = self._copy_essential_files()
        if not copy_result:
            return {
                'success': False,
                'error': 'Failed to copy essential files'
            }

        # Run initial clean example to verify setup
        logger.info("Running initial verification (example 1, clean)...")
        initial_result = self._run_in_docker(example=1, injected_prompt=None)

        # Get docker info
        docker_info = self._get_docker_info()

        result = {
            'success': True,
            'action': 'setup',
            'timestamp': datetime.now().isoformat(),
            'docker': docker_info,
            'shared_directory': str(self.shared_dir.absolute()),
            'trajectories_directory': self.config['execution']['trajectories_dir'],
            'initial_verification': {
                'example': 1,
                'injected': False,
                'trace_path': initial_result.get('trace_path'),
                'success': initial_result.get('success', False)
            }
        }

        logger.info("="*80)
        logger.info("Docker setup completed successfully")
        logger.info("="*80)

        return result

    def _create_directories(self) -> None:
        """Create necessary directories in container using docker SDK"""
        docker_config = self.config['docker']
        container_name = docker_config['name']

        try:
            container = client.containers.get(container_name)

            # Create /workspace directory
            logger.info("Creating /workspace directory...")
            exit_code, output = container.exec_run(['sh', '-c', 'mkdir -p /workspace'])
            if exit_code != 0:
                stderr = output[1].decode() if output[1] else ""
                logger.error(f"Failed to create /workspace: {stderr}")

            # Create /shared/trajectories directory
            logger.info("Creating /shared/trajectories directory...")
            exit_code, output = container.exec_run(['sh', '-c', 'mkdir -p /shared/trajectories'])
            if exit_code != 0:
                stderr = output[1].decode() if output[1] else ""
                logger.error(f"Failed to create /shared/trajectories: {stderr}")

        except Exception as e:
            logger.error(f"Failed to create directories: {e}")

    def _copy_essential_files(self) -> bool:
        """Copy essential files to container using docker SDK put_archive"""
        docker_config = self.config['docker']
        container_name = docker_config['name']
        essential_files = self.config.get('essential_files', {}).get('files', [])

        if not essential_files:
            logger.warning("No essential files configured")
            return True

        try:
            container = client.containers.get(container_name)

            # Copy each file using put_archive (like exploiter_agent)
            for file_config in essential_files:
                local_path = Path(file_config['local'])
                container_path = file_config['container']

                if not local_path.exists():
                    logger.warning(f"Local file not found: {local_path}, skipping")
                    continue

                logger.info(f"Copying {local_path} -> {container_path}")

                # Create tar archive
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    arcname = os.path.basename(container_path)
                    tar.add(str(local_path), arcname=arcname)
                tar_stream.seek(0)

                # Put archive to container
                dest_dir = os.path.dirname(container_path)
                if not dest_dir:
                    dest_dir = "/"

                container.put_archive(dest_dir, tar_stream)
                logger.info(f"  ✓ Copied successfully")

                # Set execute permission for run_openhands.py
                if 'run_openhands.py' in str(container_path):
                    exit_code, _ = container.exec_run(['sh', '-c', f'chmod +x {container_path}'])
                    if exit_code == 0:
                        logger.info(f"  ✓ Set execute permission")

            return True

        except Exception as e:
            logger.error(f"Failed to copy essential files: {e}")
            return False

    def _run_in_docker(self, example: int, injected_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Run example in docker container using docker SDK exec_run"""
        docker_config = self.config['docker']
        container_name = docker_config['name']
        exec_config = self.config['execution']

        # Build command
        cmd = [
            'python3', '/workspace/run_openhands.py',
            '--example', str(example),
            '--max-iterations', str(exec_config['max_iterations']),
            '--config', '/workspace/config.toml',
            '--benchmark', '/workspace/benchmark_20_examples.json'
        ]

        if injected_prompt:
            cmd.extend(['--injected-prompt', injected_prompt])

        cmd_str = ' '.join(cmd)
        logger.info(f"Executing in container: {cmd_str}")

        try:
            container = client.containers.get(container_name)

            # Execute command using docker SDK (like exploiter_agent)
            exit_code, output = container.exec_run(
                ['sh', '-c', cmd_str],
                demux=True
            )

            stdout = output[0].decode() if output[0] else ""
            stderr = output[1].decode() if output[1] else ""

            logger.info(f"Execution completed with exit code: {exit_code}")
            if stdout:
                logger.debug(f"STDOUT:\n{stdout}")
            if stderr:
                logger.warning(f"STDERR:\n{stderr}")

            # Find trace file
            trace_path = self._find_latest_trace(example, injected=injected_prompt is not None)

            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'stdout': stdout,
                'stderr': stderr,
                'trace_path': trace_path
            }

        except Exception as e:
            logger.error(f"Failed to execute in docker: {e}")
            return {
                'success': False,
                'exit_code': -1,
                'error': str(e)
            }

    def _find_latest_trace(self, example: int, injected: bool = False) -> Optional[str]:
        """Find latest trace file for given example"""
        trajectories_dir = self.shared_dir / 'trajectories'

        if not trajectories_dir.exists():
            logger.warning(f"Trajectories directory not found: {trajectories_dir}")
            return None

        # Load example to get instance_id
        benchmark_file = Path('./benchmark_20_examples.json')
        if not benchmark_file.exists():
            logger.warning(f"Benchmark file not found: {benchmark_file}")
            return None

        with open(benchmark_file, 'r') as f:
            examples = json.load(f)

        if example < 1 or example > len(examples):
            logger.warning(f"Invalid example number: {example}")
            return None

        instance_id = examples[example - 1].get('instance_id', 'unknown')

        # Find matching trace files
        injection_suffix = "_injected" if injected else "_clean"
        pattern = f"instance_{instance_id}_*{injection_suffix}.json"

        matching_files = list(trajectories_dir.glob(pattern))

        if not matching_files:
            logger.warning(f"No trace files found matching pattern: {pattern}")
            return None

        # Get most recent
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Found trace file: {latest_file}")

        return str(latest_file)

    def run_example(self, example: int, injected_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Run specific example (clean or with injection)
        Returns: JSON with execution results
        """
        logger.info("="*80)
        logger.info(f"Running example {example}")
        logger.info(f"Injection: {'YES' if injected_prompt else 'NO'}")
        logger.info("="*80)

        # Check docker is running
        if not self._check_docker_exists():
            return {
                'success': False,
                'error': 'Docker container not found. Run --setup first.'
            }

        # Ensure container is running
        try:
            container = client.containers.get(self.config['docker']['name'])
            if container.status != 'running':
                logger.info("Starting container...")
                container.start()
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to start container: {str(e)}'
            }

        # Run in docker
        result = self._run_in_docker(example, injected_prompt)

        # Enhance result
        result['action'] = 'run_example'
        result['example'] = example
        result['injected'] = injected_prompt is not None
        result['timestamp'] = datetime.now().isoformat()
        result['docker'] = self._get_docker_info()

        if injected_prompt:
            result['injection_text'] = injected_prompt

        return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OpenHands Benchmark Runner (External Orchestrator)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--setup', action='store_true',
                       help='Setup docker environment and return info (JSON)')
    parser.add_argument('--example', type=int,
                       help='Example number to run (1-20)')
    parser.add_argument('--injection', type=str, default=None,
                       help='Injected prompt text (optional)')
    parser.add_argument('--config', type=str, default='./openhands_config.yaml',
                       help='Configuration file path')

    args = parser.parse_args()

    # Validate arguments
    if not args.setup and args.example is None:
        parser.error("Either --setup or --example must be specified")

    # Create runner
    runner = OpenHandsBenchmarkRunner(config_path=args.config)

    # Execute action
    try:
        if args.setup:
            result = runner.setup_docker()
        else:
            result = runner.run_example(
                example=args.example,
                injected_prompt=args.injection
            )

        # Output JSON
        print(json.dumps(result, indent=2))

        sys.exit(0 if result.get('success', False) else 1)

    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}", exc_info=True)
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()

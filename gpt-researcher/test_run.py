#!/usr/bin/env python3
"""
Test script to send research requests to GPT Researcher Docker container.
This script sends a POST request to the /report/ endpoint with the specified parameters.
"""

import requests
import json
import time
import argparse
import sys


def send_research_request(task="why zhun wang is a person",
                         host="localhost",
                         port=8000,
                         generate_in_background=True,
                         timeout=300):
    """
    Send a research request to the GPT Researcher server.

    Args:
        task (str): The research task/question
        host (str): Server host (default: localhost)
        port (int): Server port (default: 8000)
        generate_in_background (bool): Whether to generate report in background
        timeout (int): Request timeout in seconds

    Returns:
        dict: Response from the server
    """

    # Prepare the request payload matching ResearchRequest model
    payload = {
        "task": task,
        "report_type": "research_report",
        "report_source": "local",
        "tone": "Objective",
        "headers": None,
        "repo_name": "",
        "branch_name": "",
        "generate_in_background": generate_in_background
    }

    # Server URL
    url = f"http://{host}:{port}/report/"

    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)

    try:
        # Send POST request
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )

        # Check if request was successful
        response.raise_for_status()

        # Parse response
        result = response.json()

        print(f"Response Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")

        # If running in background, provide the research_id for checking later
        if generate_in_background and "research_id" in result:
            print(f"\nResearch ID: {result['research_id']}")
            print(f"You can check the report later at: http://{host}:{port}/report/{result['research_id']}")

        return result

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to server at {host}:{port}")
        print("Please make sure the Docker container is running and the port is accessible.")
        return None
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out after {timeout} seconds")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error occurred: {e}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return None


def check_server_status(host="localhost", port=8000):
    """
    Check if the server is running by hitting the root endpoint.

    Args:
        host (str): Server host
        port (int): Server port

    Returns:
        bool: True if server is accessible, False otherwise
    """
    try:
        response = requests.get(f"http://{host}:{port}/", timeout=10)
        return response.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Send research requests to GPT Researcher")
    parser.add_argument("--task", "-t",
                       default="why zhun wang is a person",
                       help="Research task/question (default: 'why zhun wang is a person')")
    parser.add_argument("--host",
                       default="localhost",
                       help="Server host (default: localhost)")
    parser.add_argument("--port", "-p",
                       type=int,
                       default=8000,
                       help="Server port (default: 8000)")
    parser.add_argument("--no-background",
                       action="store_true",
                       help="Wait for report generation to complete (synchronous)")
    parser.add_argument("--timeout",
                       type=int,
                       default=300,
                       help="Request timeout in seconds (default: 300)")

    args = parser.parse_args()

    print("GPT Researcher Test Client")
    print("=" * 50)

    # Check server status first
    print("Checking server status...")
    if not check_server_status(args.host, args.port):
        print(f"ERROR: Server is not accessible at {args.host}:{args.port}")
        print("\nPlease ensure:")
        print("1. Docker container is running")
        print("2. Port mapping is correct (e.g., -p 8000:8000)")
        print("3. Server is fully started")
        sys.exit(1)

    print("Server is accessible!")
    print()

    # Send research request
    result = send_research_request(
        task=args.task,
        host=args.host,
        port=args.port,
        generate_in_background=not args.no_background,
        timeout=args.timeout
    )

    if result is None:
        sys.exit(1)

    print("\nRequest completed successfully!")


if __name__ == "__main__":
    main()
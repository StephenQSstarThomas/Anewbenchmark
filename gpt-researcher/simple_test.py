#!/usr/bin/env python3
import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8009/ws"
    print(f"Connecting to {uri}")

    async with websockets.connect(uri) as ws:
        print("Connected")

        # Very simple payload
        payload = {
            "task": "test",
            "report_type": "research_report",
            "report_source": "local",
            "source_urls": [],
            "document_urls": [],
            "tone": "Objective",
            "headers": {}
        }

        message = "start" + json.dumps(payload, ensure_ascii=True)
        print(f"Sending: {repr(message[:50])}")
        await ws.send(message)

        # Wait for response
        resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
        print(f"Got: {resp[:200]}")

asyncio.run(test())

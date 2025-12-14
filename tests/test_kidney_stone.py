#!/usr/bin/env python3
"""
Test specific query that's failing in Cherry Studio.
"""
import subprocess
import json
import time
import os
import sys

def test_kidney_stone_query():
    """Test the kidney stone query."""
    
    print("=" * 80)
    print("Testing: 'kidney stone or related condition'")
    print("=" * 80)
    
    # Get project root directory (parent of tests/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    python_executable = sys.executable  # Use current Python interpreter
    server_script = os.path.join(project_root, 'src', 'openehr_mcp_server.py')
    
    cmd = [
        python_executable,
        server_script
    ]
    
    env = {
        "EHRBASE_URL": "http://localhost:8080/ehrbase/rest",
        "EHRBASE_JSON_FORMAT": "wt_flat",
        "PYTHONPATH": os.path.join(project_root, 'src'),
        "PATH": os.environ.get("PATH", "")
    }
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1
    )
    
    # Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    print("\n📤 Initializing MCP server...")
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # Read init response
    print("✅ Initialized")
    
    # Test different query variations
    queries = [
        "kidney stone or related condition",
        "kidney stone",
        "renal calculus",
        "nephrolithiasis"
    ]
    
    for query in queries:
        print(f"\n{'─' * 80}")
        print(f"Testing query: '{query}'")
        print('─' * 80)
        
        tool_call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "suggest_icd_codes",
                "arguments": {
                    "clinical_text": query,
                    "limit": 5
                }
            }
        }
        
        print(f"📤 Sending request...")
        proc.stdin.write(json.dumps(tool_call) + "\n")
        proc.stdin.flush()
        
        print("⏳ Waiting for response...")
        start = time.time()
        response_line = proc.stdout.readline()
        elapsed = time.time() - start
        
        if response_line:
            print(f"✅ Got response in {elapsed:.2f}s")
            try:
                response = json.loads(response_line)
                
                if "error" in response:
                    print(f"\n❌ ERROR:")
                    print(json.dumps(response["error"], indent=2))
                elif "result" in response:
                    result = response["result"]
                    
                    # Extract text from content
                    if isinstance(result, dict) and "content" in result:
                        for content_item in result["content"]:
                            if content_item.get("type") == "text":
                                print(f"\n📊 Result:\n{content_item['text']}")
                    else:
                        print(f"\n📊 Result:\n{result}")
                        
            except json.JSONDecodeError as e:
                print(f"❌ Parse error: {e}")
                print(f"Raw: {response_line[:200]}")
        else:
            print("❌ No response")
            stderr = proc.stderr.read()
            if stderr:
                print(f"Stderr: {stderr[:500]}")
    
    proc.terminate()
    proc.wait(timeout=2)
    print(f"\n{'=' * 80}")
    print("✅ Test complete")

if __name__ == "__main__":
    test_kidney_stone_query()

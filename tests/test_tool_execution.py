#!/usr/bin/env python3
"""
Test MCP tool execution - simulate actual tool call.
"""
import subprocess
import json
import time
import os
import sys

def test_tool_call():
    """Test calling the suggest_icd_codes tool."""
    
    print("=" * 80)
    print("Testing suggest_icd_codes Tool Execution")
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
    
    try:
        print("\n📡 Starting MCP server...")
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
        
        print("📤 Initializing...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read init response
        init_response = proc.stdout.readline()
        print(f"✅ Initialized")
        
        # Call the tool
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "suggest_icd_codes",
                "arguments": {
                    "clinical_text": "Patient with chronic cough and fever",
                    "limit": 3
                }
            }
        }
        
        print("\n📤 Calling suggest_icd_codes tool...")
        print(f"   Input: {tool_call_request['params']['arguments']}")
        proc.stdin.write(json.dumps(tool_call_request) + "\n")
        proc.stdin.flush()
        
        # Wait for response
        print("\n⏳ Waiting for tool response (this may take 5-10 seconds)...")
        start_time = time.time()
        
        tool_response_line = proc.stdout.readline()
        elapsed = time.time() - start_time
        
        if tool_response_line:
            print(f"\n✅ Got response in {elapsed:.2f}s")
            try:
                tool_response = json.loads(tool_response_line)
                
                if "error" in tool_response:
                    print(f"\n❌ Tool returned error:")
                    print(json.dumps(tool_response["error"], indent=2))
                elif "result" in tool_response:
                    result = tool_response["result"]
                    
                    # Try to parse the result if it's a JSON string
                    try:
                        if isinstance(result, str):
                            result_data = json.loads(result)
                        else:
                            result_data = result
                        
                        print(f"\n✅ Tool executed successfully!")
                        print(f"\n📊 Results:")
                        print(json.dumps(result_data, indent=2))
                        
                        # Check if it's an error response from the tool
                        if isinstance(result_data, dict) and "error" in result_data:
                            print(f"\n⚠️  Tool returned error condition:")
                            print(f"   {result_data['error']}")
                        elif isinstance(result_data, dict) and "suggested_codes" in result_data:
                            codes = result_data["suggested_codes"]
                            print(f"\n✅ Found {len(codes)} ICD-10 codes")
                        
                    except json.JSONDecodeError:
                        print(f"\n📄 Raw result:")
                        print(result)
                else:
                    print(f"\n⚠️  Unexpected response format:")
                    print(json.dumps(tool_response, indent=2))
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response: {e}")
                print(f"   Raw: {tool_response_line}")
        else:
            print("❌ No response received from tool")
            stderr = proc.stderr.read()
            if stderr:
                print(f"\n⚠️  Stderr output:\n{stderr}")
        
        # Cleanup
        proc.terminate()
        proc.wait(timeout=2)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tool_call()

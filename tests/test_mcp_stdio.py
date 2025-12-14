#!/usr/bin/env python3
"""
Test MCP server stdio communication (simulating Claude Desktop).
"""
import subprocess
import json
import sys
import os

def test_mcp_server():
    """Test MCP server communication via stdio."""
    
    print("=" * 80)
    print("Testing MCP Server Communication (like Claude Desktop)")
    print("=" * 80)
    
    # Get project root directory (parent of tests/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    python_executable = sys.executable  # Use current Python interpreter
    server_script = os.path.join(project_root, 'src', 'openehr_mcp_server.py')
    
    # Start the MCP server
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
        
        # Send initialize request (MCP protocol)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("\n📤 Sending initialize request...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read response
        print("\n📥 Waiting for response...")
        response_line = proc.stdout.readline()
        
        if response_line:
            print(f"\n✅ Got response: {response_line[:200]}...")
            try:
                response = json.loads(response_line)
                print(f"\n📊 Response parsed successfully")
                print(f"   Protocol Version: {response.get('result', {}).get('protocolVersion')}")
                print(f"   Server Name: {response.get('result', {}).get('serverInfo', {}).get('name')}")
                
                # Request tools list
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                print("\n📤 Requesting tools list...")
                proc.stdin.write(json.dumps(tools_request) + "\n")
                proc.stdin.flush()
                
                tools_response_line = proc.stdout.readline()
                if tools_response_line:
                    tools_response = json.loads(tools_response_line)
                    tools = tools_response.get('result', {}).get('tools', [])
                    print(f"\n✅ Found {len(tools)} tools:")
                    for tool in tools:
                        name = tool.get('name', 'unknown')
                        print(f"   • {name}")
                        if 'icd' in name.lower() or 'suggest' in name.lower():
                            print(f"     ⭐ ICD coding tool found!")
                            print(f"     Description: {tool.get('description', 'N/A')}")
                            print(f"     Input schema: {json.dumps(tool.get('inputSchema', {}), indent=6)}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response: {e}")
                print(f"   Raw: {response_line}")
        else:
            print("❌ No response received")
            stderr = proc.stderr.read()
            if stderr:
                print(f"\n⚠️  Stderr output:\n{stderr}")
        
        # Cleanup
        proc.terminate()
        proc.wait(timeout=2)
        print("\n✅ Test complete")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_mcp_server()

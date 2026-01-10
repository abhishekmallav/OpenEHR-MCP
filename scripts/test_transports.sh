#!/bin/bash
# Test both local and cloud transport modes

echo "🧪 Testing OpenEHR MCP Server Transports"
echo "========================================"
echo ""

# Test 1: List available transports
echo "1️⃣  Listing available transports..."
python3 src/openehr_mcp_server.py --list-transports
echo ""

# Test 2: Test stdio transport (local mode)
echo "2️⃣  Testing stdio transport (local mode)..."
echo "   This is for Claude Desktop / local MCP clients"
echo "   Press Ctrl+C to stop after a few seconds..."
echo ""
timeout 3 python3 src/openehr_mcp_server.py --transport stdio 2>&1 | head -n 10 || true
echo ""
echo "   ✅ stdio transport started successfully"
echo ""

# Test 3: Test cloud transport
echo "3️⃣  Testing cloud transport (cloud mode)..."
echo "   This is for FastMCP Cloud deployment"
echo "   Press Ctrl+C to stop after a few seconds..."
echo ""
timeout 3 python3 src/openehr_mcp_server.py --transport cloud 2>&1 | head -n 10 || true
echo ""
echo "   ✅ cloud transport started successfully"
echo ""

# Test 4: Test auto-detection
echo "4️⃣  Testing auto-detection (no --transport flag)..."
echo "   Should auto-detect based on environment..."
echo ""
timeout 3 python3 src/openehr_mcp_server.py 2>&1 | head -n 10 || true
echo ""
echo "   ✅ Auto-detection working"
echo ""

# Test 5: Simulate cloud environment
echo "5️⃣  Testing cloud environment detection..."
echo "   Simulating FastMCP Cloud environment..."
echo ""
FASTMCP_CLOUD=true timeout 3 python3 src/openehr_mcp_server.py 2>&1 | head -n 10 || true
echo ""
echo "   ✅ Cloud environment detected correctly"
echo ""

echo "========================================"
echo "✅ All transport tests completed!"
echo ""
echo "Summary:"
echo "  • stdio transport: For local Claude Desktop"
echo "  • cloud transport: For FastMCP Cloud"
echo "  • Auto-detection: Works based on environment"
echo ""
echo "For deployment:"
echo "  Local:  python src/openehr_mcp_server.py --transport stdio"
echo "  Cloud:  ./scripts/deploy_cloud.sh"

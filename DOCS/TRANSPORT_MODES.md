# 🚀 Transport Modes: Local vs Cloud

## Overview

The openEHR MCP Server now supports **two transport modes** to work in different environments:

## 1. stdio Transport (Local Development)

**Use for:** Claude Desktop, local MCP clients

### How it Works
- Communicates via **stdin/stdout** (standard input/output)
- Direct process communication
- No network ports needed

### When to Use
- ✅ Running with Claude Desktop
- ✅ Local development and testing
- ✅ Direct process communication
- ✅ Offline operation

### How to Run
```bash
# Explicit stdio mode
python src/openehr_mcp_server.py --transport stdio

# Or auto-detect (defaults to stdio locally)
python src/openehr_mcp_server.py
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "openehr": {
      "command": "python",
      "args": [
        "/path/to/OpenEHR-MCP/src/openehr_mcp_server.py",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

## 2. cloud Transport (FastMCP Cloud)

**Use for:** FastMCP Cloud deployment, remote access

### How it Works
- Lets FastMCP Cloud handle transport layer (HTTP/SSE)
- Server accessible over the internet
- Managed by cloud platform

### When to Use
- ✅ Deploying to FastMCP Cloud
- ✅ Remote access from anywhere
- ✅ Team collaboration
- ✅ Production deployments
- ✅ Always-on availability

### How to Deploy
```bash
# Using deployment script (recommended)
./scripts/deploy_cloud.sh

# Or manual with explicit cloud transport
python src/openehr_mcp_server.py --transport cloud

# Cloud auto-detects when FASTMCP_CLOUD env var is set
FASTMCP_CLOUD=true python src/openehr_mcp_server.py
```

## Auto-Detection

The server **automatically detects** the appropriate transport based on environment:

### Detection Logic
```python
# 1. Check for cloud environment variables
if FASTMCP_CLOUD or RENDER or RAILWAY_ENVIRONMENT:
    → use 'cloud' transport

# 2. Check if stdin is interactive
if not stdin.isatty():
    → use 'stdio' transport

# 3. Default
→ use 'stdio' transport
```

### Environment Variables That Trigger Cloud Mode
- `FASTMCP_CLOUD=true` - FastMCP Cloud
- `RENDER=true` - Render.com
- `RAILWAY_ENVIRONMENT=production` - Railway.app

## Comparison Table

| Feature | stdio (Local) | cloud (FastMCP Cloud) |
|---------|---------------|----------------------|
| **Access** | Local only | Remote (internet) |
| **Client** | Claude Desktop | Any MCP client |
| **Network** | None needed | HTTP/HTTPS |
| **Deployment** | Run locally | Cloud platform |
| **Scalability** | Single instance | Auto-scaling |
| **Availability** | When running | 24/7 |
| **Use Case** | Development | Production |

## Testing Transports

### Test All Modes
```bash
./scripts/test_transports.sh
```

### Manual Testing

**Test stdio:**
```bash
python src/openehr_mcp_server.py --transport stdio
# Press Ctrl+C to stop
```

**Test cloud:**
```bash
python src/openehr_mcp_server.py --transport cloud
# Press Ctrl+C to stop
```

**Test auto-detection:**
```bash
# Local mode (should use stdio)
python src/openehr_mcp_server.py --list-transports

# Cloud mode (should use cloud)
FASTMCP_CLOUD=true python src/openehr_mcp_server.py --list-transports
```

## Why This Matters for Deployment

### ❌ Before (Only stdio)
- Server hardcoded to stdio transport
- **Cannot deploy to cloud** - stdio doesn't work over HTTP
- Only works with Claude Desktop locally

### ✅ After (Dual Transport)
- Automatic detection of environment
- **Works both locally AND in cloud**
- No code changes needed for deployment
- Production-ready

## Cloud Deployment Checklist

When deploying to FastMCP Cloud:

- [x] ✅ Server supports cloud transport
- [x] ✅ Auto-detection enabled
- [x] ✅ FASTMCP_CLOUD env var set in config
- [x] ✅ No hardcoded stdio references
- [ ] ⚠️ Set all required secrets (EHRBASE_URL, etc.)
- [ ] ⚠️ Ensure EHRbase is accessible from cloud
- [ ] ⚠️ Set up Qdrant (if using ICD coding)

## Troubleshooting

### Issue: "Server not starting in cloud"
**Check:** Is transport set correctly?
```bash
# View logs to see which transport is being used
fastmcp logs --tail 50 | grep "transport"
```

**Solution:** Ensure `FASTMCP_CLOUD=true` in environment

### Issue: "Claude Desktop can't connect"
**Check:** Are you using stdio transport?
```bash
python src/openehr_mcp_server.py --list-transports
```

**Solution:** Use `--transport stdio` or let it auto-detect

### Issue: "Auto-detection not working"
**Check:** Environment variables
```bash
env | grep -E "FASTMCP|RENDER|RAILWAY"
```

**Solution:** Set appropriate environment variable or specify transport explicitly

## Summary

The openEHR MCP Server now **intelligently switches** between:
- **stdio** for local Claude Desktop development
- **cloud** for FastMCP Cloud production deployment

**No manual configuration needed** - it auto-detects! 🎉

---

**Quick Commands:**

```bash
# Local development
python src/openehr_mcp_server.py

# Cloud deployment
./scripts/deploy_cloud.sh

# Test both modes
./scripts/test_transports.sh

# List available transports
python src/openehr_mcp_server.py --list-transports
```

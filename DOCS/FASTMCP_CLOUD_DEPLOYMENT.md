# 🚀 FastMCP Cloud Deployment Guide

This guide explains how to deploy the openEHR MCP Server to FastMCP Cloud.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Cloud Deployment Considerations](#cloud-deployment-considerations)
- [Deployment Steps](#deployment-steps)
- [Environment Configuration](#environment-configuration)
- [Testing Cloud Deployment](#testing-cloud-deployment)
- [Troubleshooting](#troubleshooting)

## Overview

FastMCP Cloud allows you to deploy your MCP server to a hosted environment, making it accessible from anywhere without running a local server. This is ideal for:

- **Remote Access**: Use your MCP server from any device
- **Team Collaboration**: Share access with team members
- **Always Available**: No need to keep local server running
- **Scalability**: Handle multiple concurrent requests

## Prerequisites

Before deploying to FastMCP Cloud, ensure you have:

1. **FastMCP CLI installed**:
   ```bash
   pip install fastmcp[cloud]
   ```

2. **FastMCP Cloud account**:
   - Sign up at https://cloud.fastmcp.dev (or relevant URL)
   - Obtain API credentials

3. **Environment variables configured**:
   - EHRbase connection details
   - API keys (Gemini, if using ICD coding)
   - Database credentials

## Cloud Deployment Considerations

### 🔄 Service Dependencies

The openEHR MCP Server relies on external services that must be accessible from the cloud:

#### ✅ Cloud-Compatible Services
- **EHRbase Server**: Must be publicly accessible or use VPN/tunnel
- **Gemini API**: Cloud-accessible (API key based)

#### ⚠️ Local Services Requiring Changes
- **Qdrant Vector Database** (localhost:6335):
  - Option 1: Deploy Qdrant to cloud (Qdrant Cloud, AWS, etc.)
  - Option 2: Disable ICD coding feature in cloud deployment
  - Option 3: Use cloud-hosted vector database alternative

### 📦 Files to Include

Ensure these files are present:
- `src/openehr_mcp_server.py` (main server)
- `src/ehrbase/` (EHRbase client modules)
- `src/utils/` (logging utilities)
- `src/mcp_prompts.py` (prompts and resources)
- `src/medical_coding.py` (if using ICD coding)
- `requirements.txt` (dependencies)
- `.env` (environment configuration)

### 🔐 Environment Variables

Required environment variables for cloud deployment:

```bash
# EHRbase Configuration
EHRBASE_URL=https://your-ehrbase-server.com
EHRBASE_USERNAME=your_username
EHRBASE_PASSWORD=your_password
EHRBASE_SECURITY=basic
DEFAULT_EHR_ID=your-default-ehr-uuid

# Optional: ICD Coding (if using suggest_icd_codes tool)
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=https://your-qdrant-instance.com  # Or localhost:6335 if tunneling
QDRANT_API_KEY=your_qdrant_api_key  # If using Qdrant Cloud

# Logging
LOG_LEVEL=INFO
```

## Deployment Steps

### Step 1: Prepare Your Server

1. **Update dependencies** for cloud compatibility:
   ```bash
   # Ensure all dependencies are in requirements.txt
   pip freeze > requirements.txt
   ```

2. **Test locally first**:
   ```bash
   python src/openehr_mcp_server.py
   ```

### Step 2: Configure for Cloud

Create a `fastmcp-cloud.yml` configuration file:

```yaml
# fastmcp-cloud.yml
name: openehr-mcp-server
runtime: python3.12

# Entry point
main: src/openehr_mcp_server.py

# Environment variables (don't commit secrets!)
env:
  LOG_LEVEL: INFO
  EHRBASE_SECURITY: basic

# Secrets (configure via CLI or dashboard)
secrets:
  - EHRBASE_URL
  - EHRBASE_USERNAME
  - EHRBASE_PASSWORD
  - GEMINI_API_KEY
  - QDRANT_URL
  - QDRANT_API_KEY

# Resource limits
resources:
  memory: 1Gi
  cpu: 0.5

# Health check
healthcheck:
  enabled: true
  path: /health
  interval: 30s

# Scaling
autoscaling:
  enabled: true
  min_instances: 1
  max_instances: 3
  target_cpu: 70
```

### Step 3: Deploy to Cloud

1. **Login to FastMCP Cloud**:
   ```bash
   fastmcp login
   ```

2. **Deploy your server**:
   ```bash
   fastmcp deploy --config fastmcp-cloud.yml
   ```

   Or use the simplified command:
   ```bash
   fastmcp deploy src/openehr_mcp_server.py
   ```

3. **Set environment secrets**:
   ```bash
   fastmcp secrets set EHRBASE_URL "https://your-ehrbase.com"
   fastmcp secrets set EHRBASE_USERNAME "your_username"
   fastmcp secrets set EHRBASE_PASSWORD "your_password"
   fastmcp secrets set GEMINI_API_KEY "your_gemini_key"
   ```

### Step 4: Verify Deployment

```bash
# Check deployment status
fastmcp status

# View logs
fastmcp logs --tail 100

# Test endpoint
fastmcp test
```

## Environment Configuration

### Option 1: Environment File (.env)

Create `.env` file (don't commit to git):

```bash
EHRBASE_URL=https://your-ehrbase-server.com
EHRBASE_USERNAME=admin
EHRBASE_PASSWORD=secret123
EHRBASE_SECURITY=basic
DEFAULT_EHR_ID=7d44b88c-4199-4bad-97dc-d78268e01398
GEMINI_API_KEY=AIza...
LOG_LEVEL=INFO
```

### Option 2: Cloud Dashboard

Configure secrets via FastMCP Cloud dashboard:
1. Navigate to your deployed server
2. Go to "Environment" or "Secrets" section
3. Add key-value pairs for sensitive data

### Option 3: CLI Commands

```bash
fastmcp config set EHRBASE_URL https://your-server.com
fastmcp secrets set EHRBASE_PASSWORD your-password
```

## Handling Service Dependencies

### EHRbase Server Access

If your EHRbase is on a private network:

**Option 1: Expose via HTTPS**
```bash
# Use reverse proxy (nginx, caddy) with SSL
# Update EHRBASE_URL to public endpoint
EHRBASE_URL=https://ehrbase.yourdomain.com
```

**Option 2: VPN/Tunnel**
```bash
# Set up VPN or SSH tunnel from cloud to your network
# Configure cloud instance to route through tunnel
```

**Option 3: Cloud-Native EHRbase**
```bash
# Deploy EHRbase to cloud alongside MCP server
# Use internal service discovery
```

### Qdrant Vector Database

**Option 1: Qdrant Cloud**
```bash
# Sign up at https://cloud.qdrant.io
# Create cluster and get credentials
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_api_key
```

**Option 2: Self-Hosted Qdrant**
```bash
# Deploy Qdrant to cloud provider
docker run -p 6333:6333 qdrant/qdrant
QDRANT_URL=https://your-qdrant-instance.com
```

**Option 3: Disable ICD Coding**
```python
# Modify server to skip ICD coding initialization
# The tool will gracefully return unavailable message
```

## Testing Cloud Deployment

### Test via FastMCP CLI

```bash
# Test server health
fastmcp test --health

# Test specific tool
fastmcp test --tool openehr_template_list

# Interactive testing
fastmcp test --interactive
```

### Test via MCP Client (Claude Desktop)

Update Claude Desktop configuration:

```json
{
  "mcpServers": {
    "openehr-cloud": {
      "url": "https://your-deployment-id.fastmcp.cloud",
      "apiKey": "your-api-key",
      "transport": "sse"
    }
  }
}
```

### Monitoring

```bash
# View real-time logs
fastmcp logs --follow

# Check metrics
fastmcp metrics

# View errors
fastmcp logs --level error --tail 50
```

## Troubleshooting

### Issue: Connection to EHRbase fails

**Symptoms**: Tools return "EHRbase client not initialized" error

**Solutions**:
1. Verify EHRBASE_URL is accessible from cloud:
   ```bash
   curl -v https://your-ehrbase-url.com/ehrbase/rest/openehr/v1/
   ```

2. Check credentials are correctly set:
   ```bash
   fastmcp secrets list
   ```

3. Ensure SSL certificates are valid (if using HTTPS)

4. Check firewall rules allow cloud IP addresses

### Issue: ICD coding unavailable

**Symptoms**: `suggest_icd_codes` tool returns "Medical coding service unavailable"

**Solutions**:
1. Deploy Qdrant to cloud:
   ```bash
   # Use Qdrant Cloud or deploy container
   QDRANT_URL=https://your-qdrant-cloud.com
   ```

2. Upload embeddings to cloud Qdrant:
   ```bash
   python scripts/upload_embeddings.py --qdrant-url https://your-qdrant.com
   ```

3. Or disable feature temporarily:
   ```python
   # Server gracefully handles unavailable service
   ```

### Issue: High memory usage

**Symptoms**: Server crashes or restarts frequently

**Solutions**:
1. Increase memory allocation:
   ```yaml
   resources:
     memory: 2Gi  # Increase from 1Gi
   ```

2. Optimize imports (lazy loading):
   ```python
   # Medical coding service already uses lazy loading
   # Ensure other heavy imports are conditional
   ```

3. Use smaller ML models if available

### Issue: Slow response times

**Solutions**:
1. Enable autoscaling:
   ```yaml
   autoscaling:
     enabled: true
     max_instances: 5
   ```

2. Cache frequently accessed data:
   ```python
   # Implement caching for template lists, etc.
   ```

3. Use connection pooling for EHRbase:
   ```python
   # Already implemented in http_client.py
   ```

## Best Practices

### Security
- ✅ Use environment variables for secrets
- ✅ Enable HTTPS for all endpoints
- ✅ Implement rate limiting
- ✅ Use VPN for private network access
- ✅ Rotate credentials regularly

### Performance
- ✅ Enable autoscaling for variable load
- ✅ Use connection pooling
- ✅ Implement caching where appropriate
- ✅ Monitor resource usage
- ✅ Optimize database queries

### Reliability
- ✅ Implement health checks
- ✅ Use graceful degradation (ICD coding optional)
- ✅ Add comprehensive logging
- ✅ Monitor error rates
- ✅ Set up alerting

## Next Steps

1. **Review Enhanced Tool Descriptions**: All tools now have comprehensive documentation
2. **Test Locally**: Ensure everything works before cloud deployment
3. **Set Up Cloud Services**: Deploy or configure EHRbase and Qdrant
4. **Deploy**: Follow steps above to deploy to FastMCP Cloud
5. **Monitor**: Set up monitoring and alerting
6. **Optimize**: Tune performance based on usage patterns

## Additional Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [openEHR Specifications](https://specifications.openehr.org/)
- [Qdrant Cloud](https://cloud.qdrant.io)
- [EHRbase Documentation](https://ehrbase.readthedocs.io/)

---

**Need Help?** Check logs with `fastmcp logs` or review error messages for specific guidance.

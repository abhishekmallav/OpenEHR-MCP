#!/bin/bash
# FastMCP Cloud Deployment Script
# This script helps you deploy the openEHR MCP Server to FastMCP Cloud

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}openEHR MCP Server - Cloud Deployment${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if fastmcp is installed
if ! command -v fastmcp &> /dev/null; then
    echo -e "${RED}Error: fastmcp CLI not found${NC}"
    echo "Please install it with: pip install fastmcp[cloud]"
    exit 1
fi

echo -e "${GREEN}✓ FastMCP CLI found${NC}"

# Check if user is logged in
if ! fastmcp whoami &> /dev/null; then
    echo -e "${YELLOW}You are not logged in to FastMCP Cloud${NC}"
    echo "Please login first:"
    echo "  fastmcp login"
    exit 1
fi

echo -e "${GREEN}✓ Logged in to FastMCP Cloud${NC}"

# Check for required files
REQUIRED_FILES=(
    "src/openehr_mcp_server.py"
    "requirements.txt"
    "fastmcp-cloud.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Required file not found: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ All required files present${NC}"

# Check if .env exists and warn about secrets
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file found${NC}"
    echo "Make sure to set secrets via FastMCP Cloud instead of committing .env"
    echo ""
fi

# Prompt for deployment type
echo "Select deployment environment:"
echo "  1) Development"
echo "  2) Production"
read -p "Enter choice (1 or 2): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENVIRONMENT="development"
        ;;
    2)
        ENVIRONMENT="production"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Deploying to: $ENVIRONMENT${NC}"

# Check if secrets are configured
echo ""
echo -e "${YELLOW}Checking required secrets...${NC}"
echo "Make sure you have set the following secrets:"
echo "  - EHRBASE_URL"
echo "  - EHRBASE_USERNAME"
echo "  - EHRBASE_PASSWORD"
echo "  - DEFAULT_EHR_ID"
echo ""
echo "Optional (for ICD coding):"
echo "  - GEMINI_API_KEY"
echo "  - QDRANT_URL"
echo "  - QDRANT_API_KEY"
echo ""
read -p "Have you configured all required secrets? (y/n): " SECRETS_OK

if [ "$SECRETS_OK" != "y" ] && [ "$SECRETS_OK" != "Y" ]; then
    echo ""
    echo "To set secrets, use:"
    echo '  fastmcp secrets set EHRBASE_URL "https://your-ehrbase.com"'
    echo '  fastmcp secrets set EHRBASE_USERNAME "your_username"'
    echo '  fastmcp secrets set EHRBASE_PASSWORD "your_password"'
    echo '  fastmcp secrets set DEFAULT_EHR_ID "your-ehr-uuid"'
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit..."
fi

# Run pre-deployment checks
echo ""
echo -e "${YELLOW}Running pre-deployment checks...${NC}"

# Check Python syntax
if ! python3 -m py_compile src/openehr_mcp_server.py; then
    echo -e "${RED}Error: Python syntax error in openehr_mcp_server.py${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python syntax OK${NC}"

# Test imports (without running server)
if ! python3 -c "import sys; sys.path.insert(0, 'src'); from openehr_mcp_server import mcp; print('OK')" &> /dev/null; then
    echo -e "${YELLOW}⚠ Warning: Could not verify imports (may be OK if dependencies are cloud-only)${NC}"
else
    echo -e "${GREEN}✓ Imports OK${NC}"
fi

# Deploy
echo ""
echo -e "${GREEN}Starting deployment...${NC}"
echo ""

if fastmcp deploy --config fastmcp-cloud.yml --env "$ENVIRONMENT"; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✓ Deployment Successful!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check status: fastmcp status"
    echo "  2. View logs: fastmcp logs --tail 100"
    echo "  3. Test endpoint: fastmcp test"
    echo ""
    echo "To monitor:"
    echo "  fastmcp logs --follow"
    echo ""
else
    echo ""
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}✗ Deployment Failed${NC}"
    echo -e "${RED}======================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check error messages above"
    echo "  2. Verify secrets are set: fastmcp secrets list"
    echo "  3. Review logs: fastmcp logs --level error"
    echo "  4. See DOCS/FASTMCP_CLOUD_DEPLOYMENT.md for detailed guide"
    echo ""
    exit 1
fi

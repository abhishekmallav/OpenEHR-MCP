# 🔐 Setup Guide - Preparing for Public Repository

## Important Files to Configure

Before running this project, you need to configure the following files with your own settings:

### 1. Environment Variables (.env)

**Copy the example file:**
```bash
cp .env.example .env
```

**Edit `.env` and add your credentials:**
```bash
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_api_key_here

# EHRbase URL (default for local Docker setup)
EHRBASE_URL=http://localhost:8080/ehrbase/rest
EHRBASE_JSON_FORMAT=wt_flat

# Optional: Set a default EHR ID
DEFAULT_EHR_ID=
```

**⚠️ NEVER commit your actual `.env` file to git** - it's already in `.gitignore`

---

### 2. MCP Configuration (mcp-config.json)

**Copy the example file:**
```bash
cp mcp-config.example.json mcp-config.json
```

**Edit `mcp-config.json` and update paths:**

Replace `/path/to/your/project` with your actual project location:

```json
{
  "mcpServers": {
    "openEHR": {
      "command": "/home/youruser/projects/openehr-mcp-server/venv/bin/python",
      "args": ["/home/youruser/projects/openehr-mcp-server/src/openehr_mcp_server.py"],
      "env": {
        "EHRBASE_URL": "http://localhost:8080/ehrbase/rest",
        "EHRBASE_JSON_FORMAT": "wt_flat",
        "PYTHONPATH": "/home/youruser/projects/openehr-mcp-server/src"
      }
    }
  }
}
```

**Path examples for different systems:**
- **Linux**: `/home/username/projects/openehr-mcp-server`
- **macOS**: `/Users/username/projects/openehr-mcp-server`
- **Windows**: `C:\\Users\\username\\projects\\openehr-mcp-server`

**⚠️ The `mcp-config.json` file is gitignored** to keep your local paths private.

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Files

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and settings

# Copy and configure MCP settings
cp mcp-config.example.json mcp-config.json
# Edit mcp-config.json with your project paths
```

### 3. Start Required Services

```bash
cd docker-compose
docker compose up -d
```

### 4. Set Up ICD-10 Embeddings (Required for Medical Coding)

**⚠️ This step is required if you want to use the `suggest_icd_codes` tool.**

**A. Obtain ICD-10 Dataset**

You need a CSV file with ICD-10 codes containing these columns:
- `code` - ICD-10 code (e.g., "A00", "R05")
- `short` - Short description
- `long` - Long/detailed description

**Where to get ICD-10 data:**
- WHO ICD-10 Online Browser: https://icd.who.int/browse10/2019/en
- CMS ICD-10 Code Sets: https://www.cms.gov/medicare/coding-billing/icd-10-codes
- Public ICD-10 datasets on GitHub or Kaggle
- Healthcare data vendors and medical coding resources

**CSV Format Example:**
```csv
code,short,long
A00,Cholera,Cholera infection
A00.0,Cholera due to Vibrio cholerae 01 biovar cholerae,Classical cholera
R05,Cough,Cough (not specified as acute or chronic)
```

**Where to place the CSV:**

```bash
# Option 1: Place in project root (default location)
openehr-mcp-server/
├── diagnosis.csv         # <-- Place your CSV here
├── scripts/
├── src/
└── ...

# Option 2: Place anywhere and specify path with --csv flag
```

**B. Generate Embeddings**

```bash
# From project root directory
# Default: Uses diagnosis.csv in current directory
python scripts/embedding.py

# Specify custom CSV location
python scripts/embedding.py --csv /path/to/your/icd10_data.csv

# Use different embedding model
python scripts/embedding.py --model sentence-transformers/all-MiniLM-L6-v2

# Custom collection name
python scripts/embedding.py --collection my_custom_icd_collection

# All options
python scripts/embedding.py \
  --model sentence-transformers/all-mpnet-base-v2 \
  --csv diagnosis.csv \
  --collection icd_embeddings \
  --qdrant-url http://localhost:6333 \
  --batch-size 2000
```

**C. Verify Embeddings**

```bash
# Check if collection was created
curl http://localhost:6333/collections

# Get collection details
curl http://localhost:6333/collections/icd_all_mpnet_base_v2

# Should show points_count: 94444 (or your dataset size)
```

**Available Embedding Models:**

| Model | Dimensions | Speed | Use Case |
|-------|-----------|-------|----------|
| `sentence-transformers/all-mpnet-base-v2` (default) | 768 | Medium | Best balance |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast | Quick setup |
| `BAAI/bge-base-en-v1.5` | 768 | Medium | High quality |
| `BAAI/bge-small-en-v1.5` | 384 | Fast | Lightweight |

**GPU Acceleration:**

The script automatically detects and uses:
- ✅ NVIDIA CUDA GPUs (significant speedup)
- ✅ Apple MPS (M1/M2/M3 Macs)
- ⚠️ Falls back to CPU if no GPU available

---

### 4. Verify Setup

```bash
# Test Python environment
python --version

# Test imports
python -c "from src.openehr_mcp_server import *; print('✅ Setup OK')"
```

---

## Security Notes

### Files That Are Safe to Commit (Public)
- ✅ `.env.example` - Template with placeholders
- ✅ `mcp-config.example.json` - Template with placeholders
- ✅ All source code files
- ✅ Documentation files
- ✅ `requirements.txt`

### Files That Should NEVER Be Committed (Private)
- ❌ `.env` - Contains your actual API keys
- ❌ `mcp-config.json` - Contains your local file paths
- ❌ `embeddings/` - Large data files
- ❌ `venv/` - Virtual environment

These are already in `.gitignore` to protect your sensitive information.

---

## For Claude Desktop Integration

See [DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md) for detailed instructions on:
- Configuring Claude Desktop
- Testing the MCP server
- Troubleshooting common issues

---

## Troubleshooting

### "Module not found" errors
- Make sure you've activated your virtual environment
- Check that `PYTHONPATH` in your config files points to the `src` directory

### "API key not found" errors
- Verify your `.env` file exists and has the correct `GEMINI_API_KEY`
- Make sure `.env` is in the same directory as your main script

### Test files fail with path errors
- The test files now automatically detect the project root
- Just run them from anywhere: `python tests/test_icd_coding.py`

---

## Need Help?

Check the documentation:
- [README.md](README.md) - Project overview
- [DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md) - Testing guide

# 🏥 openEHR MCP Server

> An intelligent bridge connecting AI assistants to Electronic Health Record (EHR) systems using the Model Context Protocol (MCP) and openEHR standards.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.7.0+-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This server enables AI assistants like Claude to interact seamlessly with openEHR-compliant EHR systems, providing natural language access to healthcare data while maintaining clinical standards and data privacy.

---

## 📚 Table of Contents

- [Technologies Overview](#-technologies-overview)
  - [Model Context Protocol (MCP)](#model-context-protocol-mcp)
  - [openEHR](#openehr)
  - [Qdrant Vector Database](#qdrant-vector-database)
- [How This Project Uses These Technologies](#-how-this-project-uses-these-technologies)
- [Features & Capabilities](#-features--capabilities)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## 🔬 Technologies Overview

### Model Context Protocol (MCP)

**What is MCP?**

The Model Context Protocol (MCP) is an open protocol developed by Anthropic that standardizes how AI applications communicate with external data sources and tools. It acts as a universal adapter, allowing Large Language Models (LLMs) to access context from various systems in a secure, controlled manner.

**Key Concepts:**

- **Protocol-Based Communication**: MCP defines a standard way for AI models to request and receive information
- **Tool Execution**: AI can execute predefined functions (tools) to perform actions like database queries, API calls, or file operations
- **Resource Management**: Provides structured access to data sources with proper authentication and permissions
- **Prompts System**: Pre-defined conversation templates to guide AI interactions

**Why MCP Matters:**

Traditional AI integrations require custom code for each data source. MCP eliminates this by providing:
- 🔒 **Security**: Controlled access to sensitive systems with proper authentication
- 🔄 **Standardization**: One protocol for all integrations
- 🚀 **Scalability**: Easy to add new tools and data sources
- 🛡️ **Safety**: Built-in guardrails for AI actions

**Learn More:**
- Official Documentation: https://modelcontextprotocol.io/
- Protocol Specification: https://spec.modelcontextprotocol.io/

### openEHR

**What is openEHR?**

openEHR (open Electronic Health Record) is an open-source technology for electronic health records and health data management. It's not just a standard—it's a comprehensive framework for building future-proof healthcare information systems.

**Core Architecture:**

1. **Two-Level Modeling**:
   - **Reference Model (RM)**: Stable information structures (like "Observation", "Composition")
   - **Archetypes**: Reusable clinical content definitions (like "Blood Pressure", "Lab Result")
   - **Templates**: Specific use-case combinations of archetypes

2. **Key Components**:
   - **EHR**: Electronic Health Record container for patient data
   - **Composition**: Document containing clinical information (visit note, lab result, etc.)
   - **AQL (Archetype Query Language)**: SQL-like language for querying health data

**Why openEHR?**

- 📊 **Semantic Interoperability**: Data means the same thing across systems
- 🔄 **Future-Proof**: Clinical knowledge separated from technical implementation
- 🌍 **International Standards**: ISO 13606 compliant
- 🔓 **Vendor Independence**: Open specifications prevent lock-in

**Real-World Example:**

```
Blood Pressure (Archetype)
├── Systolic: 120 mmHg
├── Diastolic: 80 mmHg
├── Position: Sitting
└── Time: 2025-12-14 10:30:00
```

**Learn More:**
- Official Website: https://www.openehr.org/
- Clinical Knowledge Manager: https://ckm.openehr.org/
- Specifications: https://specifications.openehr.org/

### Qdrant Vector Database

**What is Qdrant?**

Qdrant is a high-performance vector database designed for similarity search and AI applications. It stores data as high-dimensional vectors (embeddings) and enables fast semantic search based on meaning rather than exact keyword matches.

**How Vector Search Works:**

1. **Text Embeddings**: Convert text to numerical vectors (e.g., "chest pain" → [0.23, -0.45, 0.67, ...])
2. **Semantic Similarity**: Similar concepts have similar vectors
3. **Fast Retrieval**: Find nearest neighbors in milliseconds

**Example:**

```
Query: "patient has persistent cough and fever"
Embedding: [0.12, 0.45, -0.23, ...]

Qdrant finds similar vectors:
✓ R05 - Cough (similarity: 91.2%)
✓ R50.9 - Fever, unspecified (similarity: 88.7%)
✓ J00 - Acute nasopharyngitis (similarity: 85.3%)
```

**Why Qdrant?**

- ⚡ **Performance**: Written in Rust, optimized for speed
- 🎯 **Accuracy**: Advanced filtering and scoring capabilities
- 🔧 **Easy Integration**: REST API and Python client
- 💾 **Scalability**: Handles millions of vectors efficiently
- 🐳 **Docker-Ready**: Simple deployment

**Learn More:**
- Official Documentation: https://qdrant.tech/documentation/
- GitHub Repository: https://github.com/qdrant/qdrant

---

## 🏗️ How This Project Uses These Technologies

### 1️⃣ FastMCP Integration

**FastMCP** is a Python framework that simplifies building MCP servers. We use it to:

```python
from fastmcp import FastMCP

mcp = FastMCP("openEHR")

@mcp.tool()
def openehr_ehr_create(subject_id: str) -> dict:
    """Create a new Electronic Health Record"""
    # Implementation connects to EHRbase API
    return {"ehr_id": "...", "subject_id": subject_id}
```

**Our Implementation:**
- 🔧 **13 MCP Tools**: CRUD operations for EHRs, compositions, templates, and queries
- 💬 **1 MCP Prompt**: Pre-configured vital signs capture workflow
- 🤖 **AI-Powered Medical Coding**: ICD-10 code suggestion using semantic search

### 2️⃣ openEHR & EHRbase Integration

**EHRbase** is the production-grade openEHR REST API implementation we connect to.

**Our Workflow:**

```
AI Request → MCP Server → EHRbase API → PostgreSQL Database
              ↓
         Validates against
         openEHR Templates
```

**What We Handle:**
- ✅ Template validation and management
- ✅ EHR lifecycle (create, retrieve, query)
- ✅ Composition CRUD operations
- ✅ AQL query execution
- ✅ Multiple JSON formats (flat, canonical, structured)

### 3️⃣ Qdrant Vector Database for Medical Coding

**AI-Powered ICD-10 Code Suggestion:**

We use Qdrant to store 94,444+ ICD-10 codes as vector embeddings, enabling intelligent medical coding:

```
Clinical Text: "Patient with chronic cough and fever"
        ↓
  Sentence Transformer (all-mpnet-base-v2)
        ↓
  Vector Embedding [768 dimensions]
        ↓
  Qdrant Semantic Search
        ↓
Results:
  • R05 - Cough (91.2% match)
  • R50.9 - Fever (88.7% match)
```

**Optional Enhancement:**
- 🤖 Gemini AI refinement for complex multi-condition queries
- 📊 Batch processing for multiple conditions

---

## ✨ Features & Capabilities

### Core MCP Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `openehr_template_list` | List all available openEHR templates | Discover available clinical document types |
| `openehr_template_get` | Retrieve specific template definition | Understand template structure |
| `openehr_template_example_composition` | Generate example composition | See sample data format |
| `openehr_ehr_create` | Create new Electronic Health Record | Register new patient |
| `openehr_ehr_get` | Retrieve EHR by ID | Access patient record |
| `openehr_ehr_list` | List all EHRs | Browse patient records |
| `openehr_ehr_get_by_subject` | Find EHR by patient identifier | Lookup by medical record number |
| `openehr_composition_create` | Create clinical document | Record vital signs, lab results, notes |
| `openehr_composition_get` | Retrieve clinical document | View historical data |
| `openehr_composition_update` | Update clinical document | Correct or amend records |
| `openehr_composition_delete` | Delete clinical document | Remove erroneous entries |
| `openehr_query_adhoc` | Execute AQL query | Complex data retrieval |
| `suggest_icd_codes` | AI-powered ICD-10 suggestions | Automated medical coding |

### MCP Prompts

- **`vital_signs_capture`**: Guided workflow for recording vital signs with proper validation

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude / AI Assistant                   │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  openEHR MCP Server (FastMCP)               │
│  ┌──────────────┐  ┌──────────────┐ ┌───────────────┐       │
│  │   EHR Tools  │  │ Query Tools  │ │Medical Coding │       │
│  └──────┬───────┘  └───────┬──────┘ └─────────┬─────┘       │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐
  │   EHRbase     │  │  PostgreSQL   │  │   Qdrant     │
  │ (openEHR API) │  │   Database    │  │  Vector DB   │
  └───────────────┘  └───────────────┘  └──────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

#### Software Requirements

Before you begin, ensure you have:

- **Python 3.12+** - For running the MCP server
- **Git** - For cloning the repository
- **Docker & Docker Compose** - For running backend services
- **Claude Desktop** (or another MCP-compatible client) - For AI assistant integration

#### Backend Services (All Included in Docker Compose)

The project includes a complete Docker Compose setup that automatically configures:

1. **EHRbase Server** (`localhost:8080`)
   - Production-grade openEHR REST API implementation
   - Handles EHR records, compositions, and templates
   - Provides Swagger UI for API exploration

2. **PostgreSQL Database** (`localhost:5432`)
   - Database backend for EHRbase
   - Stores all EHR data with openEHR schema
   - Pre-configured with required extensions

3. **Qdrant Vector Database** (`localhost:6333`)
   - Stores ICD-10 code embeddings (94,444+ codes)
   - Enables semantic search for medical coding
   - REST API on port 6333, gRPC on port 6334
   - ⚠️ **Requires ICD-10 embeddings to be loaded before using `suggest_icd_codes` tool**

> 💡 **Everything is pre-configured!** The `docker-compose.yml` file in the `docker-compose/` directory includes all three services with proper networking and initialization scripts.

### Quick Setup (3 Steps)

#### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/openehr-mcp-server.git
cd openehr-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_actual_api_key_here
```

> 📖 **For detailed setup instructions**, see [SETUP.md](SETUP.md)

#### Step 3: Start Services

```bash
# Start EHRbase and Qdrant
cd docker-compose
docker compose up -d

# Verify services are running
docker compose ps
```

### Configure Claude Desktop

**1. Locate your Claude Desktop config file:**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**2. Copy and customize your MCP configuration:**

```bash
# Copy the example config
cp mcp-config.example.json mcp-config.json

# Edit with your actual project paths
# Replace /path/to/your/project with your installation directory
```

**3. Add to Claude Desktop config:**

```json
{
  "mcpServers": {
    "openEHR": {
      "command": "/path/to/your/project/venv/bin/python",
      "args": ["/path/to/your/project/src/openehr_mcp_server.py"],
      "env": {
        "EHRBASE_URL": "http://localhost:8080/ehrbase/rest",
        "EHRBASE_JSON_FORMAT": "wt_flat",
        "PYTHONPATH": "/path/to/your/project/src"
      }
    }
  }
}
```

**4. Restart Claude Desktop**

> 📖 **For detailed Claude Desktop setup and testing**, see [DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md)

---

## 🔧 Detailed Setup & Configuration

### Initial Setup Steps

#### 1. Upload openEHR Templates

Templates define the structure of clinical documents. Upload the included vital signs template:

```bash
# Upload the default template
python scripts/upload_template.py

# Or specify a custom template
python scripts/upload_template.py --template ehr-templates/patient_visit_template.opt
```

**Verify template upload:**

Visit http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4

#### 2. Create an Electronic Health Record (EHR)

Before storing clinical data, you need an EHR container:

```bash
# Create EHR with random subject ID
python scripts/create_ehr.py

# Or create with specific patient identifier
python scripts/create_ehr.py --subject-id "MRN-12345"
```

The script will output the EHR ID - save this for future use.

#### 3. Set Up ICD-10 Vector Database (Required for Medical Coding)

**⚠️ IMPORTANT**: The `suggest_icd_codes` MCP tool **requires** ICD-10 embeddings to be loaded in Qdrant before it can perform semantic search.

**Steps to load embeddings:**

```bash
# 1. Ensure Qdrant is running
curl http://localhost:6333/healthz

# 2. Prepare ICD-10 dataset (diagnosis.csv)
# Place your CSV file in the project root directory or specify path with --csv
# Required columns: code, short, long
# Example sources: WHO ICD-10 catalog, CMS, or other medical coding databases

# 3. Load embeddings into Qdrant (from project root)
python scripts/embedding.py

# Or specify custom CSV location
python scripts/embedding.py --csv /path/to/your/diagnosis.csv

# Use a different embedding model
python scripts/embedding.py --model sentence-transformers/all-MiniLM-L6-v2
```

**What this does:**
- Converts 94,444+ ICD-10 codes into vector embeddings using the `all-mpnet-base-v2` model
- Stores embeddings in Qdrant collection `icd_mpnet_basev2`
- Enables semantic similarity search (e.g., "chest pain" → ICD codes)

**Verification:**

```bash
# Check if collection exists
curl http://localhost:6333/collections

# Check collection size
curl http://localhost:6333/collections/icd_mpnet_basev2
```

> 📝 **Note**: 
> - Embedding generation requires the ICD-10 dataset CSV file and takes 10-15 minutes
> - The `suggest_icd_codes` tool will not work without loaded embeddings
> - If you don't need medical coding, you can skip this step

### JSON Format Configuration

The MCP server supports multiple JSON serialization formats:

| Format | Description | Use Case |
|--------|-------------|----------|
| `wt_flat` (default) | Simplified flat structure | Easier for AI to understand |
| `canonical` | Standard openEHR JSON | Maximum compatibility |
| `wt_structured` | Structured web template | Complex nested data |

Configure via environment variable:

⚠️ **Prerequisites**: ICD-10 embeddings must be loaded in Qdrant (see setup step 3)

```bash
# Test ICD-10 code suggestion
python tests/test_icd_coding.py

# Test with MCP protocol
python tests/test_mcp_cholera.py

# If embeddings are not loaded, these tests will fail with:
# "Collection not found" or "No results returned"
## 🧪 Testing & Validation

### Run Integration Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ehr_client.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Medical Coding Feature

```bash
# Test ICD-10 code suggestion
python tests/test_icd_coding.py

# Test with MCP protocol
python tests/test_mcp_cholera.py
```

### Verify Services

```bash
# Check Docker services
docker compose ps

# Test EHRbase
curl http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4

# Test Qdrant
curl http://localhost:6333/healthz

# View service logs
docker compose logs -f ehrbase
docker compose logs -f qdrant
```

### Optional: Launch Streamlit Web UI

For a graphical interface to interact with EHRbase:

```bash
# Install streamlit if not already installed
pip install streamlit

# Launch the web UI
streamlit run app.py
```

The Streamlit UI provides a browser-based interface to:
- 📋 List and manage openEHR templates
- 🏥 Create and retrieve EHRs
- 📝 Create, update, and delete compositions
- 🔍 Execute AQL queries
- 📊 View JSON data in a user-friendly format

Access at: http://localhost:8501

---

## 📖 Documentation

### Comprehensive Guides

- **[SETUP.md](SETUP.md)** - Complete setup guide with environment configuration
- **[DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md)** - Claude Desktop testing and troubleshooting
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[docker-compose/docker-compose.yml](docker-compose/docker-compose.yml)** - Service orchestration

### API References

- **EHRbase API**: http://localhost:8080/ehrbase/swagger-ui/index.html
- **Qdrant API**: https://qdrant.tech/documentation/
- **MCP Protocol**: https://spec.modelcontextprotocol.io/

### Project Structure

```
openehr-mcp-server/
├── src/                          # Source code
│   ├── openehr_mcp_server.py    # Main MCP server
│   ├── medical_coding.py        # ICD-10 coding logic
│   ├── mcp_prompts.py          # MCP prompt definitions
│   └── ehrbase/                # EHRbase API clients
├── scripts/                    # Utility scripts
│   ├── create_ehr.py          # EHR creation
│   ├── upload_template.py     # Template upload
│   ├── embedding.py           # ICD-10 embedding generator
│   └── vector_search.py       # Vector search utilities
├── tests/                       # Test suite
├── docker-compose/             # Docker services configuration
│   └── docker-compose.yml      # EHRbase + PostgreSQL + Qdrant
├── ehr-templates/              # openEHR templates (.opt files)
├── DOCS/                       # Documentation
│   ├── SETUP.md               # Detailed setup guide
│   └── MCP_TEST_GUIDE.md      # Testing guide
├── app.py                      # Streamlit Web UI for EHRbase (optional)
├── diagnosis.csv               # ICD-10 dataset (place here or specify path)
├── .env.example               # Environment template
├── mcp-config.example.json    # MCP configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🖥️ Streamlit Web UI (Optional)

**`app.py`** provides a **browser-based admin interface** for direct interaction with EHRbase, complementing the MCP server for AI assistants.

### What Does app.py Do?

The Streamlit application (`app.py`) is a comprehensive web interface with 5 main sections:

#### 1. **Templates Tab** 📋
- **List Templates**: View all available openEHR templates in EHRbase
- **Get Example**: Generate example FLAT JSON for any template
- **Upload Templates**: Upload new `.opt` (Operational Template) files
- **Preview**: View template structure and required fields

#### 2. **EHRs Tab** 🏥
- **Create EHR**: Generate new Electronic Health Records
- **Fetch EHR**: Retrieve EHR details by ID
- **List EHRs**: Browse all EHRs with pagination
- **View Metadata**: See EHR status, creation time, and subject details

#### 3. **Compositions Tab** 📝
- **Create Composition**: Submit clinical data using FLAT JSON format
  - Paste JSON directly or use generated examples
  - Specify EHR ID and template ID
  - Automatic validation and error handling
- **Fetch Composition**: Retrieve existing clinical documents
  - Search by composition UID
  - View complete composition with all data points

#### 4. **AQL Query Tab** 🔍
- **Execute AQL Queries**: Run Archetype Query Language queries
- **Query Builder**: 
  - Pre-built query templates
  - Custom query input
  - Parameter support
- **Results Display**: Pretty-printed JSON results with syntax highlighting
- **Examples**: Common queries like "list all vital signs" or "find patients"

#### 5. **FORM Tab** 🩺
- **Interactive Blood Pressure Form**: User-friendly form for vital signs entry
  - Visual input fields (no JSON required)
  - Systolic/diastolic pressure readings
  - Mean arterial pressure calculation
  - Position, cuff size, and measurement method
  - Clinical interpretation notes
- **Automatic JSON Generation**: Converts form data to openEHR FLAT format
- **Direct Submission**: Posts composition to EHRbase with one click

### Key Features

✨ **User-Friendly Interface**
- No coding required - point-and-click operations
- Form-based data entry for common use cases
- Real-time validation and error messages

📊 **JSON Management**
- Pretty-printed JSON with syntax highlighting
- Copy/paste support for quick testing
- Visual diff between expected and actual formats

⚙️ **Connection Settings** (Sidebar)
- Configure EHRbase base URL
- Add custom headers (authentication, audit details)
- Test connection status

🔧 **Development Tools**
- Inspect API requests and responses
- HTTP status codes and error messages
- Example data generation for testing

### Launch the UI

```bash
# Ensure EHRbase is running
cd docker-compose && docker compose up -d

# Launch Streamlit
streamlit run app.py
```

Open your browser to: **http://localhost:8501**

### Use Cases

| Use Case | Description |
|----------|-------------|
| 🧪 **Testing** | Quickly test EHRbase operations without writing code |
| 📚 **Learning** | Explore openEHR concepts visually with immediate feedback |
| 🔧 **Development** | Debug and validate compositions before automation |
| 👥 **Demos** | Show EHRbase capabilities to stakeholders |
| 📝 **Data Entry** | Manual clinical data entry via forms |
| 🔍 **Querying** | Ad-hoc data retrieval and exploration |

### Example Workflow

1. **Upload Template**: Use Templates tab to upload `patient_visit_template.opt`
2. **Create EHR**: Use EHRs tab to create a new patient record
3. **Enter Data**: Use FORM tab to input vital signs (blood pressure, etc.)
4. **Query Data**: Use AQL tab to retrieve and analyze the stored data
5. **Review**: View compositions in JSON format to verify structure

> 💡 **Tip**: The Streamlit UI and MCP server can run simultaneously - they're independent interfaces to the same EHRbase instance. Use the UI for testing and the MCP server for AI-powered automation.

---

## 🎯 Usage Examples

### Example 1: Create Patient Record with Vital Signs

**In Claude Desktop:**

```
I need to record vital signs for patient EHR ID: abc-123-xyz

Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm
Temperature: 98.6°F
Respiratory Rate: 16 breaths/min
```

Claude will use the `openehr_composition_create` tool to store this data in openEHR format.

### Example 2: Query Patient Data

**In Claude Desktop:**

```
Show me all vital signs recordings for the last 7 days
for EHR ID: abc-123-xyz
```
⚠️ **Prerequisites**: ICD-10 embeddings must be loaded in Qdrant

**In Claude Desktop:**

```
Suggest ICD-10 codes for: "Patient presents with persistent 
dry cough, mild fever, and shortness of breath"
```

**Expected Response:**

```
Found 3 ICD-10 codes:

1. R05 - Cough (91.2% match)
2. R50.9 - Fever, unspecified (88.7% match)
3. R06.02 - Shortness of breath (86.4% match)
**In Claude Desktop:**


Suggest ICD-10 codes for: "Patient presents with persistent 
dry cough, mild fever, and shortness of breath"
```

Claude will use `suggest_icd_codes` to return relevant ICD-10 codes with similarity scores.

## 🛠️ Troubleshooting

### Common Issues

**Issue: "Connection refused" when accessing EHRbase**

```bash
# Check if services are running
docker compose ps
```
Restart services or "Collection not found"

This means ICD-10 embeddings are not loaded in Qdrant.

```bash
# 1. Ensure Qdrant is running
curl http://localhost:6333/healthz

# 2. Check if collection exists
curl http://localhost:6333/collections

# 3. If collection is missing, load embeddings
python scripts/embedding.py

# 4. Verify collection was created
curl http://localhost:6333/collections/icd_all_mpnet_base_v2
```

> The `suggest_icd_codes` tool requires embeddings to be pre-loaded!
```bash
# Upload the template
python scripts/upload_template.py

# Verify upload
curl http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4
```

**Issue: "No ICD-10 codes found"**

```bash
# Ensure Qdrant is running
curl http://localhost:6333/healthz

# Check if collection exists
curl http://localhost:6333/collections
```

**Issue: Claude Desktop doesn't see the MCP server**

1. Check config file path is correct
2. Verify Python path in config
3. Restart Claude Desktop completely
4. Check logs in Claude Desktop's console

### Get Help

- 📖 Check [DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md) for troubleshooting guide
- 🐛 Open an issue on GitHub
- 💬 Review EHRbase documentation: https://ehrbase.readthedocs.io/

---

## 🔐 Security Considerations

⚠️ **Important Security Notes:**

1. **API Keys**: Never commit `.env` files with real API keys
2. **Production Use**: This setup is for development - use proper authentication for production
3. **Data Privacy**: Ensure compliance with healthcare regulations (HIPAA, GDPR)
4. **Network Security**: Don't expose EHRbase or Qdrant ports to the internet without proper security
5. **AI Model Selection**: For production healthcare data, use models with strong data privacy guarantees

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** - For the Model Context Protocol
- **EHRbase** - For the openEHR implementation
- **Qdrant** - For the vector database
- **openEHR Foundation** - For the healthcare data standards
- **FastMCP** - For the Python MCP framework

---

## 📞 Support

- 📖 Documentation: See [SETUP.md](SETUP.md) and [DOCS/MCP_TEST_GUIDE.md](DOCS/MCP_TEST_GUIDE.md)
- 🌐 openEHR Community: https://discourse.openehr.org/
- 💬 MCP Community: https://github.com/modelcontextprotocol

---

## Authors
- [Abhishek](https://github.com/abhishekmallav)
- [Ayush](https://github.com/)
- [Anish](https://github.com/)
- [Prathamesh](https://github.com/)

---
**Built with ❤️ for better healthcare data interoperability**

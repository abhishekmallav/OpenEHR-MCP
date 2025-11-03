# openEHR MCP Server

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.7.0%2B-green.svg)](https://github.com/punkpeye/fastmcp)
[![License](https://img.shields.io/badge/License-TODO-lightgrey.svg)](#license)
[![Tests](https://img.shields.io/badge/Tests-Pytest-orange.svg)](https://pytest.org)

A Model Context Protocol (MCP) server for interacting with openEHR Electronic Health Record systems, specifically designed for EHRbase integration. This server provides AI-powered medical coding capabilities and comprehensive EHR management through a standardized MCP interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Performance Notes](#performance-notes)
- [Scalability Considerations](#scalability-considerations)
- [Contributing](#contributing)
- [License](#license)

## Overview

The openEHR MCP Server bridges the gap between AI language models and openEHR-compliant Electronic Health Record systems. It provides a standardized interface for creating, retrieving, updating, and querying health records while offering intelligent medical coding suggestions using machine learning models.

This server is particularly useful for:
- Healthcare applications requiring structured data entry
- Clinical decision support systems
- Medical coding automation
- EHR integration projects
- Healthcare AI applications

## Features

### Core EHR Operations
- **Template Management**: List, retrieve, and generate example compositions from openEHR templates
- **EHR Lifecycle**: Create, read, update, and delete Electronic Health Records
- **Composition Management**: Full CRUD operations for openEHR compositions
- **AQL Queries**: Execute Archetype Query Language (AQL) queries against the EHR database

### AI-Powered Medical Coding
- **ICD-10 Code Suggestions**: Semantic search for relevant ICD-10 codes based on clinical text
- **Vector Database Integration**: Uses Qdrant for fast similarity search
- **Gemini AI Integration**: Optional LLM-powered clinical text refinement
- **Sentence Transformers**: Advanced embedding models for medical text understanding

### User Interface
- **Streamlit Frontend**: Complete web-based UI for EHR management and testing
- **Blood Pressure Forms**: Specialized forms for vital signs capture
- **Template Upload**: Direct template (.opt) file upload functionality
- **Real-time Validation**: Immediate feedback on data entry and API responses

### Developer Experience
- **MCP Protocol**: Standard Model Context Protocol for AI integration
- **Async Architecture**: High-performance asynchronous operations
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Plugin System**: Extensible transport plugin architecture

## Tech Stack

### Backend Framework
- **FastMCP**: Model Context Protocol server framework
- **Python 3.8+**: Core programming language
- **AsyncIO**: Asynchronous programming support

### AI/ML Components
- **PyTorch**: Deep learning framework for embeddings
- **Transformers**: Hugging Face transformers library
- **Sentence Transformers**: Specialized embedding models
- **Qdrant**: Vector database for semantic search
- **LangChain Google GenAI**: Gemini AI integration

### Web Framework
- **Streamlit**: Interactive web application framework
- **HTTPX**: Modern HTTP client library

### Data & Configuration
- **JSON**: Primary data exchange format
- **Environment Variables**: Configuration management
- **Python-dotenv**: Environment variable loading

### Testing & Quality
- **Pytest**: Testing framework with async support
- **Pytest-asyncio**: Async test utilities
- **Pytest-cov**: Code coverage reporting

## Installation

### Prerequisites

1. **Python 3.8 or higher**
2. **EHRbase server** running and accessible
3. **Qdrant vector database** (for medical coding features)
4. **Optional**: Gemini API key for enhanced medical coding

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd openehr-mcp-server
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install test dependencies (optional)**
   ```bash
   pip install -r requirements-test.txt
   ```

5. **Set up environment variables**
   ```bash
   # Create .env file
   echo "EHRBASE_URL=http://localhost:8080/ehrbase/rest" > .env
   echo "DEFAULT_EHR_ID=your-default-ehr-id" >> .env
   echo "GEMINI_API_KEY=your-gemini-api-key" >> .env  # Optional
   ```

6. **Start Qdrant (for medical coding)**
   ```bash
   # Using Docker
   docker run -p 6333:6333 qdrant/qdrant
   ```

## Usage Examples

### Running the MCP Server

```bash
# Start with stdio transport (default)
python src/openehr_mcp_server.py

# List available transports
python src/openehr_mcp_server.py --list-transports

# Use specific transport
python src/openehr_mcp_server.py --transport stdio
```

### Running the Streamlit Frontend

```bash
# Start the web interface
streamlit run APP.py
```

### Basic MCP Tool Usage

The server provides several MCP tools that can be called by AI assistants:

```python
# List all available templates
await openehr_template_list()

# Get a specific template
await openehr_template_get("patient_visit_template")

# Create a new EHR
await openehr_ehr_create()

# Suggest ICD-10 codes
await suggest_icd_codes("patient has chest pain and shortness of breath")
```

### AQL Query Example

```python
# Execute an AQL query
query = """
SELECT 
    c/uid/value AS composition_uid,
    c/name/value AS composition_name
FROM EHR e 
CONTAINS COMPOSITION c
WHERE e/ehr_id/value = $ehr_id
"""

await openehr_query_adhoc(query, {"ehr_id": "your-ehr-id"})
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EHRBASE_URL` | EHRbase server base URL | `http://localhost:8080/ehrbase/rest` | Yes |
| `DEFAULT_EHR_ID` | Default EHR ID for operations | None | No |
| `GEMINI_API_KEY` | Google Gemini API key | None | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Medical Coding Configuration

The medical coding service requires:
- **Qdrant server** running at `localhost:6333`
- **ICD-10 vector collection** named `icd_mpnet_basev2`
- **Sentence transformer model**: `sentence-transformers/all-mpnet-base-v2`

### Streamlit Configuration

The web interface can be configured through the sidebar:
- **EHRbase URL**: Server endpoint
- **Extra Headers**: Additional HTTP headers in JSON format
- **Template Selection**: Choose from available templates

## Project Structure

```
openehr-mcp-server/
├── src/                          # Source code
│   ├── ehrbase/                  # EHRbase client library
│   │   ├── __init__.py          # Package initialization
│   │   ├── client.py            # Main facade client
│   │   ├── composition_client.py # Composition operations
│   │   ├── ehr_client.py        # EHR operations
│   │   ├── http_client.py       # HTTP client wrapper
│   │   ├── query_client.py      # AQL query operations
│   │   ├── template_client.py   # Template operations
│   │   └── format_config.py     # Format configuration
│   ├── utils/                   # Utility modules
│   │   └── logging_utils.py     # Logging configuration
│   ├── medical_coding.py        # AI-powered medical coding
│   ├── mcp_prompts.py          # MCP prompt definitions
│   └── openehr_mcp_server.py   # Main MCP server
├── tests/                       # Test suite
│   ├── conftest.py             # Pytest configuration
│   ├── pytest.ini             # Test settings
│   └── test_*.py               # Test modules
├── APP.py                      # Streamlit web interface
├── requirements.txt            # Production dependencies
├── requirements-test.txt       # Test dependencies
└── README.md                   # This file
```

### Key Components

- **EHRbase Client**: Modular client library with specialized clients for different operations
- **Medical Coding Service**: AI-powered ICD-10 code suggestion using vector similarity
- **MCP Server**: FastMCP-based server implementing the Model Context Protocol
- **Streamlit App**: Complete web interface for testing and demonstration
- **Transport Plugins**: Extensible system for different communication protocols

## API Documentation

### MCP Tools

The server exposes the following MCP tools:

#### Template Operations
- `openehr_template_list()`: List all available templates
- `openehr_template_get(template_id)`: Get specific template
- `openehr_template_example_composition(template_id)`: Generate example composition

#### EHR Operations
- `openehr_ehr_create(ehr_status?)`: Create new EHR
- `openehr_ehr_get(ehr_id)`: Retrieve EHR by ID
- `openehr_ehr_list()`: List all EHRs
- `openehr_ehr_get_by_subject(subject_id, subject_namespace)`: Get EHR by subject

#### Composition Operations
- `openehr_composition_create(composition_data, ehr_id?)`: Create composition
- `openehr_composition_get(composition_uid, ehr_id?)`: Get composition
- `openehr_composition_update(composition_uid, composition_data, ehr_id?)`: Update composition
- `openehr_composition_delete(preceding_version_uid, ehr_id?)`: Delete composition

#### Query Operations
- `openehr_query_adhoc(query, query_parameters?)`: Execute AQL query

#### Medical Coding
- `suggest_icd_codes(clinical_text, limit?, use_gemini?)`: Suggest ICD-10 codes

### Response Formats

All tools return JSON-formatted responses with consistent error handling:

```json
{
  "data": "...",
  "error": null
}
```

Error responses include detailed error messages:

```json
{
  "error": "Detailed error description",
  "data": null
}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_openehr_mcp_server.py

# Run with verbose output
pytest -v
```

### Test Configuration

- **Async Support**: All tests support async operations
- **EHRbase Integration**: Tests require running EHRbase server
- **Logging**: Comprehensive test logging enabled
- **Coverage**: Code coverage reporting available

### Test Structure

```
tests/
├── conftest.py                 # Shared test configuration
├── test_openehr_mcp_server.py  # MCP server integration tests
├── test_ehr_client.py          # EHR client tests
├── test_composition_client.py  # Composition client tests
├── test_query_client.py        # Query client tests
└── test_template_client.py     # Template client tests
```

## Performance Notes

### Optimization Strategies

- **Async Architecture**: All I/O operations are asynchronous for better concurrency
- **Connection Pooling**: HTTP client uses connection pooling for efficiency
- **Lazy Loading**: Medical coding service initializes only when needed
- **Vector Caching**: Qdrant provides efficient vector similarity search
- **Error Handling**: Comprehensive error handling prevents cascading failures

### Performance Characteristics

- **Template Operations**: ~100-500ms depending on template complexity
- **Composition CRUD**: ~200-1000ms depending on data size
- **AQL Queries**: ~100ms-5s depending on query complexity
- **Medical Coding**: ~500-2000ms including ML inference
- **Memory Usage**: ~200-500MB base, +1-2GB with ML models loaded

### Monitoring

- **Structured Logging**: All operations include timing and performance metrics
- **Error Tracking**: Detailed error logging with stack traces
- **Request Tracing**: Full request/response logging for debugging

## Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: Server maintains no session state
- **Database Scaling**: EHRbase can be clustered for high availability
- **Vector Database**: Qdrant supports clustering and sharding
- **Load Balancing**: Multiple server instances can run behind load balancer

### Vertical Scaling

- **Memory Requirements**: ML models require 2-4GB RAM
- **CPU Usage**: Vector operations benefit from multi-core processors
- **Storage**: Vector database requires SSD storage for optimal performance

### Production Considerations

- **Container Deployment**: Docker-ready architecture
- **Health Checks**: Built-in health monitoring endpoints
- **Configuration Management**: Environment-based configuration
- **Security**: HTTPS support and authentication integration points

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code style and standards
- Pull request process
- Issue reporting
- Development setup
- Testing requirements

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

TODO: Add license information

---

**Note**: This project is under active development. APIs and interfaces may change between versions. Please check the changelog for breaking changes.

For questions, issues, or contributions, please visit our [GitHub repository](TODO: Add repository URL).
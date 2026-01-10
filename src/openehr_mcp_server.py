from fastmcp import FastMCP
import json
import time
import os
import argparse
import sys
from medical_coding import MedicalCodingService
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"✅ Loaded .env from: {env_path}")  # Debug line
print(f"   GEMINI_API_KEY present: {bool(os.getenv('GEMINI_API_KEY'))}")  # Debug line


# Import custom logging utilities
from utils.logging_utils import get_logger

# Import the EHRbase client facade
from ehrbase import EHRbaseClient

# Import prompts
from mcp_prompts import register_prompts

# Get a logger for this module
logger = get_logger("openehr_mcp_server")

# Initialize the EHRbase client with error handling
try:
    ehrbase_client = EHRbaseClient()
    DEFAULT_EHR_ID = ehrbase_client.default_ehr_id
    logger.info("EHRbase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize EHRbase client: {e}")
    ehrbase_client = None
    DEFAULT_EHR_ID = None

# Initialize the MCP server with the official SDK
mcp = FastMCP("openEHR MCP Server")

# Register prompts and resources
try:
    mcp = register_prompts(mcp)
    logger.info("Registered prompts and resources for the openEHR MCP Server")
except Exception as e:
    logger.warning(f"Failed to register prompts: {e}")

# Initialize medical coding service (lazy loading to avoid startup delays)
medical_coding_service = None
medical_coding_service_failed = False  # Track if initialization failed


def get_medical_coding_service():
    """Lazy initialization of cloud-based medical coding service with error handling."""
    global medical_coding_service, medical_coding_service_failed

    # If we already tried and failed, don't try again
    if medical_coding_service_failed:
        return None

    if medical_coding_service is None:
        try:
            medical_coding_service = MedicalCodingService()
            logger.info("✅ Medical coding service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize medical coding service: {e}")
            logger.error(
                f"   This feature requires: HF_TOKEN, QDRANT_URL, and QDRANT_API_KEY in .env")
            medical_coding_service_failed = True
            return None
    return medical_coding_service


# Define this ONCE at the top level (not inside function)
class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# TRANSPORT PLUGIN SYSTEM


class TransportPlugin:
    """Base class for transport plugins."""

    def __init__(self, name: str):
        self.name = name

    def run(self, mcp_server, **kwargs):
        """Run the transport with the given MCP server."""
        raise NotImplementedError("Transport plugins must implement run()")


class StdioTransportPlugin(TransportPlugin):
    """Standard I/O transport plugin (for local development with Claude Desktop)."""

    def __init__(self):
        super().__init__("stdio")

    def run(self, mcp_server, **kwargs):
        """Run the MCP server with stdio transport."""
        logger.info("Using stdio transport (local development mode)")
        mcp_server.run(transport='stdio')


class CloudTransportPlugin(TransportPlugin):
    """Cloud/HTTP transport plugin (for FastMCP Cloud deployment)."""

    def __init__(self):
        super().__init__("cloud")

    def run(self, mcp_server, **kwargs):
        """Run the MCP server with cloud-compatible transport.
        
        For FastMCP Cloud, we don't specify a transport - the cloud platform
        handles the transport layer (HTTP/SSE) automatically.
        """
        logger.info("Using cloud transport (FastMCP Cloud mode)")
        # Let FastMCP Cloud handle transport - don't specify 'stdio'
        mcp_server.run()


# Global transport registry
_transport_plugins = {}


def register_transport_plugin(plugin: TransportPlugin):
    """Register a transport plugin."""
    _transport_plugins[plugin.name] = plugin
    logger.info(f"Registered transport plugin: {plugin.name}")


def get_transport_plugin(name: str) -> TransportPlugin:
    """Get a registered transport plugin by name."""
    return _transport_plugins.get(name)


def list_transport_plugins():
    """List all registered transport plugins."""
    return list(_transport_plugins.keys())


# Register the default stdio transport
register_transport_plugin(StdioTransportPlugin())

# Register the cloud transport for FastMCP Cloud deployment
register_transport_plugin(CloudTransportPlugin())

# Auto-detect environment and set default transport
def get_default_transport():
    """Auto-detect the appropriate transport based on environment."""
    # Check if running in cloud environment
    if os.getenv('FASTMCP_CLOUD') or os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT'):
        return 'cloud'
    # Check if stdin is a TTY (interactive terminal)
    if not sys.stdin.isatty():
        return 'stdio'
    # Default to stdio for local development
    return 'stdio'

# TOOLS - Actions to perform with templates and EHRs


@mcp.tool()
async def openehr_template_list() -> str:
    """List all available openEHR templates from the EHRbase server.
    
    This tool retrieves a comprehensive list of all clinical document templates 
    registered in the openEHR system. Templates define the structure and constraints 
    for clinical compositions (e.g., vital signs, lab results, discharge summaries).
    
    Returns:
        JSON string containing an array of template objects, each with:
        - template_id: Unique identifier for the template
        - concept: Human-readable name describing the template's purpose
        - created_timestamp: When the template was registered
        
    Use this tool when:
        - You need to discover available clinical document types
        - Before creating a composition to identify valid templates
        - To explore the system's clinical data capabilities
        
    Example response:
        [
          {
            "template_id": "vital_signs_basic",
            "concept": "Vital Signs Basic",
            "created_timestamp": "2024-01-15T10:30:00Z"
          }
        ]
    """
    logger.info("MCP Tool call: openehr_template_list")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        templates = await ehrbase_client.get_template_list()
        result = json.dumps(templates, indent=2)

        elapsed = time.time() - start_time
        count = len(templates) if isinstance(templates, list) else 'N/A'
        logger.info(
            f"Returning template list with {count} templates in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error listing templates: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_template_get(template_id: str) -> str:
    """Retrieve a specific openEHR template by its unique identifier.
    
    This tool fetches the complete structure and constraints of a specific clinical 
    template. The template defines what data fields are required, their data types, 
    terminology bindings, and validation rules for creating valid compositions.
    
    Args:
        template_id: The unique identifier of the template (e.g., 'vital_signs_basic', 
                    'patient_visit_template'). Must match an existing template in the system.
                    
    Returns:
        JSON string containing the complete template definition including:
        - Tree structure of all data nodes
        - Data type constraints (text, numeric, coded values)
        - Required vs optional fields
        - Terminology bindings (SNOMED CT, LOINC, etc.)
        
    Use this tool when:
        - You need to understand the structure of a specific clinical document
        - Before creating or validating a composition
        - To identify required fields and their constraints
        
    Example usage:
        template_id = "vital_signs_basic"  # Get vital signs template structure
    """
    if not template_id or not isinstance(template_id, str):
        return json.dumps({"error": "Invalid template_id provided"}, indent=2)

    logger.info(f"MCP Tool call: openehr_template_get with ID {template_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        template = await ehrbase_client.get_template(template_id)
        result = json.dumps(template, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Retrieved template {template_id} in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error retrieving template {template_id}: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_template_example_composition(template_id: str) -> str:
    """Generate an example openEHR composition based on a specific template.
    
    This tool creates a sample composition populated with placeholder data that 
    conforms to the template's structure and constraints. This is invaluable for 
    understanding the expected JSON format when creating real clinical documents.
    
    Args:
        template_id: The unique identifier of the template for which to generate 
                    an example (e.g., 'vital_signs_basic', 'patient_visit_template').
                    
    Returns:
        JSON string containing a complete, valid composition example with:
        - All required fields populated with sample data
        - Proper data structure and nesting
        - Correct data types (strings, numbers, coded values)
        - Valid archetype paths and naming conventions
        
    Use this tool when:
        - You need to create a new composition and want to see the expected format
        - Learning how to structure clinical data for a specific template
        - Validating your composition structure before submission
        - Understanding the relationship between template and composition
        
    Example workflow:
        1. Use openehr_template_list to find available templates
        2. Use this tool to get an example composition structure
        3. Replace sample data with real patient information
        4. Use openehr_composition_create to save the real data
    """
    if not template_id or not isinstance(template_id, str):
        return json.dumps({"error": "Invalid template_id provided"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_template_example_composition for template {template_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        example = await ehrbase_client.get_template_example(template_id)
        result = json.dumps(example, indent=2)

        elapsed = time.time() - start_time
        logger.info(
            f"Generated example composition for {template_id} in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error generating example: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


# EHR MANAGEMENT TOOLS
@mcp.tool()
async def openehr_ehr_create(ehr_status=None) -> str:
    """Create a new Electronic Health Record (EHR) in the system.
    
    This tool initializes a new patient record container in the openEHR system. 
    Each patient must have an EHR before any clinical data (compositions) can be stored.
    The EHR acts as the top-level container that holds all clinical documents, lab results,
    medications, and other health data for a single patient throughout their lifetime.
    
    Args:
        ehr_status: Optional JSON object or string defining the EHR metadata. Can include:
                   - subject: Patient identifier (external_ref with id and namespace)
                   - is_modifiable: Whether the EHR can be modified (default: true)
                   - is_queryable: Whether the EHR can be queried (default: true)
                   If not provided, creates an EHR with default status.
                   
    Returns:
        JSON string containing:
        - ehr_id: UUID uniquely identifying this patient's EHR (save this!)
        - system_id: The openEHR system identifier
        - time_created: Timestamp when the EHR was created
        - ehr_status: The complete EHR status object
        
    Use this tool when:
        - Registering a new patient in the system
        - Starting a new patient encounter or admission
        - Setting up test/demo patient records
        
    Important: Save the returned ehr_id - it's required for all subsequent operations
    on this patient's record (creating compositions, querying data, etc.).
    
    Example:
        # Create basic EHR
        result = await openehr_ehr_create()
        
        # Create EHR with patient identifier
        status = {
            "subject": {
                "external_ref": {
                    "id": {"value": "PATIENT-12345"},
                    "namespace": "HOSPITAL_ID"
                }
            }
        }
        result = await openehr_ehr_create(ehr_status=status)
    """
    logger.info(f"MCP Tool call: openehr_ehr_create")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        status_json = None
        if ehr_status:
            if isinstance(ehr_status, str):
                try:
                    status_json = json.loads(ehr_status)
                except json.JSONDecodeError:
                    return json.dumps({"error": f"Invalid JSON in ehr_status: {ehr_status}"}, indent=2)
            else:
                status_json = ehr_status

        result = await ehrbase_client.create_ehr(status_json)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        ehr_id = result.get('ehr_id', 'unknown') if isinstance(
            result, dict) else 'unknown'
        logger.info(f"Created EHR in {elapsed:.2f}s with ID: {ehr_id}")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error creating EHR: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_ehr_get(ehr_id: str) -> str:
    """Retrieve a complete Electronic Health Record by its unique identifier.
    
    This tool fetches the complete EHR container including its metadata and status.
    The EHR is the top-level container for all clinical data (compositions) for a patient.
    
    Args:
        ehr_id: UUID of the EHR to retrieve (e.g., "7d44b88c-4199-4bad-97dc-d78268e01398").
               Obtain this from openehr_ehr_create, openehr_ehr_list, or 
               openehr_ehr_get_by_subject.
               
    Returns:
        JSON string containing:
        - ehr_id: The EHR's unique identifier
        - system_id: System identifier
        - time_created: When the EHR was created
        - ehr_status: Status object with subject information, modifiable flag, etc.
        - compositions: Reference to associated compositions
        
    Use this tool when:
        - Verifying an EHR exists before creating compositions
        - Retrieving patient identifier information
        - Checking EHR metadata and status
        - Validating EHR accessibility
        
    Example:
        ehr_data = await openehr_ehr_get("7d44b88c-4199-4bad-97dc-d78268e01398")
    """
    if not ehr_id or not isinstance(ehr_id, str):
        return json.dumps({"error": "Invalid or missing ehr_id"}, indent=2)

    logger.info(f"MCP Tool call: openehr_ehr_get for EHR {ehr_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        result = await ehrbase_client.get_ehr(ehr_id)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Retrieved EHR in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error retrieving EHR: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_ehr_list() -> str:
    """List all Electronic Health Records (EHRs) in the openEHR system.
    
    This tool retrieves a complete list of all patient EHR identifiers registered in
    the system. Each EHR represents a unique patient record container. This is useful
    for discovering available patients, system administration, and testing.
    
    Returns:
        JSON string containing:
        - ehr_ids: Array of all EHR UUIDs in the system
        - total: Total count of EHRs
        
    Use this tool when:
        - Discovering all patients in the system
        - Getting an overview of system contents
        - Finding test/demo patient records
        - System administration and auditing
        - Selecting an EHR for testing or demonstration
        
    Note: In production systems with many patients, this query may be slow.
    Consider using openehr_query_adhoc with filters for better performance.
    
    Example response:
        {
          "ehr_ids": [
            "7d44b88c-4199-4bad-97dc-d78268e01398",
            "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
          ],
          "total": 2
        }
    """
    logger.info("MCP Tool call: openehr_ehr_list")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        query = "SELECT e/ehr_id/value AS ehr_id FROM EHR e"
        query_result = await ehrbase_client.execute_adhoc_query(query)

        ehr_ids = []
        if isinstance(query_result, dict) and "rows" in query_result:
            for row in query_result.get("rows", []):
                if row and len(row) > 0:
                    ehr_ids.append(row[0])

        result = {
            "ehr_ids": ehr_ids,
            "total": len(ehr_ids)
        }
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Listed {len(ehr_ids)} EHRs in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error listing EHRs: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg, "ehr_ids": [], "total": 0}, indent=2)


@mcp.tool()
async def openehr_ehr_get_by_subject(subject_id: str, subject_namespace: str) -> str:
    """Retrieve an Electronic Health Record using patient identifier and namespace.
    
    This tool finds an EHR by the patient's external identifier (e.g., hospital MRN,
    national health ID) rather than the internal EHR UUID. This is the primary method
    for locating a patient's EHR using real-world identifiers.
    
    Args:
        subject_id: The patient's external identifier. Examples:
                   - "PATIENT-12345" (hospital medical record number)
                   - "NHS-9876543210" (national health service number)
                   - "SSN-123-45-6789" (social security number)
                   The format depends on your organization's patient ID system.
                   
        subject_namespace: The namespace/system that issued the subject_id.
                          Examples:
                          - "HOSPITAL_MRN" (hospital medical record numbers)
                          - "NHS" (UK National Health Service)
                          - "SSN" (Social Security)
                          - "LOCAL" (local system identifiers)
                          This ensures ID uniqueness across systems.
                          
    Returns:
        JSON string containing the complete EHR record including:
        - ehr_id: Internal UUID for subsequent operations
        - ehr_status: Contains the subject identifier you searched with
        - time_created: When the EHR was created
        - system_id: The openEHR system identifier
        
    Use this tool when:
        - Looking up a patient by their hospital/medical record number
        - Finding an EHR using a national health ID
        - Converting external patient IDs to internal EHR UUIDs
        - Patient lookup during clinical workflows
        
    Workflow:
        1. Get patient's external ID (e.g., MRN from hospital system)
        2. Use this tool to find their EHR
        3. Extract ehr_id from response
        4. Use ehr_id for creating/querying compositions
        
    Example:
        # Find patient by hospital MRN
        result = await openehr_ehr_get_by_subject(
            subject_id="MRN-987654",
            subject_namespace="GENERAL_HOSPITAL"
        )
    """
    if not subject_id or not subject_namespace:
        return json.dumps({"error": "Both subject_id and subject_namespace are required"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_ehr_get_by_subject for subject {subject_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        ehr = await ehrbase_client.get_ehr_by_subject_id(subject_id, subject_namespace)
        result = json.dumps(ehr, indent=2)

        elapsed = time.time() - start_time
        logger.info(
            f"Retrieved EHR for subject {subject_id} in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error retrieving EHR by subject: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)

# COMPOSITION LIFECYCLE TOOLS (same pattern applies to all)


@mcp.tool()
async def openehr_composition_create(composition_data=None, ehr_id=None) -> str:
    """Create a new openEHR composition (clinical document) in the Electronic Health Record.
    
    This tool stores clinical data in the patient's EHR. Compositions are the actual clinical
    documents containing observations, procedures, medications, diagnoses, etc. Each composition
    must conform to a registered template and is stored as an immutable, versioned document.
    
    Args:
        composition_data: JSON object or string containing the clinical data. Must include:
                         - _type: "COMPOSITION"
                         - name: Document name
                         - archetype_details: Template reference
                         - content: Array of clinical entries (observations, actions, etc.)
                         - language, territory, category, composer, context
                         Use openehr_template_example_composition to get valid structure.
                         
        ehr_id: UUID of the patient's EHR where this composition will be stored.
               If omitted, uses the default EHR ID from server configuration.
               Get this from openehr_ehr_create or openehr_ehr_list.
               
    Returns:
        JSON string containing:
        - composition_uid: Unique version identifier (e.g., "abc-123::system::1")
        - composition_id: Base identifier without version
        - Created composition metadata
        
    Use this tool when:
        - Recording new vital signs, lab results, or clinical observations
        - Documenting a patient encounter or procedure
        - Storing medication administration records
        - Creating discharge summaries or clinical notes
        
    Workflow:
        1. Get template structure: openehr_template_example_composition(template_id)
        2. Replace sample data with real patient data
        3. Create composition: openehr_composition_create(composition_data, ehr_id)
        4. Save returned composition_uid for future updates/retrieval
        
    Important: Compositions are immutable once created. Updates create new versions
    using openehr_composition_update with the previous version's UID.
    
    Example:
        # Record vital signs for patient
        vital_signs_data = { /* structured clinical data */ }
        result = await openehr_composition_create(
            composition_data=vital_signs_data,
            ehr_id="7d44b88c-4199-4bad-97dc-d78268e01398"
        )
    """
    if not composition_data:
        return json.dumps({"error": "No composition data provided"}, indent=2)

    target_ehr_id = ehr_id or DEFAULT_EHR_ID

    if not target_ehr_id:
        return json.dumps({"error": "No EHR ID provided or available"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_composition_create for EHR {target_ehr_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        if isinstance(composition_data, str):
            try:
                composition_json = json.loads(composition_data)
            except json.JSONDecodeError:
                return json.dumps({"error": f"Invalid JSON in composition_data"}, indent=2)
        else:
            composition_json = composition_data

        result = await ehrbase_client.create_composition(target_ehr_id, composition_json)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Created composition in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error creating composition: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_composition_get(composition_uid: str, ehr_id=None) -> str:
    """Retrieve an existing openEHR composition (clinical document) by its unique identifier.
    
    Compositions are versioned clinical documents. Each time a composition is updated,
    it gets a new version. The UID includes version information (e.g., "abc-123::system::1").
    This tool retrieves the complete composition content for a specific version.
    
    Args:
        composition_uid: The version-specific unique identifier of the composition.
                        Format: "<composition_id>::<system_id>::<version_number>"
                        Examples:
                        - "8849182c-82ad-4088-a07c-48ead4180515::openEHRSys.example.com::1"
                        - "a1b2c3d4-e5f6-4a7b-8c9d::local::2" (version 2)
                        Get this from openehr_composition_create response or query results.
                        
        ehr_id: UUID of the patient's EHR containing this composition.
               If omitted, uses the default EHR ID from server configuration.
               
    Returns:
        JSON string containing the complete composition including:
        - _type: "COMPOSITION"
        - name: Document title
        - uid: Version-specific identifier
        - archetype_details: Template and archetype information
        - content: Array of clinical entries (observations, procedures, etc.)
        - composer: Who created the document
        - context: Clinical context and metadata
        - language, territory, category: Document properties
        
    Use this tool when:
        - Retrieving previously recorded clinical data
        - Viewing a specific version of a clinical document
        - Reading patient observations, lab results, or encounters
        - Checking what data was recorded at a specific time
        - Before updating a composition (to get current state)
        
    Example:
        # Retrieve vital signs composition
        composition = await openehr_composition_get(
            composition_uid="8849182c-82ad-4088-a07c-48ead4180515::local::1",
            ehr_id="7d44b88c-4199-4bad-97dc-d78268e01398"
        )
    """
    if not composition_uid or not isinstance(composition_uid, str):
        return json.dumps({"error": "Invalid or missing composition_uid"}, indent=2)

    target_ehr_id = ehr_id or DEFAULT_EHR_ID

    if not target_ehr_id:
        return json.dumps({"error": "No EHR ID provided or available"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_composition_get for composition {composition_uid}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        result = await ehrbase_client.get_composition(target_ehr_id, composition_uid)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Retrieved composition in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error retrieving composition: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_composition_update(composition_uid: str, composition_data, ehr_id=None) -> str:
    """Update an existing openEHR composition, creating a new version.
    
    Compositions are immutable and versioned. Updates don't modify the existing version;
    instead, they create a new version while preserving the complete audit trail.
    The version number increments automatically (v1 -> v2 -> v3, etc.).
    
    Args:
        composition_uid: The UID of the PRECEDING version to update.
                        Format: "<composition_id>::<system_id>::<version_number>"
                        Example: "abc-123::local::1" (updating version 1 creates version 2)
                        IMPORTANT: Use the UID from the most recent version.
                        
        composition_data: JSON object or string with the COMPLETE updated composition.
                         Must include all fields (not just changed ones):
                         - _type: "COMPOSITION"
                         - name: Document title
                         - archetype_details: Template reference
                         - content: All clinical entries (with your changes)
                         - composer, context, language, territory, category
                         
                         Workflow to update:
                         1. Get current version: openehr_composition_get(uid)
                         2. Modify the content fields you want to change
                         3. Pass the complete modified composition here
                         
        ehr_id: UUID of the patient's EHR.
               If omitted, uses the default EHR ID from server configuration.
               
    Returns:
        JSON string containing:
        - composition_uid: New version UID (version number incremented)
        - composition_id: Base identifier (unchanged)
        - Updated composition metadata
        
    Use this tool when:
        - Correcting errors in clinical documentation
        - Adding additional observations to an encounter
        - Updating patient status or measurements
        - Amending clinical notes or assessments
        
    Important Notes:
        - ⚠️ All previous versions remain accessible (full audit trail)
        - ⚠️ You must provide the COMPLETE composition (not a partial update)
        - ⚠️ Use the most recent version's UID to avoid conflicts
        - ⚠️ The template structure must remain the same
        
    Example Workflow:
        # 1. Get current composition
        current = await openehr_composition_get("abc-123::local::1")
        
        # 2. Modify it (e.g., update blood pressure reading)
        updated_data = json.loads(current)
        updated_data['content'][0]['data']['events'][0]['data']['items'][0]['value']['magnitude'] = 125
        
        # 3. Save new version
        result = await openehr_composition_update(
            composition_uid="abc-123::local::1",
            composition_data=updated_data,
            ehr_id="7d44b88c-4199-4bad-97dc-d78268e01398"
        )
        # Result will have UID "abc-123::local::2" (version 2)
    """
    if not composition_uid:
        return json.dumps({"error": "No composition UID provided"}, indent=2)

    if not composition_data:
        return json.dumps({"error": "No composition data provided"}, indent=2)

    target_ehr_id = ehr_id or DEFAULT_EHR_ID

    if not target_ehr_id:
        return json.dumps({"error": "No EHR ID provided or available"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_composition_update for composition {composition_uid}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        if isinstance(composition_data, str):
            try:
                composition_json = json.loads(composition_data)
            except json.JSONDecodeError:
                return json.dumps({"error": f"Invalid JSON in composition_data"}, indent=2)
        else:
            composition_json = composition_data

        result = await ehrbase_client.update_composition(target_ehr_id, composition_uid, composition_json)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Updated composition in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error updating composition: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_composition_delete(preceding_version_uid: str, ehr_id=None) -> str:
    """Delete an existing openEHR composition from the Electronic Health Record."""
    if not preceding_version_uid:
        return json.dumps({"error": "No composition version UID provided"}, indent=2)

    target_ehr_id = ehr_id or DEFAULT_EHR_ID

    if not target_ehr_id:
        return json.dumps({"error": "No EHR ID provided or available"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_composition_delete for version {preceding_version_uid}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        result = await ehrbase_client.delete_composition(target_ehr_id, preceding_version_uid)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Deleted composition in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error deleting composition: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_query_adhoc(query: str, query_parameters=None) -> str:
    """Execute an ad-hoc AQL (Archetype Query Language) query against the openEHR server.
    
    AQL is SQL-like query language designed for querying clinical data in openEHR systems.
    It allows complex queries across EHRs, compositions, and specific clinical data points
    while respecting the archetype-based structure of openEHR data.
    
    Args:
        query: AQL query string. Common patterns:
               - SELECT e/ehr_id/value FROM EHR e
               - SELECT c FROM COMPOSITION c WHERE c/name/value = 'Vital Signs'
               - SELECT o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude
                 FROM EHR e CONTAINS COMPOSITION c CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
                 WHERE e/ehr_id/value = $ehr_id
               
        query_parameters: Optional JSON object/string with parameter values for parameterized queries.
                         Use $parameter_name in query, then provide {"parameter_name": "value"}.
                         Prevents SQL injection and improves query reusability.
                         
    Returns:
        JSON string containing:
        - q: The executed query
        - columns: Array of column definitions with name and path
        - rows: Array of result rows (each row is array matching columns)
        - meta: Query metadata (execution time, result count, etc.)
        
    Use this tool when:
        - Searching for patients with specific conditions
        - Retrieving time-series data (e.g., all blood pressure readings)
        - Generating reports across multiple patients
        - Finding compositions by criteria (date range, template, values)
        - Aggregating clinical data for analytics
        
    AQL Key Concepts:
        - FROM clause defines containment: EHR CONTAINS COMPOSITION CONTAINS OBSERVATION
        - Archetype predicates filter by type: OBSERVATION o[openEHR-EHR-OBSERVATION.lab_test.v1]
        - Paths navigate data structure: o/data[at0001]/events[at0002]/data[at0003]
        - WHERE clause filters results
        - Use $parameters for dynamic values
        
    Examples:
        # Find all EHRs
        query: "SELECT e/ehr_id/value FROM EHR e"
        
        # Get vital signs for specific patient
        query: "SELECT c FROM EHR e CONTAINS COMPOSITION c 
                WHERE e/ehr_id/value = $ehr_id AND c/name/value = 'Vital Signs'"
        parameters: {"ehr_id": "7d44b88c-4199-4bad-97dc-d78268e01398"}
        
        # Retrieve blood pressure values over time
        query: "SELECT o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
                       o/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic
                FROM EHR e CONTAINS COMPOSITION c CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
                WHERE e/ehr_id/value = $ehr_id"
    """
    if not query or not isinstance(query, str):
        return json.dumps({"error": "No valid query provided"}, indent=2)

    logger.info(f"MCP Tool call: openehr_query_adhoc")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        params = None
        if query_parameters:
            if isinstance(query_parameters, str):
                try:
                    params = json.loads(query_parameters)
                except json.JSONDecodeError:
                    return json.dumps({"error": f"Invalid JSON in query_parameters"}, indent=2)
            else:
                params = query_parameters

        result = await ehrbase_client.execute_adhoc_query(query, params)
        response = json.dumps(result, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Executed ad-hoc query in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error executing query: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def openehr_compositions_list(template_id: str) -> str:
    """List all compositions created from a specific openEHR template.
    
    This tool finds all clinical documents (compositions) across all patients that
    were created using a particular template. It's useful for finding all instances
    of a specific type of clinical document (e.g., all vital signs, all lab results).
    
    Args:
        template_id: The unique identifier of the template to search for.
                    Examples:
                    - "vital_signs_basic" (find all vital signs records)
                    - "patient_visit_template" (find all patient visits)
                    - "lab_results" (find all lab result documents)
                    Get available templates from openehr_template_list.
                    
    Returns:
        JSON string containing AQL query results with:
        - q: The executed query
        - columns: Column definitions (ehr_id, composition)
        - rows: Array of results, each row contains:
          [0]: ehr_id (which patient this composition belongs to)
          [1]: composition object (the complete composition data)
        - meta: Query metadata
        
    Use this tool when:
        - Finding all vital signs records across patients
        - Listing all lab results for analysis
        - Discovering all documents of a specific type
        - Reporting and analytics across multiple patients
        - Quality assurance and data validation
        - Research and population health queries
        
    Note: Returns compositions from ALL patients. For single-patient queries,
    use openehr_query_adhoc with WHERE clause filtering by ehr_id.
    
    Example:
        # Find all vital signs compositions
        results = await openehr_compositions_list("vital_signs_basic")
        
        # Response structure:
        {
          "rows": [
            [
              "7d44b88c-4199-4bad-97dc-d78268e01398",  # patient 1
              { /* vital signs composition data */ }
            ],
            [
              "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",  # patient 2
              { /* vital signs composition data */ }
            ]
          ]
        }
    """
    if not template_id or not isinstance(template_id, str):
        return json.dumps({"error": "Invalid template_id provided"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_compositions_list for template {template_id}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        query = "SELECT e/ehr_id/value AS ehr_id, c AS composition FROM EHR e CONTAINS COMPOSITION c WHERE c/archetype_details/template_id/value = $template_id"
        query_parameters = {"template_id": template_id}

        result = await ehrbase_client.execute_adhoc_query(query, query_parameters)
        response = json.dumps(result, indent=2)

        composition_count = len(result.get("rows", [])
                                ) if isinstance(result, dict) else 0

        elapsed = time.time() - start_time
        logger.info(
            f"Listed {composition_count} compositions for template {template_id} in {elapsed:.2f}s")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error listing compositions for template {template_id}: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


def _parse_blood_pressure(composition_data: dict) -> dict:
    """Helper function to parse blood pressure from openEHR composition structure with error handling."""
    blood_pressure = {
        "measurements": {},
        "clinical_interpretation": None,
        "comment": None,
        "error": None
    }

    try:
        if not isinstance(composition_data, dict):
            blood_pressure["error"] = "Invalid composition data format"
            return blood_pressure

        for content in composition_data.get("content", []):
            if content.get("_type") == "OBSERVATION" and content.get("name", {}).get("value") == "Blood pressure":
                events = content.get("data", {}).get("events", [])
                for event in events:
                    # Extract numeric values
                    for item in event.get("data", {}).get("items", []):
                        try:
                            name = item.get("name", {}).get("value", "")
                            value = item.get("value", {}).get("magnitude")

                            if name in ["Systolic", "Diastolic", "Mean arterial pressure", "Pulse pressure"]:
                                blood_pressure["measurements"][name] = value
                            elif name == "Clinical interpretation":
                                blood_pressure["clinical_interpretation"] = item.get(
                                    "value", {}).get("value")
                            elif name == "Comment":
                                blood_pressure["comment"] = item.get(
                                    "value", {}).get("value")
                        except Exception as e:
                            logger.warning(f"Error extracting item: {e}")

                    # Extract tilt from state
                    for state_item in event.get("state", {}).get("items", []):
                        try:
                            if state_item.get("name", {}).get("value") == "Tilt":
                                blood_pressure["measurements"]["Tilt"] = state_item.get(
                                    "value", {}).get("magnitude")
                        except Exception as e:
                            logger.warning(f"Error extracting state item: {e}")
    except Exception as e:
        logger.error(f"Error parsing blood pressure: {e}")
        blood_pressure["error"] = str(e)

    return blood_pressure


@mcp.tool()
async def openehr_extract_blood_pressure(ehr_id: str, composition_uid: str) -> str:
    """Extract blood pressure measurements from a composition."""
    if not ehr_id or not composition_uid:
        return json.dumps({"error": "Both ehr_id and composition_uid are required"}, indent=2)

    logger.info(
        f"MCP Tool call: openehr_extract_blood_pressure for composition {composition_uid}")
    start_time = time.time()

    try:
        if not ehrbase_client:
            return json.dumps({"error": "EHRbase client not initialized"}, indent=2)

        composition = await ehrbase_client.get_composition(ehr_id, composition_uid)
        blood_pressure_data = _parse_blood_pressure(composition)
        result = json.dumps(blood_pressure_data, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"Extracted blood pressure data in {elapsed:.2f}s")
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error extracting blood pressure: {str(e)}"
        logger.error(f"{error_msg} after {elapsed:.2f}s")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool(name="suggest_icd_codes")
async def openehr_suggest_icd_codes(
    clinical_text: str,
    limit: int = 5,
    use_gemini: bool = False
) -> str:
    """Suggest ICD-10 diagnostic codes based on clinical text using semantic search.
    
    This tool uses AI-powered semantic similarity search to match clinical descriptions
    to official ICD-10 diagnosis codes. It uses HuggingFace embeddings and Qdrant Cloud
    for vector similarity search to find relevant codes even when exact terminology doesn't match.
    
    🔬 MEDICAL CODING PIPELINE:
    1. Input text is vectorized using sentence-transformers (all-mpnet-base-v2)
    2. Semantic search performed against ICD-10 vector database in Qdrant Cloud
    3. Most similar ICD codes returned with confidence scores
    4. Optional: Gemini AI can enhance clinical text before search
    
    Args:
        clinical_text: Clinical description, symptoms, or diagnosis in natural language.
                      Simple searches work great - just describe the condition!
                      Examples: "cholera",
                               "patient has severe headache and fever",
                               "acute myocardial infarction",
                               "type 2 diabetes with complications"
                               
        limit: Maximum number of ICD-10 codes to return (1-20, default: 5).
              More results provide alternatives but may include less relevant codes.
              
        use_gemini: Whether to use Gemini AI for text enhancement (default: false).
                   When true, uses Google's Gemini model to expand and enrich
                   clinical text before vectorization for better search results.
                   Requires GEMINI_API_KEY in environment.
                   
    Returns:
        Formatted string containing:
        - List of matching ICD-10 codes with descriptions
        - Similarity scores (0-100%) indicating match confidence
        - Total number of codes found
        - Search method used (direct embedding or AI-enhanced)
        
    Use this tool when:
        - Converting clinical notes to standardized diagnosis codes
        - Searching for ICD codes by disease name or symptoms
        - Assisting with medical coding and billing
        - Validating diagnosis code selections
        - Exploring related diagnostic codes
        
    Requirements:
        ✅ Cloud-ready infrastructure:
        - HF_TOKEN: HuggingFace API token for embeddings
        - QDRANT_URL: Qdrant Cloud instance URL
        - QDRANT_API_KEY: Qdrant authentication key
        - GEMINI_API_KEY: (Optional) For clinical text enhancement
        
    Examples:
        # Simple disease search
        result = suggest_icd_codes("cholera")
        # Returns A00.9 (Cholera, unspecified)
        
        # Symptom-based search
        result = suggest_icd_codes("severe diarrhea and dehydration")
        # Returns related gastrointestinal codes
        
        # With AI enhancement for complex queries
        result = suggest_icd_codes(
            "chest pain with shortness of breath",
            limit=10,
            use_gemini=True
        )
        # Returns cardiac-related codes with AI-enhanced clinical context
        
    Note: This tool is cloud-native and works seamlessly in both local and cloud deployment.
          All searches automatically use the embedding → vector search pipeline.
    """
    start_time = time.time()
    
    try:
        if not clinical_text or not isinstance(clinical_text, str):
            return "Error: Please provide valid clinical text"

        clinical_text = clinical_text.strip()
        if not clinical_text:
            return "Error: Clinical text cannot be empty"

        # ⚠️ SAFE INITIALIZATION
        try:
            coding_service = get_medical_coding_service()
        except Exception as e:
            logger.error(f"Medical coding service error: {e}")
            return f"Error: Medical coding service unavailable - {str(e)}"

        if coding_service is None:
            return (
                "Error: Medical coding service not available.\n\n"
                "This feature requires environment variables:\n"
                "1. HF_TOKEN - HuggingFace API token\n"
                "2. QDRANT_URL - Qdrant Cloud instance URL\n"
                "3. QDRANT_API_KEY - Qdrant authentication key\n\n"
                "Please ensure these are set in your .env file."
            )

        logger.info(f"🔍 Searching ICD codes for: '{clinical_text}' (use_gemini={use_gemini})")

        # ⚠️ SAFE SEARCH WITH FULL MEDICAL CODING PIPELINE
        try:
            # The search_icd_codes method automatically:
            # 1. Vectorizes the input text using HuggingFace embeddings
            # 2. Performs semantic search in Qdrant vector database
            # 3. Returns the most similar ICD codes
            results = coding_service.search_icd_codes(
                clinical_text,
                limit=max(1, min(limit, 20)),
                use_gemini_refinement=use_gemini
            )
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return f"Error: Search failed - {str(e)}\n\nPlease ensure Qdrant vector database is accessible."

        # Format response with pipeline information
        if not results:
            response_text = (
                f"No ICD-10 codes found for: '{clinical_text}'\n\n"
                f"🔬 Search method: Embedding vectorization → Semantic search\n"
                f"💡 Tip: Try different phrasing or more descriptive terms"
            )
        else:
            search_method = "AI-enhanced embedding" if use_gemini else "Direct embedding"
            response_text = (
                f"ICD-10 codes for '{clinical_text}':\n"
                f"🔬 Search method: {search_method} → Vector similarity search\n\n"
            )
            
            for i, result in enumerate(results, 1):
                response_text += f"{i}. {result['code']} - {result['description']}\n"
                response_text += f"   📊 Similarity: {result['score']:.2%}\n\n"
            
            response_text += f"Total: {len(results)} codes found"

        elapsed = time.time() - start_time
        logger.info(
            f"✅ Found {len(results) if results else 0} ICD codes in {elapsed:.2f}s")
        return response_text

    except Exception as e:
        logger.error(f"Unexpected error in suggest_icd_codes: {e}", exc_info=True)
        return f"Error: Unexpected error occurred - {str(e)}"


# Run the server
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='openEHR MCP Server')
    parser.add_argument('--transport', type=str, default=None,
                        help=f'Transport type (available: {", ".join(list_transport_plugins())}). Auto-detects if not specified.')
    parser.add_argument('--list-transports', action='store_true',
                        help='List available transport plugins')

    args, unknown = parser.parse_known_args()

    if args.list_transports:
        print("Available transport plugins:")
        for transport_name in list_transport_plugins():
            print(f"  - {transport_name}")
        print(f"\nDefault (auto-detected): {get_default_transport()}")
        sys.exit(0)

    # Use specified transport or auto-detect
    transport_name = args.transport or get_default_transport()
    
    logger.info(f"Starting openEHR MCP Server with {transport_name} transport")

    transport_plugin = get_transport_plugin(transport_name)
    if not transport_plugin:
        logger.error(f"Unknown transport: {transport_name}")
        logger.error(
            f"Available transports: {', '.join(list_transport_plugins())}")
        sys.exit(1)

    # Run the server with the selected transport
    transport_plugin.run(mcp)

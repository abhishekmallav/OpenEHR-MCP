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
    """Lazy initialization of medical coding service with error handling."""
    global medical_coding_service, medical_coding_service_failed

    # If we already tried and failed, don't try again
    if medical_coding_service_failed:
        return None

    if medical_coding_service is None:
        try:
            gemini_key = os.getenv("GEMINI_API_KEY")
            medical_coding_service = MedicalCodingService(
                gemini_api_key=gemini_key
            )
            logger.info("✅ Medical coding service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize medical coding service: {e}")
            logger.error(
                f"   This feature requires: Qdrant running at localhost:6335, ML models, and encodings directory")
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
        try:
            import torch
            if isinstance(obj, torch.Tensor):
                return obj.cpu().numpy().tolist()
        except:
            pass
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
    """Standard I/O transport plugin (default behavior)."""

    def __init__(self):
        super().__init__("stdio")

    def run(self, mcp_server, **kwargs):
        """Run the MCP server with stdio transport."""
        logger.info("Using stdio transport")
        mcp_server.run(transport='stdio')


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

# TOOLS - Actions to perform with templates and EHRs


@mcp.tool()
async def openehr_template_list() -> str:
    """List all available openEHR templates from the EHRbase server."""
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
    """Retrieve a specific openEHR template by its unique identifier."""
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
    """Generate an example openEHR composition based on a specific template."""
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
    """Create a new EHR in the system."""
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
    """Retrieve an EHR by its ID."""
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
    """List all available EHRs in the system."""
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
    """Get an EHR by subject ID and namespace."""
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
    """Create a new openEHR composition in the Electronic Health Record."""
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
    """Retrieve an existing openEHR composition by its unique identifier."""
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
    """Update an existing openEHR composition in the Electronic Health Record."""
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
    """Execute an ad-hoc AQL query against the openEHR server."""
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
    """List all compositions for a specific openEHR template."""
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
    """Suggest ICD-10 codes based on clinical text."""
    logger.info(f"MCP Tool: openehr_suggest_icd_codes")
    start_time = time.time()

    try:
        if not clinical_text or not isinstance(clinical_text, str):
            return "Error: Please provide valid clinical text"

        # ⚠️ SAFE INITIALIZATION
        try:
            coding_service = get_medical_coding_service()
        except Exception as e:
            logger.error(f"Medical coding service error: {e}")
            return f"Error: Medical coding service unavailable - {str(e)}"

        if coding_service is None:
            return (
                "Error: Medical coding service not available.\n\n"
                "This feature requires:\n"
                "1. Qdrant vector database running at localhost:6335\n"
                "2. ML models (sentence-transformers)\n"
                "3. ICD-10 encodings directory with vector data\n\n"
                "When running via Docker, these are not accessible. Run locally instead."
            )

        # ⚠️ SAFE SEARCH
        try:
            results = coding_service.search_icd_codes(
                clinical_text,
                limit=max(1, min(limit, 20)),
                use_gemini_refinement=use_gemini
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Error: Search failed - {str(e)}"

        # Simplified response format for better MCP client compatibility
        if not results:
            response_text = f"No ICD-10 codes found for: {clinical_text}"
        else:
            response_text = f"ICD-10 codes for '{clinical_text}':\n\n"
            for i, result in enumerate(results, 1):
                response_text += f"{i}. {result['code']} - {result['description']}\n"
                response_text += f"   Similarity: {result['score']:.2%}\n\n"
            response_text += f"Total: {len(results)} codes found"

        elapsed = time.time() - start_time
        logger.info(
            f"ICD codes: {len(results) if results else 0} in {elapsed:.2f}s")
        return response_text

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"Error: Unexpected error occurred - {str(e)}"


# Run the server
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='openEHR MCP Server')
    parser.add_argument('--transport', type=str, default='stdio',
                        help=f'Transport type (available: {", ".join(list_transport_plugins())})')
    parser.add_argument('--list-transports', action='store_true',
                        help='List available transport plugins')

    args, unknown = parser.parse_known_args()

    if args.list_transports:
        print("Available transport plugins:")
        for transport_name in list_transport_plugins():
            print(f"  - {transport_name}")
        sys.exit(0)

    logger.info(f"Starting openEHR MCP Server with {args.transport} transport")

    transport_plugin = get_transport_plugin(args.transport)
    if not transport_plugin:
        logger.error(f"Unknown transport: {args.transport}")
        logger.error(
            f"Available transports: {', '.join(list_transport_plugins())}")
        sys.exit(1)

    # Run the server with the selected transport
    transport_plugin.run(mcp)

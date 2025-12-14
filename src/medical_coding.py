"""
Medical coding utilities for ICD-10 code suggestion.
Connects to local Qdrant database for semantic search of ICD-10 codes.
"""
import os
import torch
import numpy as np
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
import logging
import json

# Setup logging
logger = logging.getLogger(__name__)

# Optional: Use Gemini for clinical interpretation refinement
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning(
        "langchain_google_genai not installed. Gemini refinement disabled.")


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy/torch types."""

    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, torch.Tensor):
            return obj.cpu().numpy().tolist()
        return super().default(obj)


class MedicalCodingService:
    """Service for AI-powered medical coding with Qdrant vector database."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        qdrant_url: str = "http://localhost:6335",
        collection_name: str = "icd_mpnet_basev2",
        gemini_api_key: Optional[str] = None
    ):
        """Initialize the medical coding service."""
        self.json_encoder = NumpyEncoder

        try:
            # Setup device (CUDA if available, else CPU)
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"[MedicalCodingService] Using device: {self.device}")

            # Load sentence transformer model
            logger.info(f"[MedicalCodingService] Loading model: {model_name}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(
                    model_name).to(self.device).eval()
                logger.info(
                    f"[MedicalCodingService] Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise

            # Connect to Qdrant
            logger.info(
                f"[MedicalCodingService] Connecting to Qdrant at {qdrant_url}")
            try:
                self.qdrant_client = QdrantClient(url=qdrant_url, timeout=10)
                # Test connection
                self.qdrant_client.get_collections()
                self.collection_name = collection_name
                logger.info(
                    f"[MedicalCodingService] Connected to Qdrant successfully")
            except Exception as e:
                logger.error(
                    f"Failed to connect to Qdrant at {qdrant_url}: {e}")
                raise ConnectionError(
                    f"Cannot connect to Qdrant. Make sure it's running at {qdrant_url}")

            # Verify collection exists
            try:
                collections = self.qdrant_client.get_collections()
                collection_names = [c.name for c in collections.collections]
                if collection_name not in collection_names:
                    logger.warning(
                        f"Collection {collection_name} not found. Available: {collection_names}")
                else:
                    logger.info(
                        f"[MedicalCodingService] Collection {collection_name} found")
            except Exception as e:
                logger.warning(f"Could not verify collection: {e}")

            # Optional: Setup Gemini
            self.llm = None
            if gemini_api_key and GEMINI_AVAILABLE:
                try:
                    os.environ["GOOGLE_API_KEY"] = gemini_api_key
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.0-flash-exp", temperature=0)
                    logger.info(
                        f"[MedicalCodingService] Gemini LLM initialized")
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize Gemini: {e}. Proceeding without Gemini.")

            logger.info(f"[MedicalCodingService] Initialization complete")

        except Exception as e:
            logger.error(
                f"[MedicalCodingService] Fatal initialization error: {e}")
            raise

    def text_to_embedding(self, text: str) -> List[float]:
        """Convert text to embedding vector using mean pooling."""
        try:
            if not text or not isinstance(text, str):
                raise ValueError(f"Invalid text input: {text}")

            text = text.strip()
            if len(text) == 0:
                raise ValueError("Text cannot be empty")

            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=128
            ).to(self.device)

            with torch.no_grad():
                embedding = self.model(
                    **inputs).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

            # Convert numpy to list of floats
            return embedding.astype(np.float32).tolist()

        except Exception as e:
            logger.error(f"Error converting text to embedding: {e}")
            raise

    def refine_clinical_text_with_gemini(self, clinical_text: str) -> List[str]:
        """Use Gemini to extract ICD-10 style diagnostic phrases."""
        if not self.llm:
            logger.debug("Gemini not available, returning original text")
            return [clinical_text] if clinical_text else []

        try:
            if not clinical_text or not isinstance(clinical_text, str):
                logger.warning(f"Invalid clinical text: {clinical_text}")
                return [clinical_text] if clinical_text else []

            prompt = f"""You are a certified ICD-10 coding specialist.

Your goal: From the given *clinical interpretation text*, extract only the distinct diagnostic entities that would be coded in ICD-10.

Guidelines:
1. Use official ICD-10 terminology (e.g., “Calculus of gallbladder”, “Fatty liver”, “Hydronephrosis due to calculus”).
2. Exclude:
   - Duplicate or overlapping terms (e.g., “Calculus of ureter” when already covered by “Hydronephrosis due to ureteric calculus”).
   - General organ descriptions (“liver shows echogenicity”) that are not billable diagnoses.
   - Symptom descriptions or incidental findings unless diagnostic (e.g., skip “mild”, “reactive”, “suggestive” unless part of ICD phrasing).
3. If multiple related findings describe a single condition, **merge them** into one canonical ICD-style phrase.
4. Output only distinct diagnostic phrases, each on a new line — no numbering, no bullets.
5. If the text mentions gallstones or cholelithiasis, rewrite in ICD form as “Calculus of gallbladder …”.

Clinical Interpretation:
{clinical_text}

Output:
"""

            icd_response = self.llm.invoke(prompt).content.strip()

            if not icd_response:
                logger.warning("Gemini returned empty response")
                return [clinical_text]

            queries = [
                q.strip('-• ').strip().rstrip('.')
                for q in icd_response.split('\n')
                if q.strip()
            ]

            if not queries:
                logger.warning("No queries extracted from Gemini response")
                return [clinical_text]

            logger.debug(
                f"Extracted {len(queries)} queries from clinical text")
            return queries

        except Exception as e:
            logger.error(
                f"Gemini refinement failed: {e}. Using original text.")
            return [clinical_text] if clinical_text else []

    def search_icd_codes(
        self,
        clinical_text: str,
        limit: int = 5,
        use_gemini_refinement: bool = False
    ) -> List[Dict]:
        """Search for relevant ICD-10 codes using semantic similarity."""
        try:
            if not clinical_text or not isinstance(clinical_text, str):
                raise ValueError(f"Invalid clinical text: {clinical_text}")

            if limit < 1:
                limit = 5
                logger.warning(f"Invalid limit value, using default: {limit}")

            # Refine text if requested
            if use_gemini_refinement and self.llm:
                queries = self.refine_clinical_text_with_gemini(clinical_text)
                logger.info(f"Refined queries: {queries}")
            else:
                queries = [clinical_text]

            if not queries:
                logger.warning("No queries to search")
                return []

            all_results = []

            for query_text in queries:
                try:
                    # Generate embedding
                    embedding = self.text_to_embedding(query_text)

                    # Ensure embedding is a proper list of floats
                    embedding = [float(x) for x in embedding]

                    # Search Qdrant
                    search_results = self.qdrant_client.query_points(
                        collection_name=self.collection_name,
                        query=embedding,
                        limit=limit,
                        with_payload=True
                    )

                    # Format results with proper type conversion
                    for point in search_results.points:
                        result = {
                            "query": str(query_text),
                            "code": str(point.payload.get('code', 'N/A')),
                            "description": str(point.payload.get('short', 'N/A')),
                            "score": float(point.score)  # Ensure float type
                        }
                        all_results.append(result)

                except Exception as e:
                    logger.error(
                        f"Error searching for query '{query_text}': {e}")
                    continue

            # Sort by score and limit
            all_results.sort(key=lambda x: x['score'], reverse=True)
            final_results = all_results[:limit * len(queries)]

            logger.info(f"Returned {len(final_results)} ICD code suggestions")
            return final_results

        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_icd_codes: {e}")
            raise

    def search_icd_codes_detailed(
        self,
        clinical_text: str,
        limit: int = 5,
        use_gemini_refinement: bool = False
    ) -> Dict:
        """Search with detailed results grouped by query."""
        try:
            if not clinical_text or not isinstance(clinical_text, str):
                raise ValueError(f"Invalid clinical text: {clinical_text}")

            if limit < 1:
                limit = 5

            # Refine text if requested
            if use_gemini_refinement and self.llm:
                queries = self.refine_clinical_text_with_gemini(clinical_text)
            else:
                queries = [clinical_text]

            detailed_results = {
                "original_text": str(clinical_text),
                "refined_queries": [str(q) for q in queries],
                "results_by_query": [],
                "error": None
            }

            if not queries:
                detailed_results["error"] = "No queries to search"
                return detailed_results

            # Search for each query
            for query_text in queries:
                try:
                    embedding = self.text_to_embedding(query_text)
                    embedding = [float(x) for x in embedding]

                    search_results = self.qdrant_client.query_points(
                        collection_name=self.collection_name,
                        query=embedding,
                        limit=limit,
                        with_payload=True
                    )

                    query_results = {
                        "query": str(query_text),
                        "codes": [
                            {
                                "code": str(point.payload.get('code', 'N/A')),
                                "description": str(point.payload.get('short', 'N/A')),
                                "score": float(point.score)
                            }
                            for point in search_results.points
                        ],
                        "error": None
                    }

                    detailed_results["results_by_query"].append(query_results)

                except Exception as e:
                    logger.error(f"Error searching query '{query_text}': {e}")
                    query_results = {
                        "query": str(query_text),
                        "codes": [],
                        "error": str(e)
                    }
                    detailed_results["results_by_query"].append(query_results)

            return detailed_results

        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_icd_codes_detailed: {e}")
            raise

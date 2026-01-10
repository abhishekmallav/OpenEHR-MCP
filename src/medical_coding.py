"""
Cloud-based medical coding service for ICD-10 code retrieval.
Uses HuggingFace embeddings and Qdrant Cloud for semantic search.
"""
import os
from typing import List, Dict, Optional
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()


class MedicalCodingService:
    """Cloud-based medical coding service using HuggingFace and Qdrant Cloud."""

    def __init__(
        self,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "icd_mpnet_basev2"
    ):
        """Initialize the cloud medical coding service."""
        
        # Get credentials from environment or parameters
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name

        # Validate credentials
        if not self.hf_token:
            raise ValueError("HF_TOKEN not found in environment or parameters")
        if not self.qdrant_url:
            raise ValueError("QDRANT_URL not found in environment or parameters")
        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY not found in environment or parameters")

        # Initialize HuggingFace client
        try:
            self.hf_client = InferenceClient(
                provider="auto",
                api_key=self.hf_token,
                model="sentence-transformers/all-mpnet-base-v2",
            )
            logger.info("✅ HuggingFace client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace client: {e}")
            raise

        # Initialize Qdrant client
        try:
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
            # Test connection
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            logger.info(f"✅ Qdrant connected - {collection_info.points_count} points in {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

        # Initialize Gemini (optional)
        self.llm = None
        if self.gemini_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=1.0,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                )
                logger.info("✅ Gemini LLM initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

    def generate_clinical_narrative(self, patient_data: Dict) -> str:
        """Generate clinical narrative from structured patient data using Gemini."""
        if not self.llm:
            # Fallback: simple text generation
            parts = []
            if patient_data.get("doctorRemarks"):
                parts.append(patient_data["doctorRemarks"])
            if patient_data.get("temperature"):
                parts.append(f"Temperature: {patient_data['temperature']}°F")
            if patient_data.get("heartRate"):
                parts.append(f"Heart rate: {patient_data['heartRate']} bpm")
            return " ".join(parts) if parts else "Clinical data provided"

        try:
            messages = [
                (
                    "system",
                    """You are a clinical-text normalization and enrichment engine designed to assist downstream semantic retrieval of ICD-10 diagnostic codes.
                    Your task is to:
                    1. Analyze structured patient vitals, observations, and clinician remarks.
                    2. Convert them into a concise yet semantically rich clinical narrative.
                    3. Use standardized medical terminology commonly aligned with ICD-10 indexing language.
                    4. Explicitly describe conditions, symptoms, observations, and clinical impressions.
                    5. Avoid assigning ICD codes directly.
                    6. Avoid speculative or unsupported diagnoses.
                    7. Do not include treatment plans unless explicitly stated.
                    8. Prefer medically recognized phrasing over casual language.
                    9. Preserve clinical neutrality (observations > conclusions).
                    10. Optimize the output for vector embedding and semantic similarity search.

                    Output requirements:
                    - Output must be plain clinical text (no JSON, no bullet points).
                    - Use complete sentences.
                    - Include relevant vitals, abnormal findings, and physician observations.
                    - Expand implicit clinical meaning where appropriate (e.g., "borderline hypertension" instead of raw BP values).
                    - Do not mention ICD, embeddings, vectors, or databases.
                    - Do not repeat input verbatim; rewrite and normalize it.

                    Your output will be embedded and used for similarity search against an ICD-10 vector database.
                    Accuracy, semantic density, and standardized terminology are critical."""
                ),
                (
                    "human",
                    f"Convert the following structured clinical encounter data into a semantically rich, ICD-retrieval-optimized clinical narrative.\nHere is the data: {patient_data}"
                ),
            ]
            
            ai_msg = self.llm.invoke(messages)
            return ai_msg.content
        except Exception as e:
            logger.error(f"Gemini narrative generation failed: {e}")
            # Fallback
            return patient_data.get("doctorRemarks", str(patient_data))

    def text_to_embedding(self, text: str) -> List[float]:
        """Convert text to embedding vector using HuggingFace."""
        try:
            if not text or not isinstance(text, str):
                raise ValueError(f"Invalid text input: {text}")
            
            text = text.strip()
            if len(text) == 0:
                raise ValueError("Text cannot be empty")
            
            embedding = self.hf_client.feature_extraction(text)
            return embedding
        except Exception as e:
            logger.error(f"Error converting text to embedding: {e}")
            raise

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

            # Generate embedding
            embedding = self.text_to_embedding(clinical_text)

            # Search Qdrant
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=embedding,
                limit=limit,
                with_payload=True
            )

            # Format results
            results = []
            for point in search_results.points:
                code = point.payload.get("code", "N/A")
                # Try to get description from various fields
                description = (
                    point.payload.get("long") or 
                    point.payload.get("short") or 
                    point.payload.get("description", "No description available")
                )
                score = float(point.score)
                
                results.append({
                    "code": str(code),
                    "description": str(description),
                    "score": score
                })

            logger.info(f"Found {len(results)} ICD codes for query: {clinical_text[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error in search_icd_codes: {e}")
            raise

    def search_icd_codes_from_patient_data(
        self,
        patient_data: Dict,
        limit: int = 5,
        use_gemini: bool = True
    ) -> Dict:
        """Search ICD codes from structured patient data."""
        try:
            # Generate clinical narrative
            if use_gemini and self.llm:
                clinical_narrative = self.generate_clinical_narrative(patient_data)
            else:
                clinical_narrative = patient_data.get("doctorRemarks", str(patient_data))

            # Search for ICD codes
            icd_codes = self.search_icd_codes(
                clinical_narrative,
                limit=limit,
                use_gemini_refinement=False  # Already used Gemini for narrative
            )

            return {
                "clinical_narrative": clinical_narrative,
                "icd_codes": icd_codes,
                "total_matches": len(icd_codes)
            }

        except Exception as e:
            logger.error(f"Error in search_icd_codes_from_patient_data: {e}")
            raise

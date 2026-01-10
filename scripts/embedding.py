#!/usr/bin/env python3
"""
General Purpose ICD-10 Embedding Generator for Qdrant Vector Database

This script generates vector embeddings for ICD-10 codes and stores them in Qdrant.
Supports multiple embedding models and automatic GPU acceleration.

Usage:
    python embedding_mpnet_basev2.py --model sentence-transformers/all-mpnet-base-v2
    python embedding_mpnet_basev2.py --model sentence-transformers/all-MiniLM-L6-v2 --collection custom_name
    python embedding_mpnet_basev2.py --csv path/to/diagnosis.csv --qdrant-url http://localhost:6333
"""

import argparse
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from tqdm import tqdm

# ============================================================================
# Configuration - Modify these defaults or use command-line arguments
# ============================================================================

# Default embedding model (can be any sentence-transformers compatible model)
DEFAULT_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Alternative models you can use:
# "sentence-transformers/all-MiniLM-L6-v2"        - Faster, smaller (384 dim)
# "sentence-transformers/all-mpnet-base-v2"       - Balanced (768 dim) - DEFAULT
# "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  - Multilingual
# "BAAI/bge-small-en-v1.5"                        - High quality, small
# "BAAI/bge-base-en-v1.5"                         - High quality, balanced

DEFAULT_CSV_PATH = "diagnosis.csv"
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_BATCH_SIZE = 2000

# ============================================================================
# Device Setup (CPU only - using HuggingFace API for embeddings)
# ============================================================================

def setup_device():
    """Return CPU device - sentence-transformers will handle device selection."""
    device = "cpu"
    print(f"💻 Using CPU for local processing")
    print(f"   Note: sentence-transformers will auto-detect available hardware")
    return device

# ============================================================================
# Embedding Generation
# ============================================================================

def generate_collection_name(model_name):
    """Generate a collection name from the model name."""
    # Extract meaningful part from model path
    # e.g., "sentence-transformers/all-mpnet-base-v2" -> "icd_all_mpnet_base_v2"
    model_basename = model_name.split('/')[-1]
    # Replace hyphens with underscores and add icd prefix
    collection = f"icd_{model_basename.replace('-', '_')}"
    return collection

def load_and_prepare_data(csv_path):
    """Load ICD-10 dataset and prepare text for embedding."""
    print(f"\n📂 Loading dataset from: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}\n"
            "Please ensure you have the ICD-10 diagnosis.csv file.\n"
            "Expected columns: code, short, long"
        )
    
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['code', 'short', 'long']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Fill missing values
    df["short"] = df["short"].fillna("")
    df["long"] = df["long"].fillna("")
    
    print(f"✅ Loaded {len(df)} ICD-10 codes")
    print(f"   Columns: {list(df.columns)}")
    
    # Combine short and long descriptions for better semantic search
    texts = (df["short"] + " " + df["long"]).str.strip()
    # Use code if both descriptions are empty
    texts = texts.where(texts != "", df["code"].astype(str))
    
    return df, texts

def generate_embeddings(texts, model_name, device):
    """Generate embeddings using the specified model."""
    print(f"\n🤖 Loading embedding model: {model_name}")
    print(f"   Note: sentence-transformers will auto-detect best device")
    
    # Let sentence-transformers handle device selection automatically
    model = SentenceTransformer(model_name, trust_remote_code=True)
    embedding_dim = model.get_sentence_embedding_dimension()
    
    print(f"✅ Model loaded successfully")
    print(f"   Embedding dimension: {embedding_dim}")
    
    print(f"\n⚙️  Generating embeddings for {len(texts)} texts...")
    print(f"   This may take several minutes depending on your hardware...")
    
    embeddings = model.encode(
        texts.tolist(),
        normalize_embeddings=True,
        show_progress_bar=True
    )
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    
    return embeddings, embedding_dim

def create_qdrant_collection(client, collection_name, dimension):
    """Create or recreate Qdrant collection."""
    print(f"\n📊 Setting up Qdrant collection: {collection_name}")
    
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if exists:
            print(f"⚠️  Collection '{collection_name}' already exists")
            response = input("   Overwrite? (yes/no): ").strip().lower()
            if response == 'yes':
                client.delete_collection(collection_name)
                print(f"   Deleted existing collection")
            else:
                print(f"   Keeping existing collection, will upsert new data")
                return
        
        # Create new collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
        )
        print(f"✅ Created collection with {dimension} dimensions (COSINE distance)")
        
    except Exception as e:
        print(f"ℹ️  Collection setup: {e}")

def upload_to_qdrant(client, collection_name, df, embeddings, batch_size):
    """Upload embeddings to Qdrant in batches."""
    print(f"\n📤 Uploading embeddings to Qdrant...")
    print(f"   Collection: {collection_name}")
    print(f"   Batch size: {batch_size}")
    
    n = len(df)
    
    for start in tqdm(range(0, n, batch_size), desc="Uploading batches"):
        end = min(start + batch_size, n)
        batch_points = [
            PointStruct(
                id=int(i + 1),
                vector=embeddings[i].tolist(),
                payload={
                    "code": str(df.loc[i, "code"]),
                    "short": str(df.loc[i, "short"]),
                    "long": str(df.loc[i, "long"]),
                },
            )
            for i in range(start, end)
        ]
        client.upsert(collection_name=collection_name, points=batch_points, wait=True)
    
    print(f"✅ Successfully upserted {n} points into '{collection_name}'")

def verify_upload(client, collection_name):
    """Verify the upload by checking collection info."""
    print(f"\n🔍 Verifying upload...")
    
    try:
        collection_info = client.get_collection(collection_name)
        print(f"✅ Collection '{collection_name}' verified")
        print(f"   Points count: {collection_info.points_count}")
        print(f"   Vectors dimension: {collection_info.config.params.vectors.size}")
        print(f"   Distance metric: {collection_info.config.params.vectors.distance}")
    except Exception as e:
        print(f"⚠️  Verification warning: {e}")

# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate ICD-10 embeddings and store in Qdrant vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default settings (all-mpnet-base-v2 model)
  python embedding_mpnet_basev2.py
  
  # Use a different model
  python embedding_mpnet_basev2.py --model sentence-transformers/all-MiniLM-L6-v2
  
  # Specify custom collection name
  python embedding_mpnet_basev2.py --collection my_icd_embeddings
  
  # Use custom CSV file and Qdrant URL
  python embedding_mpnet_basev2.py --csv data/icd10.csv --qdrant-url http://192.168.1.100:6333
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help=f'Embedding model to use (default: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default=None,
        help='Qdrant collection name (default: auto-generated from model name)'
    )
    parser.add_argument(
        '--csv',
        type=str,
        default=DEFAULT_CSV_PATH,
        help=f'Path to ICD-10 CSV file (default: {DEFAULT_CSV_PATH})'
    )
    parser.add_argument(
        '--qdrant-url',
        type=str,
        default=DEFAULT_QDRANT_URL,
        help=f'Qdrant server URL (default: {DEFAULT_QDRANT_URL})'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f'Batch size for uploading (default: {DEFAULT_BATCH_SIZE})'
    )
    
    args = parser.parse_args()
    
    # Generate collection name if not specified
    collection_name = args.collection or generate_collection_name(args.model)
    
    print("=" * 80)
    print("🏥 ICD-10 Embedding Generator for Qdrant")
    print("=" * 80)
    print(f"Model:      {args.model}")
    print(f"Collection: {collection_name}")
    print(f"CSV File:   {args.csv}")
    print(f"Qdrant:     {args.qdrant_url}")
    print("=" * 80)
    
    # Setup device (GPU or CPU)
    device = setup_device()
    
    # Load dataset
    df, texts = load_and_prepare_data(args.csv)
    
    # Generate embeddings
    embeddings, embedding_dim = generate_embeddings(texts, args.model, device)
    
    # Connect to Qdrant
    print(f"\n🔌 Connecting to Qdrant at {args.qdrant_url}")
    try:
        client = QdrantClient(url=args.qdrant_url)
        print(f"✅ Connected to Qdrant")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print(f"   Make sure Qdrant is running: docker compose up -d")
        return
    
    # Create collection
    create_qdrant_collection(client, collection_name, embedding_dim)
    
    # Upload embeddings
    upload_to_qdrant(client, collection_name, df, embeddings, args.batch_size)
    
    # Verify
    verify_upload(client, collection_name)
    
    print("\n" + "=" * 80)
    print("✅ Embedding generation complete!")
    print("=" * 80)
    print(f"\n💡 To use this collection in the MCP server, update medical_coding.py:")
    print(f"   COLLECTION_NAME = '{collection_name}'")
    print(f"   EMBEDDING_MODEL = '{args.model}'")
    print("\n💡 Test the semantic search:")
    print(f"   python tests/test_icd_coding.py")
    print("=" * 80)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test medical coding service directly for cholera.
"""
import sys
import os

# Add src to path (works from any location)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

print("=" * 80)
print("Testing Medical Coding Service for 'cholera'")
print("=" * 80)

# Test 1: Import and initialize
try:
    from medical_coding import MedicalCodingService
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize service
try:
    print("\n📦 Initializing medical coding service...")
    service = MedicalCodingService()
    print("✅ Service initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    print(f"   Make sure Qdrant is running at localhost:6335")
    sys.exit(1)

# Test 3: Search for cholera
try:
    print("\n🔍 Searching for ICD-10 codes for 'cholera'...")
    results = service.search_icd_codes('cholera', limit=5)
    
    if not results:
        print("❌ No results found")
    else:
        print(f"✅ Found {len(results)} ICD-10 codes:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['code']} - {result['description']}")
            print(f"   Similarity: {result['score']:.2%}\n")
            
except Exception as e:
    print(f"❌ Search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 80)
print("✅ All tests passed!")

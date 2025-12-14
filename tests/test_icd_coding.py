#!/usr/bin/env python3
"""
Test script for ICD-10 code suggestion feature in openEHR MCP Server.
"""
import json
import sys
import os

# Add src directory to path (works from any location)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from medical_coding import MedicalCodingService

def test_icd_search():
    """Test ICD-10 code search functionality."""
    
    print("=" * 80)
    print("🧪 Testing ICD-10 Code Suggestion Service")
    print("=" * 80)
    
    # Test cases
    test_queries = [
        "Patient presents with persistent dry cough and mild fever for 3 days",
        "Hypertension with elevated blood pressure readings 160/95 mmHg",
        "Type 2 diabetes mellitus with peripheral neuropathy",
        "Acute myocardial infarction anterior wall",
        "Pneumonia with shortness of breath",
    ]
    
    try:
        print("\n📊 Initializing Medical Coding Service...")
        service = MedicalCodingService()
        print("✅ Service initialized successfully\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'─' * 80}")
            print(f"Test {i}/{len(test_queries)}")
            print(f"{'─' * 80}")
            print(f"📝 Query: {query}\n")
            
            # Search without Gemini refinement
            print("🔍 Searching (basic mode)...")
            results = service.search_icd_codes(query, limit=5, use_gemini_refinement=False)
            
            if results:
                print(f"✅ Found {len(results)} ICD-10 codes:\n")
                for j, result in enumerate(results, 1):
                    print(f"  {j}. {result['code']:8s} - {result['description']}")
                    print(f"     Score: {result['score']:.4f}")
            else:
                print("❌ No results found")
        
        print(f"\n{'=' * 80}")
        print("✅ All tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_with_gemini():
    """Test ICD-10 search with Gemini refinement (requires API key)."""
    
    print("\n" + "=" * 80)
    print("🤖 Testing with Gemini AI Refinement (Optional)")
    print("=" * 80)
    
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set. Skipping Gemini tests.")
        print("   Set it with: export GEMINI_API_KEY='your-key-here'")
        return
    
    try:
        print("\n📊 Initializing service with Gemini...")
        service = MedicalCodingService(gemini_api_key=gemini_key)
        
        query = "Patient has gallstones, fatty liver, and kidney stones with mild hydronephrosis"
        print(f"\n📝 Complex Query: {query}\n")
        
        print("🔍 Searching with Gemini refinement...")
        results = service.search_icd_codes(query, limit=5, use_gemini_refinement=True)
        
        if results:
            print(f"✅ Found {len(results)} ICD-10 codes:\n")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['code']:8s} - {result['description']}")
                print(f"     Query: {result['query']}")
                print(f"     Score: {result['score']:.4f}")
        
        print("\n✅ Gemini test completed")
        
    except Exception as e:
        print(f"⚠️  Gemini test failed: {e}")


if __name__ == "__main__":
    test_icd_search()
    
    # Uncomment to test with Gemini
    # test_with_gemini()
    
    print("\n💡 To test via MCP server, use Claude Desktop with the prompt:")
    print('   "Suggest ICD-10 codes for: Patient with chronic cough and fever"')

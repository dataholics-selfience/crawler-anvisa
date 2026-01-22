#!/usr/bin/env python3
"""
Script de teste para o Anvisa Crawler corrigido
Testa as melhorias aplicadas
"""

import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the fixed crawler
from anvisa_crawler_fixed import anvisa_crawler

async def test_search(molecule: str, brand: str = None):
    """Test a search"""
    print(f"\n{'='*80}")
    print(f"Testing: {molecule}" + (f" ({brand})" if brand else ""))
    print(f"{'='*80}\n")
    
    result = await anvisa_crawler.search_anvisa(
        molecule=molecule,
        brand=brand,
        groq_api_key=None,  # Set to your Groq key if you have one
        use_proxy=False
    )
    
    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Found: {result['found']}")
    print(f"Total products: {result['summary']['total_products']}")
    
    if result['products']:
        print(f"\nFirst product:")
        product = result['products'][0]
        print(f"  Name: {product.get('product_name', 'N/A')}")
        print(f"  Active Ingredient: {product.get('active_ingredient', 'N/A')}")
        print(f"  Company: {product.get('company', 'N/A')}")
        print(f"  Registration Date: {product.get('registration_date', 'N/A')}")
    
    return result

async def main():
    """Run all tests"""
    tests = [
        # Test 1: Darolutamida / Nubeqa (the failing case)
        ("darolutamida", "nubeqa"),
        
        # Test 2: Just molecule
        ("darolutamida", None),
        
        # Test 3: Common drug (should work easily)
        # ("paracetamol", None),
    ]
    
    results = []
    for molecule, brand in tests:
        try:
            result = await test_search(molecule, brand)
            results.append((molecule, brand, result['found'], result['summary']['total_products']))
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}\n")
            results.append((molecule, brand, False, 0))
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}")
    for molecule, brand, found, count in results:
        status = "✅" if found else "❌"
        print(f"{status} {molecule}" + (f" ({brand})" if brand else "") + f": {count} products")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)

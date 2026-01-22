"""
ANVISA API v1.1 - Enhanced with V2 Crawler

FastAPI service for querying Brazilian drug registrations
Now with FULL data extraction (presentations + document links)

V2 Enhancements:
✅ Collects ALL presentations with complete details
✅ Collects ALL document links (Bulário, Parecer, Rotulagem)
✅ Better click strategy (fewer timeouts)
✅ 50 results per page pagination

Usage:
    uvicorn anvisa_main:app --host 0.0.0.0 --port 8000
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import both crawler versions
from anvisa_crawler import anvisa_crawler as crawler_v1

try:
    from anvisa_crawler_v2 import anvisa_crawler_v2 as crawler_v2
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False
    logging.warning("⚠️  V2 crawler not available, only V1 will be used")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("anvisa")

# FastAPI app
app = FastAPI(
    title="Anvisa API",
    description="Brazilian Regulatory Intelligence API for pharmaceutical products",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class AnvisaSearchRequest(BaseModel):
    molecule: str
    brand_name: Optional[str] = None
    groq_api_key: Optional[str] = None
    use_proxy: bool = False

# Response model (for documentation)
class AnvisaSearchResponse(BaseModel):
    found: bool
    products: list
    summary: dict
    search_terms: dict


@app.get("/")
async def root():
    """Health check endpoint"""
    endpoints = {
        "search": "POST /anvisa/search (V1 - original)",
        "search_v2": "POST /anvisa/search/v2 (V2 - enhanced)" if V2_AVAILABLE else "V2 not available",
        "health": "GET /health",
        "test": "GET /test"
    }
    
    return {
        "service": "Anvisa API",
        "version": "1.1.0",
        "status": "online",
        "v2_available": V2_AVAILABLE,
        "endpoints": endpoints,
        "v2_features": [
            "✅ Full presentations extraction",
            "✅ Document links collection",
            "✅ Improved click strategy",
            "✅ 50 results pagination"
        ] if V2_AVAILABLE else []
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy", 
        "service": "anvisa-api",
        "version": "1.1.0",
        "v2_available": V2_AVAILABLE
    }


@app.post("/anvisa/search", response_model=AnvisaSearchResponse)
async def search_anvisa_v1(request: AnvisaSearchRequest):
    """
    Search Anvisa for drug registrations - V1 (Original)
    
    This is the original V1 endpoint, kept for backward compatibility.
    For enhanced data extraction, use /anvisa/search/v2
    
    Args:
        molecule: Molecule name (English) - REQUIRED
        brand_name: Brand/commercial name (optional)
        groq_api_key: Groq API key for translation (optional)
        use_proxy: Enable proxy rotation (default: False)
    
    Returns:
        Dictionary with:
        - found: bool - Whether products were found
        - products: list - List of products with basic details
        - summary: dict - Summary statistics
        - search_terms: dict - Search terms used (EN + PT)
    
    Example:
        {
            "molecule": "darolutamide",
            "brand_name": "nubeqa",
            "groq_api_key": "gsk_xxx",
            "use_proxy": false
        }
    """
    try:
        logger.info(f"🔍 V1 Search request: {request.molecule}" + (f" ({request.brand_name})" if request.brand_name else ""))
        
        # Use env GROQ_API_KEY if not provided in request
        groq_key = request.groq_api_key or os.getenv("GROQ_API_KEY")
        
        # Execute search with V1
        result = await crawler_v1.search_anvisa(
            molecule=request.molecule,
            brand=request.brand_name,
            groq_api_key=groq_key,
            use_proxy=request.use_proxy
        )
        
        logger.info(f"✅ V1 Search completed: {result['summary']['total_products']} products found")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ V1 Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/anvisa/search/v2", response_model=AnvisaSearchResponse)
async def search_anvisa_v2(request: AnvisaSearchRequest):
    """
    Search Anvisa for drug registrations - V2 (Enhanced) ✨
    
    V2 provides FULL data extraction including:
    - ✅ ALL presentations with complete details (description, registration, form, dates)
    - ✅ ALL document links (Bulário Eletrônico, Parecer Público, Rotulagem PDFs)
    - ✅ Better click strategy (fewer timeouts)
    - ✅ 50 results per page pagination
    - ✅ Enhanced summary statistics
    
    Args:
        molecule: Molecule name (English) - REQUIRED
        brand_name: Brand/commercial name (optional)
        groq_api_key: Groq API key for translation (optional)
        use_proxy: Enable proxy rotation (default: False)
    
    Returns:
        Dictionary with:
        - found: bool - Whether products were found
        - products: list - List of products with FULL details
          - Each product includes:
            - presentations: [{ description, registration, pharmaceutical_form, ... }]
            - links: { bulario, parecer_publico, rotulagem: [...] }
        - summary: dict - Enhanced summary statistics
          - total_presentations: int (NEW)
          - documents_available: { bulario, parecer_publico, rotulagem } (NEW)
        - search_terms: dict - Search terms used (EN + PT)
    
    Example Request:
        {
            "molecule": "darolutamide",
            "brand_name": "nubeqa",
            "groq_api_key": "gsk_xxx",
            "use_proxy": false
        }
    
    Example Response:
        {
            "found": true,
            "products": [{
                "product_name": "NUBEQA",
                "presentations": [{
                    "number": "1",
                    "description": "300 MG COM REV CT FR PLAS PEAD OPC X 120",
                    "registration": "170560120001",
                    "pharmaceutical_form": "Comprimido Revestido",
                    "publication_date": "23/12/2019",
                    "validity": "36 meses"
                }],
                "links": {
                    "bulario": "https://...",
                    "parecer_publico": "https://...",
                    "rotulagem": [{"filename": "NUBEQA_FB_LB.PDF", "url": "https://..."}]
                }
            }],
            "summary": {
                "total_products": 1,
                "total_presentations": 1,
                "documents_available": {
                    "bulario": 1,
                    "parecer_publico": 1,
                    "rotulagem": 1
                }
            }
        }
    """
    if not V2_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="V2 crawler not available. Please use /anvisa/search instead."
        )
    
    try:
        logger.info(f"🔍 V2 Search request: {request.molecule}" + (f" ({request.brand_name})" if request.brand_name else ""))
        
        # Use env GROQ_API_KEY if not provided in request
        groq_key = request.groq_api_key or os.getenv("GROQ_API_KEY")
        
        # Execute search with V2
        result = await crawler_v2.search_anvisa(
            molecule=request.molecule,
            brand=request.brand_name,
            groq_api_key=groq_key,
            use_proxy=request.use_proxy
        )
        
        # Log enhanced stats
        total_products = result['summary']['total_products']
        total_presentations = result['summary'].get('total_presentations', 0)
        docs = result['summary'].get('documents_available', {})
        
        logger.info(f"✅ V2 Search completed:")
        logger.info(f"   - Products: {total_products}")
        logger.info(f"   - Presentations: {total_presentations}")
        logger.info(f"   - Documents: Bulário({docs.get('bulario', 0)}) Parecer({docs.get('parecer_publico', 0)}) Rotulagem({docs.get('rotulagem', 0)})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ V2 Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
async def test_endpoint():
    """
    Quick test endpoint - searches for a known drug (aspirin)
    Uses V1 for quick testing
    """
    try:
        result = await crawler_v1.search_anvisa(
            molecule="acetylsalicylic acid",
            brand="aspirin",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            use_proxy=False
        )
        
        return {
            "test": "aspirin (V1)",
            "found": result['found'],
            "products_count": result['summary']['total_products'],
            "products": result['products'][:2] if result['products'] else []  # First 2 only
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/test/v2")
async def test_endpoint_v2():
    """
    Quick test endpoint for V2 - searches for a known drug
    Demonstrates V2's enhanced data extraction
    """
    if not V2_AVAILABLE:
        return {"error": "V2 not available"}
    
    try:
        result = await crawler_v2.search_anvisa(
            molecule="darolutamide",
            brand="nubeqa",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            use_proxy=False
        )
        
        # Show enhanced data
        first_product = result['products'][0] if result['products'] else None
        
        return {
            "test": "nubeqa (V2)",
            "found": result['found'],
            "products_count": result['summary']['total_products'],
            "presentations_count": result['summary'].get('total_presentations', 0),
            "documents_available": result['summary'].get('documents_available', {}),
            "sample_product": {
                "name": first_product.get('product_name') if first_product else None,
                "presentations": first_product.get('presentations', []) if first_product else [],
                "links": first_product.get('links', {}) if first_product else {}
            } if first_product else None
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/compare/{molecule}")
async def compare_versions(molecule: str, brand_name: Optional[str] = None):
    """
    Compare V1 vs V2 results for the same query
    Useful for testing and validation
    
    Example: GET /compare/darolutamide?brand_name=nubeqa
    """
    if not V2_AVAILABLE:
        return {"error": "V2 not available for comparison"}
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    try:
        # Run both searches in parallel
        import asyncio
        v1_result, v2_result = await asyncio.gather(
            crawler_v1.search_anvisa(molecule, brand_name, groq_key, False),
            crawler_v2.search_anvisa(molecule, brand_name, groq_key, False),
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(v1_result, Exception):
            v1_result = {"error": str(v1_result)}
        if isinstance(v2_result, Exception):
            v2_result = {"error": str(v2_result)}
        
        # Build comparison
        comparison = {
            "query": {"molecule": molecule, "brand": brand_name},
            "v1": {
                "products": len(v1_result.get('products', [])),
                "presentations": sum(len(p.get('presentations', [])) for p in v1_result.get('products', [])),
                "has_links": any('links' in p for p in v1_result.get('products', []))
            },
            "v2": {
                "products": len(v2_result.get('products', [])),
                "presentations": sum(len(p.get('presentations', [])) for p in v2_result.get('products', [])),
                "has_links": any(p.get('links', {}).get('bulario') for p in v2_result.get('products', []))
            },
            "improvements": {
                "presentations_gained": None,
                "links_added": None
            }
        }
        
        # Calculate improvements
        v1_pres = comparison['v1']['presentations']
        v2_pres = comparison['v2']['presentations']
        comparison['improvements']['presentations_gained'] = v2_pres - v1_pres
        comparison['improvements']['links_added'] = comparison['v2']['has_links'] and not comparison['v1']['has_links']
        
        return comparison
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    logger.info("=" * 100)
    logger.info("🏥 ANVISA API v1.1")
    logger.info("=" * 100)
    logger.info(f"   Port: {port}")
    logger.info(f"   Endpoints:")
    logger.info(f"      - POST /anvisa/search     (V1 - original)")
    if V2_AVAILABLE:
        logger.info(f"      - POST /anvisa/search/v2  (V2 - enhanced) ✨")
        logger.info(f"      - GET  /test/v2           (V2 quick test)")
        logger.info(f"      - GET  /compare/{{molecule}} (V1 vs V2 comparison)")
    logger.info(f"      - GET  /health            (health check)")
    logger.info(f"      - GET  /test              (V1 quick test)")
    logger.info("=" * 100)
    
    uvicorn.run(app, host="0.0.0.0", port=port)

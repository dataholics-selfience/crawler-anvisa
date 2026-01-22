"""
ANVISA API v1.0 - Standalone Regulatory Intelligence API

FastAPI service for querying Brazilian drug registrations
Designed to be integrated into Pharmyrus later

Usage:
    uvicorn anvisa_main:app --host 0.0.0.0 --port 8000
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from anvisa_crawler import anvisa_crawler

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
    version="1.0.0"
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
    return {
        "service": "Anvisa API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "search": "POST /anvisa/search",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "anvisa-api"}


@app.post("/anvisa/search", response_model=AnvisaSearchResponse)
async def search_anvisa(request: AnvisaSearchRequest):
    """
    Search Anvisa for drug registrations
    
    Args:
        molecule: Molecule name (English) - REQUIRED
        brand_name: Brand/commercial name (optional)
        groq_api_key: Groq API key for translation (optional)
        use_proxy: Enable proxy rotation (default: False)
    
    Returns:
        Dictionary with:
        - found: bool - Whether products were found
        - products: list - List of products with full details
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
        logger.info(f"🔍 Search request: {request.molecule}" + (f" ({request.brand_name})" if request.brand_name else ""))
        
        # Execute search
        result = await anvisa_crawler.search_anvisa(
            molecule=request.molecule,
            brand=request.brand_name,
            groq_api_key=request.groq_api_key,
            use_proxy=request.use_proxy
        )
        
        logger.info(f"✅ Search completed: {result['summary']['total_products']} products found")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
async def test_endpoint():
    """
    Quick test endpoint - searches for a known drug (aspirin)
    """
    try:
        result = await anvisa_crawler.search_anvisa(
            molecule="acetylsalicylic acid",
            brand="aspirin",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            use_proxy=False
        )
        
        return {
            "test": "aspirin",
            "found": result['found'],
            "products_count": result['summary']['total_products'],
            "products": result['products'][:2] if result['products'] else []  # First 2 only
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    logger.info("=" * 100)
    logger.info("🏥 ANVISA API v1.0")
    logger.info("=" * 100)
    logger.info(f"   Port: {port}")
    logger.info(f"   Endpoints:")
    logger.info(f"      - POST /anvisa/search  (main search)")
    logger.info(f"      - GET  /health         (health check)")
    logger.info(f"      - GET  /test           (quick test)")
    logger.info("=" * 100)
    
    uvicorn.run(app, host="0.0.0.0", port=port)

"""
ContextBridge FastAPI Backend
Simple API server for NLP chatbot interface

Endpoints:
- POST /query - Main chat endpoint
- GET /health - Health check
- GET /products - List available products

Usage:
    uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Import ContextBridge orchestrator
from contextbridge_orchestrator import query_contextbridge

# Initialize FastAPI
app = FastAPI(
    title="ContextBridge API",
    description="Unified AI assistant for BidDeed.AI, Michael D1, ZoneWise, Life OS, and SPD",
    version="1.0.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for /query endpoint"""
    query: str
    product: str  # biddeed, michael, zonewise, lifeos, spd
    user_id: Optional[str] = "ariel"
    conversation_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for /query endpoint"""
    success: bool
    query: str
    product: str
    response: str
    intent: Optional[str] = None
    agents_used: List[str] = []
    suggested_actions: List[str] = []
    follow_up_questions: List[str] = []
    processing_time_ms: int
    cost_usd: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class ProductInfo(BaseModel):
    """Product information"""
    id: str
    name: str
    description: str
    example_queries: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "ContextBridge API",
        "version": "1.0.0",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health",
            "products": "GET /products"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@app.get("/products", response_model=List[ProductInfo])
async def get_products():
    """Get list of available products"""
    return [
        ProductInfo(
            id="biddeed",
            name="BidDeed.AI",
            description="Foreclosure auction intelligence",
            example_queries=[
                "What properties are BID recommendations?",
                "How is max bid calculated?",
                "Show December 17 auction properties"
            ]
        ),
        ProductInfo(
            id="michael",
            name="Michael D1 Swimming",
            description="D1 college recruiting pathway",
            example_queries=[
                "What are my target schools?",
                "What's my gap to UF walk-on times?",
                "When are my upcoming meets?"
            ]
        ),
        ProductInfo(
            id="zonewise",
            name="ZoneWise",
            description="Zoning intelligence platform",
            example_queries=[
                "What permits were filed in Melbourne?",
                "What are setback requirements?",
                "Which jurisdictions do we cover?"
            ]
        ),
        ProductInfo(
            id="lifeos",
            name="Life OS",
            description="ADHD productivity tracking",
            example_queries=[
                "How many tasks did I complete this week?",
                "What are my active goals?",
                "Show my current habits"
            ]
        ),
        ProductInfo(
            id="spd",
            name="SPD Site Planning",
            description="Automated site plan development",
            example_queries=[
                "What's the status of Bliss Palm Bay?",
                "What approvals are pending?",
                "Show project timeline"
            ]
        )
    ]


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main chat endpoint
    
    Accepts natural language query and routes to appropriate agents
    Returns synthesized response
    """
    
    # Validate product
    valid_products = ["biddeed", "michael", "zonewise", "lifeos", "spd"]
    if request.product not in valid_products:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product. Must be one of: {', '.join(valid_products)}"
        )
    
    # Validate query
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        # Call ContextBridge orchestrator
        result = query_contextbridge(
            user_query=request.query,
            product=request.product,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        # Format response
        return QueryResponse(
            success=result['workflow_status'] == 'completed',
            query=request.query,
            product=request.product,
            response=result['synthesized_response'],
            intent=result.get('intent', 'unknown'),
            agents_used=result.get('agent_sequence', []),
            suggested_actions=result.get('suggested_actions', []),
            follow_up_questions=result.get('follow_up_questions', []),
            processing_time_ms=result.get('processing_time_ms', 0),
            cost_usd=result.get('cost_usd', 0.0),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Error processing query: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    print("\n" + "="*70)
    print("ContextBridge API Starting...")
    print("="*70)
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Environment:")
    print(f"  ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"  SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
    print(f"  SUPABASE_SERVICE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_KEY') else '❌ Missing'}")
    print("\nEndpoints:")
    print("  GET  /         - API info")
    print("  GET  /health   - Health check")
    print("  GET  /products - List products")
    print("  POST /query    - Main chat endpoint")
    print("\nReady! 🚀")
    print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown"""
    print("\n" + "="*70)
    print("ContextBridge API Shutting Down...")
    print("="*70 + "\n")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("Starting ContextBridge API Server")
    print("="*70)
    print("\nUsage:")
    print("  uvicorn api:app --reload --port 8000")
    print("\nOr run this file directly:")
    print("  python api.py")
    print("\nAPI will be available at:")
    print("  http://localhost:8000")
    print("\nInteractive docs:")
    print("  http://localhost:8000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

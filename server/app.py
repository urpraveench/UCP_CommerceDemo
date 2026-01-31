"""
UCP Business Server - Main FastAPI application.
"""
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
import uvicorn
import os

from .products import get_all_products, search_products, get_product
from .profile import get_business_profile
from .checkout import (
    create_checkout_session,
    get_checkout_session,
    update_checkout_session,
    complete_checkout_session
)
from .ai_agent import process_chat_message, LITELLM_AVAILABLE, LITELLM_MODEL, API_KEY_CONFIGURED
from pydantic import BaseModel
from typing import List, Dict, Any, Optional as Opt
import sys

app = FastAPI(
    title="UCP Business Server",
    description="Universal Commerce Protocol Business Server Demo",
    version="1.0.0"
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for web UI
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")
    
    @app.get("/demo")
    async def serve_demo():
        """Serve the web UI demo."""
        index_path = os.path.join(web_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Web UI not found"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "UCP Business Server",
        "version": "1.0.0",
        "endpoints": {
            "profile": "/.well-known/ucp",
            "products": "/products",
            "checkout": "/checkout-sessions"
        }
    }


@app.get("/.well-known/ucp")
async def get_ucp_profile():
    """
    UCP Business Profile endpoint for agent discovery.
    This endpoint allows AI agents to discover business capabilities.
    """
    return get_business_profile()


@app.get("/products")
async def list_products(
    query: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Product discovery endpoint - UCP compliant.
    Allows agents to search and browse products.
    """
    products = search_products(query=query, category=category)
    
    return {
        "ucp": {
            "version": "2026-01-11",
            "capabilities": [{
                "name": "dev.ucp.shopping.product_discovery",
                "version": "2026-01-11"
            }]
        },
        "products": [product.model_dump() for product in products]
    }


@app.get("/products/{product_id}")
async def get_product_detail(product_id: str):
    """Get a specific product by ID."""
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "ucp": {
            "version": "2026-01-11",
            "capabilities": [{
                "name": "dev.ucp.shopping.product_discovery",
                "version": "2026-01-11"
            }]
        },
        "product": product.model_dump()
    }


@app.post("/checkout-sessions")
async def create_checkout(
    request: Request,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
    request_id: Optional[str] = Header(None, alias="request-id")
):
    """
    Create a new checkout session - UCP compliant.
    """
    try:
        body = await request.json()
        
        line_items = body.get("line_items", [])
        currency = body.get("currency", "USD")
        buyer = body.get("buyer")
        
        session = create_checkout_session(
            line_items=line_items,
            currency=currency,
            buyer=buyer
        )
        
        return session.to_ucp_response()
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/checkout-sessions/{session_id}")
async def get_checkout(session_id: str):
    """Get a checkout session by ID."""
    session = get_checkout_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    
    return session.to_ucp_response()


@app.put("/checkout-sessions/{session_id}")
async def update_checkout(
    session_id: str,
    request: Request,
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
    request_id: Optional[str] = Header(None, alias="request-id")
):
    """
    Update a checkout session - UCP compliant.
    Supports updating line items, applying discounts, etc.
    """
    try:
        body = await request.json()
        
        line_items = body.get("line_items")
        discounts = body.get("discounts")
        buyer = body.get("buyer")
        
        session = update_checkout_session(
            session_id=session_id,
            line_items=line_items,
            discounts=discounts,
            buyer=buyer
        )
        
        return session.to_ucp_response()
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/checkout-sessions/{session_id}/complete")
async def complete_checkout(
    session_id: str,
    request: Request
):
    """
    Complete a checkout session - UCP compliant.
    """
    try:
        session = complete_checkout_session(session_id)
        return session.to_ucp_response()
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# AI Agent Chat Endpoint
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    cart: List[Dict[str, Any]] = []
    checkout_session: Opt[Dict[str, Any]] = None


@app.post("/ai-agent/chat")
async def ai_agent_chat(request: ChatRequest):
    """
    AI Agent chat endpoint for LLM-powered shopping assistant.
    Accepts user message and conversation history, returns LLM response with updated state.
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Log the request for debugging
        logger.info(f"AI Agent chat request: message='{request.message[:50]}...', cart_items={len(request.cart)}")
        
        result = process_chat_message(
            message=request.message,
            conversation_history=request.conversation_history,
            cart=request.cart,
            checkout_session=request.checkout_session
        )
        
        # Log the response for debugging
        logger.info(f"AI Agent response: function_calls={len(result.get('function_calls', []))}")
        
        return {
            "response": result["response"],
            "cart": result["cart"],
            "checkout_session": result.get("checkout_session"),
            "function_calls": result.get("function_calls", [])
        }
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /ai-agent/chat endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@app.get("/ai-agent/status")
async def ai_agent_status():
    """
    Diagnostic endpoint to check AI Agent / LiteLLM configuration status.
    """
    import os
    return {
        "litellm_available": LITELLM_AVAILABLE,
        "litellm_model": LITELLM_MODEL,
        "api_key_configured": API_KEY_CONFIGURED,
        "python_interpreter": sys.executable,
        "python_version": sys.version,
        "environment_vars": {
            "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else None,
            "ANTHROPIC_API_KEY": "***" if os.getenv("ANTHROPIC_API_KEY") else None,
            "OPENROUTER_API_KEY": "***" if os.getenv("OPENROUTER_API_KEY") else None,
            "GEMINI_API_KEY": "***" if os.getenv("GEMINI_API_KEY") else None,
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


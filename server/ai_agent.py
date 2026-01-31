"""
AI Agent service for LLM-powered shopping assistant using LiteLLM.
Integrates with UCP APIs through function calling.
"""
import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Try to import litellm, but handle gracefully if not available
LITELLM_AVAILABLE = False
litellm = None
import_error = None

try:
    import litellm
    LITELLM_AVAILABLE = True
    print(f"[AI Agent] ✅ LiteLLM imported successfully (version: {getattr(litellm, '__version__', 'unknown')})")
except ImportError as e:
    LITELLM_AVAILABLE = False
    litellm = None
    import_error = str(e)
    print(f"[AI Agent] ❌ LiteLLM import failed (ImportError): {import_error}")
except Exception as e:
    LITELLM_AVAILABLE = False
    litellm = None
    import_error = str(e)
    print(f"[AI Agent] ❌ LiteLLM import failed (unexpected error): {type(e).__name__}: {import_error}")

from .products import search_products, get_product, get_all_products, Product
from .checkout import (
    create_checkout_session,
    get_checkout_session,
    update_checkout_session,
    complete_checkout_session
)
from .shopping_behavior import extract_behavior_from_conversation, ShoppingBehaviorTracker

# Load environment variables
# Try loading from multiple locations: root folder first, then server folder

# Get the project root directory (parent of server directory)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent  # Go up from server/ai_agent.py to project root
server_dir = current_file.parent  # server directory

# Try loading .env from root folder first, then server folder
env_loaded = False
env_paths = [
    project_root / ".env",      # Root folder (preferred location)
    server_dir / ".env",        # Server folder (fallback)
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"[AI Agent] ✅ Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print(f"[AI Agent] ⚠️  No .env file found. Checked:")
    for env_path in env_paths:
        print(f"  - {env_path} ({'exists' if env_path.exists() else 'not found'})")
    print(f"[AI Agent] 💡 Tip: Create .env file in project root with your API keys")

# Print diagnostic information
print(f"[AI Agent] Python interpreter: {sys.executable}")
print(f"[AI Agent] Python version: {sys.version}")

# LiteLLM configuration
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "openai/gpt-4o-mini")
print(f"[AI Agent] LiteLLM model configured: {LITELLM_MODEL}")

# Check if any API key is configured
# LiteLLM will automatically use the appropriate API key based on the model
# For OpenAI: OPENAI_API_KEY
# For Anthropic: ANTHROPIC_API_KEY
# For OpenRouter: OPENROUTER_API_KEY
# For Google: GEMINI_API_KEY
# etc.
API_KEY_CONFIGURED = (
    os.getenv("OPENAI_API_KEY") or
    os.getenv("ANTHROPIC_API_KEY") or
    os.getenv("OPENROUTER_API_KEY") or
    os.getenv("GEMINI_API_KEY")
)

if API_KEY_CONFIGURED:
    print(f"[AI Agent] ✅ API key configured")
else:
    print(f"[AI Agent] ❌ No API key found. Please set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY")


def get_system_prompt(shopping_behavior: Optional[str] = None) -> str:
    """Get the system prompt for the AI shopping agent.
    
    Args:
        shopping_behavior: Optional natural language summary of user shopping behavior
    
    Returns:
        The composed system prompt string
    """
    try:
        from .prompts import System_Prompt, User_Shopping_behaviour
        
        prompt = System_Prompt
        
        # Build behavior context: always include User_Shopping_behaviour, then add dynamic behavior if available
        behavior_context_parts = [User_Shopping_behaviour]
        if shopping_behavior:
            behavior_context_parts.append(shopping_behavior)
        
        behavior_context = "\n\n".join(behavior_context_parts)
        
        # Replace behavior placeholder with the combined behavior context
        prompt = prompt.replace("{{BEHAVIOR_SUMMARY}}", behavior_context)
        
        return prompt.strip()
        
    except ImportError:
        print(f"[AI Agent] ⚠️  prompts.py not found, using fallback prompt")
        return _get_default_fallback_prompt()
    except Exception as e:
        print(f"[AI Agent] ❌ Error loading prompt: {e}, using fallback prompt")
        return _get_default_fallback_prompt()


def _get_default_fallback_prompt() -> str:
    """Default fallback prompt if prompts.py is not available."""
    return """You are a helpful and friendly AI shopping assistant powered by the Universal Commerce Protocol (UCP). 
Your role is to help users discover products, manage their shopping cart, and complete purchases through natural conversation.

You have access to the following capabilities through function calling:
- Search for products by query or category
- Get detailed information about specific products
- Add items to the user's shopping cart
- View the current cart contents
- Apply discount codes
- Create and manage checkout sessions
- Complete purchases

Guidelines:
- Be conversational, friendly, and helpful
- When users search for products, use the search_products function
- When users want to add items, use add_to_cart function
- Always confirm actions clearly (e.g., "I've added X to your cart")
- If a user asks about a product, use get_product_details to get full information
- When showing products, highlight key features like price, rating, and category
- If the user's request is ambiguous, ask clarifying questions
- Remember context from the conversation
- Use natural language - don't sound robotic
- If you need to show multiple products, summarize them clearly

Example interactions:
- User: "Show me laptops" → Call search_products(query="laptop"), then describe the results
- User: "Add the first one to cart" → Call add_to_cart with the product ID from previous search
- User: "What's in my cart?" → Call view_cart(), then summarize the items
- User: "Apply discount 10OFF" → Call apply_discount(code="10OFF")
- User: "Checkout" → Call create_checkout() then complete_checkout()

Always be helpful and make shopping easy and enjoyable!"""


def get_ucp_tools() -> List[Dict[str, Any]]:
    """Define function calling tools for UCP operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": "Search for products by query string or category. Use this when the user wants to find products.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find products (e.g., 'laptop', 'headphones', 'coffee maker')"
                        },
                        "category": {
                            "type": "string",
                            "description": "Product category filter (e.g., 'Electronics', 'Home & Kitchen', 'Sports & Fitness')"
                        }
                    }
                },
                "required": []
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product including description, technical specs, ratings, and reviews.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The ID of the product to get details for"
                        }
                    },
                    "required": ["product_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_to_cart",
                "description": "Add a product to the user's shopping cart. Use this when the user wants to add an item.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The ID of the product to add to cart"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to add (default is 1)",
                            "default": 1
                        }
                    },
                    "required": ["product_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_cart",
                "description": "Get the current contents of the user's shopping cart including items, quantities, and totals.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "apply_discount",
                "description": "Apply a discount code to the cart. Use this when the user wants to use a coupon or discount code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The discount code to apply (e.g., '10OFF', 'SAVE20', 'FREESHIP')"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_checkout",
                "description": "Create a checkout session for the current cart. Use this when the user is ready to checkout.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "buyer_name": {
                            "type": "string",
                            "description": "Buyer's full name",
                            "default": "Customer"
                        },
                        "buyer_email": {
                            "type": "string",
                            "description": "Buyer's email address",
                            "default": "customer@example.com"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "complete_checkout",
                "description": "Complete the checkout and finalize the purchase. Use this when the user confirms they want to complete the purchase.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    ]


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert Pydantic models and AnyUrl objects to JSON-serializable types.
    """
    if hasattr(obj, 'model_dump'):
        # Pydantic model - use mode='json' to convert AnyUrl to str
        return obj.model_dump(mode='json')
    elif hasattr(obj, '__str__') and hasattr(obj, '__class__') and 'Url' in obj.__class__.__name__:
        # AnyUrl or similar URL type - convert to string
        return str(obj)
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj


def execute_ucp_function(
    function_name: str,
    arguments: Dict[str, Any],
    cart: List[Dict[str, Any]],
    checkout_session: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute UCP API function calls based on LLM function requests."""
    result = {"success": False, "data": None, "error": None, "cart": cart, "checkout_session": checkout_session}
    
    try:
        if function_name == "search_products":
            query = arguments.get("query")
            category = arguments.get("category")
            products = search_products(query=query, category=category)
            # Use mode='json' to ensure AnyUrl and other Pydantic types are JSON-serializable
            result["data"] = {
                "products": [product.model_dump(mode='json') for product in products],
                "count": len(products)
            }
            result["success"] = True
            
        elif function_name == "get_product_details":
            product_id = arguments.get("product_id")
            product = get_product(product_id)
            if product:
                # Use mode='json' to ensure AnyUrl and other Pydantic types are JSON-serializable
                result["data"] = product.model_dump(mode='json')
                result["success"] = True
            else:
                result["error"] = f"Product {product_id} not found"
                
        elif function_name == "add_to_cart":
            product_id = arguments.get("product_id")
            quantity = arguments.get("quantity", 1)
            product = get_product(product_id)
            
            if not product:
                result["error"] = f"Product {product_id} not found"
                return result
                
            # Add to cart
            existing_item = next((item for item in cart if item.get("id") == product_id), None)
            if existing_item:
                existing_item["quantity"] = existing_item.get("quantity", 1) + quantity
            else:
                cart.append({
                    "id": product_id,
                    "title": product.title,
                    "price": product.price,
                    "quantity": quantity
                })
            
            result["cart"] = cart
            result["data"] = {
                "product": product.title,
                "quantity": quantity,
                "message": f"Added {product.title} to cart"
            }
            result["success"] = True
            
        elif function_name == "view_cart":
            subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart)
            result["data"] = {
                "items": cart,
                "subtotal": subtotal,
                "item_count": len(cart),
                "total_items": sum(item.get("quantity", 1) for item in cart)
            }
            result["success"] = True
            
        elif function_name == "apply_discount":
            code = arguments.get("code", "").upper()
            if not cart:
                result["error"] = "Cart is empty. Add items before applying discount."
                return result
                
            # Create or update checkout session with discount
            line_items = [{
                "item": {
                    "id": item["id"],
                    "title": item["title"],
                    "price": item["price"]
                },
                "quantity": item.get("quantity", 1)
            } for item in cart]
            
            buyer = {
                "full_name": "Customer",
                "email": "customer@example.com"
            }
            
            if checkout_session:
                # Update existing session
                session = update_checkout_session(
                    session_id=checkout_session["id"],
                    line_items=line_items,
                    discounts={"codes": [code]},
                    buyer=buyer
                )
            else:
                # Create new session
                session = create_checkout_session(
                    line_items=line_items,
                    currency="USD",
                    buyer=buyer
                )
                # Apply discount after creating session
                try:
                    session.apply_discount(code)
                except ValueError:
                    pass  # Ignore invalid discount codes
            
            checkout_session = session.to_ucp_response()
            # Ensure JSON serializable
            checkout_session = make_json_serializable(checkout_session)
            result["checkout_session"] = checkout_session
            result["data"] = {
                "code": code,
                "discount_applied": True,
                "message": f"Discount code {code} applied successfully"
            }
            result["success"] = True
            
        elif function_name == "create_checkout":
            if not cart:
                result["error"] = "Cart is empty. Add items before checkout."
                return result
                
            buyer_name = arguments.get("buyer_name", "Customer")
            buyer_email = arguments.get("buyer_email", "customer@example.com")
            
            line_items = [{
                "item": {
                    "id": item["id"],
                    "title": item["title"],
                    "price": item["price"]
                },
                "quantity": item.get("quantity", 1)
            } for item in cart]
            
            session = create_checkout_session(
                line_items=line_items,
                currency="USD",
                buyer={
                    "full_name": buyer_name,
                    "email": buyer_email
                }
            )
            
            checkout_session = session.to_ucp_response()
            # Ensure JSON serializable
            checkout_session = make_json_serializable(checkout_session)
            result["checkout_session"] = checkout_session
            result["data"] = {
                "session_id": session.id,
                "status": session.status,
                "message": "Checkout session created"
            }
            result["success"] = True
            
        elif function_name == "complete_checkout":
            if not checkout_session:
                result["error"] = "No checkout session. Please create one first."
                return result
                
            session = complete_checkout_session(checkout_session["id"])
            completed_session = session.to_ucp_response()
            # Ensure JSON serializable
            completed_session = make_json_serializable(completed_session)
            
            # Clear cart after successful checkout
            cart = []
            
            result["cart"] = cart
            result["checkout_session"] = None
            result["data"] = {
                "status": "completed",
                "message": "Purchase completed successfully!"
            }
            result["success"] = True
            
        else:
            result["error"] = f"Unknown function: {function_name}"
            
    except Exception as e:
        result["error"] = str(e)
        
    return result


def process_chat_message(
    message: str,
    conversation_history: List[Dict[str, str]],
    cart: List[Dict[str, Any]],
    checkout_session: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a chat message using LLM with function calling.
    
    Returns:
        {
            "response": str,
            "cart": List[Dict],
            "checkout_session": Dict,
            "function_calls": List[Dict]
        }
    """
    if not LITELLM_AVAILABLE:
        error_msg = "LLM service is not available. "
        if import_error:
            error_msg += f"Import error: {import_error}. "
        error_msg += "Please ensure:\n1. litellm is installed: `pip install litellm`\n2. You're using the correct Python interpreter from your virtual environment\n3. If using uvicorn, run: `python run_server.py` or `python -m uvicorn server.app:app`"
        return {
            "response": error_msg,
            "cart": cart,
            "checkout_session": checkout_session,
            "function_calls": []
        }
    
    if not API_KEY_CONFIGURED:
        return {
            "response": "LLM service is not configured. Please set an API key environment variable (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY) and LITELLM_MODEL.",
            "cart": cart,
            "checkout_session": checkout_session,
            "function_calls": []
        }
    
    # Extract shopping behavior from conversation history and cart
    behavior_tracker = extract_behavior_from_conversation(
        conversation_history=conversation_history,
        cart=cart
    )
    
    # Generate behavior summary
    behavior_summary = behavior_tracker.generate_behavior_summary()
    
    # Build conversation messages
    # Ensure all messages are in dict format for LiteLLM
    messages = [
        {"role": "system", "content": get_system_prompt(shopping_behavior=behavior_summary)}
    ]
    
    # Add conversation history (limit to last 10 messages to manage context)
    for msg in conversation_history[-10:]:
        # Ensure message is in dict format
        if isinstance(msg, dict):
            messages.append(msg)
        else:
            messages.append({
                "role": getattr(msg, 'role', 'user'),
                "content": getattr(msg, 'content', '')
            })
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    # Add cart context to system message if cart has items
    if cart:
        cart_summary = f"\n\nCurrent cart contains {len(cart)} item(s): " + ", ".join([f"{item.get('title')} (x{item.get('quantity', 1)})" for item in cart])
        messages[0]["content"] += cart_summary
    
    function_calls_made = []
    max_iterations = 5  # Prevent infinite loops
    iteration = 0
    current_cart = cart.copy()
    current_checkout = checkout_session
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            if not LITELLM_AVAILABLE:
                raise ImportError("litellm is not installed or not available in the current Python environment")
            
            # Call LLM with function calling using LiteLLM
            # LiteLLM uses OpenAI-compatible API
            response = litellm.completion(
                model=LITELLM_MODEL,
                messages=messages,
                tools=get_ucp_tools(),
                tool_choice="auto"
            )
            
            # Extract assistant message from response
            assistant_message = response.choices[0].message
            
            # Convert to dict format for message history (LiteLLM returns OpenAI-compatible format)
            assistant_msg_dict = {
                "role": "assistant",
                "content": getattr(assistant_message, 'content', None)
            }
            
            # Handle tool calls if present
            tool_calls = getattr(assistant_message, 'tool_calls', None)
            if tool_calls:
                # Convert tool calls to dict format
                tool_calls_list = []
                for tc in tool_calls:
                    if hasattr(tc, 'function'):
                        tool_calls_list.append({
                            "id": getattr(tc, 'id', None),
                            "type": "function",
                            "function": {
                                "name": getattr(tc.function, 'name', ''),
                                "arguments": getattr(tc.function, 'arguments', '{}')
                            }
                        })
                    elif isinstance(tc, dict):
                        tool_calls_list.append(tc)
                
                if tool_calls_list:
                    assistant_msg_dict["tool_calls"] = tool_calls_list
            
            messages.append(assistant_msg_dict)
            
            # Check if LLM wants to call a function
            if tool_calls and len(tool_calls) > 0:
                for tool_call in tool_calls:
                    # Extract function name and arguments
                    if hasattr(tool_call, 'function'):
                        function_name = getattr(tool_call.function, 'name', '')
                        function_args_str = getattr(tool_call.function, 'arguments', '{}')
                    else:
                        # Handle dict format
                        func_data = tool_call.get('function', {}) if isinstance(tool_call, dict) else {}
                        function_name = func_data.get('name', '')
                        function_args_str = func_data.get('arguments', '{}')
                    
                    try:
                        arguments = json.loads(function_args_str) if isinstance(function_args_str, str) else function_args_str
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}
                    
                    # Execute the function
                    function_result = execute_ucp_function(
                        function_name,
                        arguments,
                        current_cart,
                        current_checkout
                    )
                    
                    # Track behavior for search results
                    if function_name == "search_products" and function_result.get("success"):
                        products_data = function_result.get("data", {}).get("products", [])
                        if products_data:
                            for product_data in products_data:
                                product_id = product_data.get("id")
                                if product_id:
                                    behavior_tracker.track_view(product_id)
                    
                    # Update state
                    current_cart = function_result.get("cart", current_cart)
                    if "checkout_session" in function_result:
                        current_checkout = function_result.get("checkout_session")
                    
                    # Track cart additions
                    if function_name == "add_to_cart" and function_result.get("success"):
                        product_id = arguments.get("product_id")
                        if product_id:
                            behavior_tracker.track_cart_addition(product_id)
                    
                    # Record function call
                    function_calls_made.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": function_result
                    })
                    
                    # Add function result to messages for LLM
                    # Ensure all data is JSON-serializable (convert AnyUrl to str, etc.)
                    tool_call_id = getattr(tool_call, 'id', None) if hasattr(tool_call, 'id') else tool_call.get('id', None) if isinstance(tool_call, dict) else None
                    serializable_result = {
                        "success": function_result["success"],
                        "data": make_json_serializable(function_result.get("data")),
                        "error": function_result.get("error")
                    }
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(serializable_result)
                    })
            else:
                # LLM provided a final response, break loop
                break
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in LLM call: {str(e)}")
            print(f"Traceback: {error_details}")
            # Log the error but don't break the loop - try to return a helpful message
            if iteration == 1:
                # First iteration failed, return error
                return {
                    "response": f"I encountered an error: {str(e)}. Please check:\n1. Your API key is set correctly in .env file\n2. The model '{LITELLM_MODEL}' is valid for your provider\n3. You have sufficient API credits\n\nError type: {type(e).__name__}",
                    "cart": current_cart,
                    "checkout_session": current_checkout,
                    "function_calls": function_calls_made
                }
            # Continue to next iteration if we have function calls to process
            break
    
    # Get final response text
    # Handle case where assistant_message might not be defined
    if 'assistant_message' not in locals() or not assistant_message:
        final_response = "I'm here to help you shop! How can I assist you today?"
    else:
        # Try to get content from assistant_message object or dict
        if hasattr(assistant_message, 'content'):
            final_response = assistant_message.content if assistant_message.content else "I'm here to help you shop!"
        elif isinstance(assistant_message, dict):
            final_response = assistant_message.get('content', "I'm here to help you shop!")
        else:
            final_response = "I'm here to help you shop!"
    
    return {
        "response": final_response,
        "cart": current_cart,
        "checkout_session": current_checkout,
        "function_calls": function_calls_made
    }


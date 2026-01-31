# UCP Prototype Application

A complete demonstration of the **Universal Commerce Protocol (UCP)** - an open-source standard for agentic commerce that enables seamless shopping experiences across AI platforms.

![UCP Demo](https://img.shields.io/badge/UCP-2026--01--11-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)

## 🎯 Overview

This prototype demonstrates how businesses can integrate with UCP to enable AI agents (like Google's AI Mode in Search and Gemini) to discover products, create checkout sessions, and complete purchases seamlessly.

### What is UCP?

The Universal Commerce Protocol (UCP) is an open-source standard developed by Google in collaboration with industry leaders including Shopify, Etsy, Wayfair, Target, and Walmart. It enables:

- **Unified Integration**: Single integration point for all consumer surfaces
- **Agentic Commerce**: Seamless shopping experiences through AI agents
- **Flexible Architecture**: Support for APIs, Agent2Agent (A2A), and Model Context Protocol (MCP)
- **Security-First**: Tokenized payments and verifiable credentials

Learn more: [UCP Official Documentation](https://developers.google.com/merchant/ucp)

## ✨ Features

This prototype implements:

1. **Business Profile Discovery** (`/.well-known/ucp`)
   - AI agents can discover business capabilities
   - Payment handler and instrument configurations
   - Capability bindings (REST, MCP, A2A)

2. **Product Discovery** (`/products`)
   - Search and browse products
   - UCP-compliant product responses
   - Category filtering

3. **Checkout Flow** (`/checkout-sessions`)
   - Create checkout sessions
   - Update sessions (apply discounts)
   - Complete checkout
   - Line items and totals calculation

4. **Interactive Web UI**
   - Modern, responsive design
   - Real-time API interaction
   - Shopping cart management
   - Discount code application

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager

### Installation

1. **Clone this repository**
   ```bash
   git clone <your-repo-url>
   cd UCP
   ```

2. **Set up UCP SDK** (if not already cloned)
   ```bash
   mkdir -p sdk
   git clone https://github.com/Universal-Commerce-Protocol/python-sdk.git sdk/python
   cd sdk/python
   pip install -e .
   cd ../..
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or
   uv pip install -r requirements.txt
   ```

4. **Configure LLM (for AI Agent Shopping)**
   
   **Install LiteLLM** (if not already installed):
   ```bash
   pip install litellm
   ```
   
   Create a `.env` file in the project root with your LLM provider API key:
   ```bash
   # For OpenAI (Recommended for testing)
   LITELLM_MODEL=openai/gpt-4o-mini
   OPENAI_API_KEY=your_openai_api_key_here
   
   # For Anthropic Claude
   # LITELLM_MODEL=anthropic/claude-3-haiku
   # ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # For OpenRouter
   # LITELLM_MODEL=openrouter/openai/gpt-4o-mini
   # OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   # For Google Gemini
   # LITELLM_MODEL=gemini/gemini-pro
   # GEMINI_API_KEY=your_gemini_api_key_here
   ```
   
   LiteLLM supports many providers. See [LiteLLM documentation](https://docs.litellm.ai/) for full list.
   
   **Verify Installation:**
   ```bash
   # Check LiteLLM is installed
   python -c "import litellm; print('LiteLLM version:', litellm.__version__)"
   
   # Verify API key is set
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Model:', os.getenv('LITELLM_MODEL')); print('API Key set:', bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')))"
   ```

5. **Start the server**
   ```bash
   python run_server.py
   # or
   uvicorn server.app:app --reload --port 8000
   ```

4. **Open the web UI**
   - Navigate to: `http://localhost:8000/demo`
   - Or open `web/index.html` directly in your browser (with CORS disabled or using a local server)

## 📖 Demo Walkthrough

### Prerequisites

1. Server is running on `http://localhost:8000`
2. Web UI is accessible at `http://localhost:8000/demo` or open `web/index.html`

### Step 1: Business Profile Discovery

**Goal**: Show how AI agents discover business capabilities

1. Open the web UI
2. Click "Discover Business Profile" button
3. Observe the UCP profile response showing:
   - Business information
   - Available capabilities (product_discovery, checkout)
   - Payment handlers and instruments
   - REST API bindings

**Key Point**: This is the endpoint (`/.well-known/ucp`) that AI agents query to understand what your business can do.

### Step 2: Product Discovery

**Goal**: Demonstrate UCP-compliant product search

1. Click "Load All Products" to see the full catalog
2. Try searching for "laptop" or "headphones"
3. Observe the UCP-compliant response structure:
   - UCP version header
   - Capability declaration
   - Product data with prices in cents

**Key Point**: Products are returned in UCP format, making them discoverable by AI agents.

### Step 3: Shopping Cart

**Goal**: Show cart management

1. Add multiple products to cart
2. Adjust quantities using +/- buttons
3. Remove items
4. Observe real-time total calculations

**Key Point**: Cart is managed client-side before creating a checkout session.

### Step 4: Create Checkout Session

**Goal**: Demonstrate UCP checkout session creation

1. Ensure cart has items
2. Enter buyer information (name and email)
3. Click "Create Checkout Session"
4. Observe the UCP checkout response:
   - Session ID
   - Line items with totals
   - Buyer information
   - Status: "ready_for_complete"
   - Payment handlers and instruments

**Key Point**: This creates a UCP-compliant checkout session that AI agents can manage.

### Step 5: Apply Discount

**Goal**: Show checkout session updates

1. Enter a discount code:
   - `10OFF` - 10% off
   - `SAVE20` - 20% off
   - `FREESHIP` - $5.00 off
2. Click "Apply Discount"
3. Observe:
   - Discount appears in totals
   - Applied discounts in response
   - Updated final total

**Key Point**: UCP supports dynamic checkout updates, allowing agents to apply discounts, change quantities, etc.

### Step 6: Complete Checkout

**Goal**: Finalize the purchase

1. Click "Complete Checkout"
2. Observe:
   - Status changes to "completed"
   - Success message
   - Cart resets

**Key Point**: This completes the UCP checkout flow, simulating a successful purchase.

## 🔌 API Endpoints

### Business Profile
```
GET /.well-known/ucp
```
Returns the UCP business profile for agent discovery.

### Product Discovery
```
GET /products
GET /products?query=laptop
GET /products?category=Electronics
GET /products/{product_id}
```

### Checkout
```
POST /checkout-sessions
PUT /checkout-sessions/{session_id}
GET /checkout-sessions/{session_id}
POST /checkout-sessions/{session_id}/complete
```

All endpoints return UCP-compliant responses with proper version headers and capability declarations.

### API Request Examples

#### Discover Business Profile
```bash
curl http://localhost:8000/.well-known/ucp
```

#### Search Products
```bash
curl "http://localhost:8000/products?query=laptop"
```

#### Create Checkout Session
```bash
curl -X POST http://localhost:8000/checkout-sessions \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=\"https://agent.example/profile\"" \
  -H "request-signature: test" \
  -H "idempotency-key: $(uuidgen)" \
  -H "request-id: $(uuidgen)" \
  -d '{
    "line_items": [{
      "item": {"id": "laptop_pro_16", "title": "Laptop Pro 16", "price": 129900},
      "quantity": 1
    }],
    "currency": "USD",
    "buyer": {
      "full_name": "John Doe",
      "email": "john.doe@example.com"
    }
  }'
```

#### Apply Discount
```bash
curl -X PUT http://localhost:8000/checkout-sessions/{SESSION_ID} \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=\"https://agent.example/profile\"" \
  -d '{
    "id": "{SESSION_ID}",
    "line_items": [...],
    "currency": "USD",
    "discounts": {
      "codes": ["10OFF"]
    }
  }'
```

#### Complete Checkout
```bash
curl -X POST http://localhost:8000/checkout-sessions/{SESSION_ID}/complete
```

## 🏗️ Project Structure

```
UCP/
├── server/
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── products.py         # Product catalog and discovery
│   ├── checkout.py         # Checkout session management
│   └── profile.py          # Business profile generation
├── web/
│   ├── index.html          # Web UI
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
├── requirements.txt        # Python dependencies
├── run_server.py          # Server startup script
└── README.md              # This file
```

## 🔧 Configuration

The server runs on `http://localhost:8000` by default. To change this, modify `server/app.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📚 UCP SDK Integration

This prototype **fully integrates the official UCP Python SDK** for complete specification compliance and production-ready implementation.

### SDK Integration Status

The application uses official UCP SDK types throughout:

- ✅ **Products**: `ItemResponse` from `ucp_sdk.models.schemas.shopping.types.item_resp`
- ✅ **Checkout**: `CheckoutResponse` from `ucp_sdk.models.schemas.shopping.checkout_resp`
- ✅ **Line Items**: `LineItemResponse` from `ucp_sdk.models.schemas.shopping.types.line_item_resp`
- ✅ **Totals**: `TotalResponse` from `ucp_sdk.models.schemas.shopping.types.total_resp`
- ✅ **Buyer**: `Buyer` from `ucp_sdk.models.schemas.shopping.types.buyer`
- ✅ **Discounts**: `AppliedDiscount` and `Allocation` from `ucp_sdk.models.schemas.shopping.discount_resp`
- ✅ **Profile**: `UcpDiscoveryProfile` and `DiscoveryProfile` from `ucp_sdk.models.discovery.profile_schema`
- ✅ **Payment**: `PaymentResponse` from `ucp_sdk.models.schemas.shopping.payment_resp`

### Official UCP SDK

The Universal Commerce Protocol provides official SDKs and reference implementations:

- **Python SDK**: https://github.com/Universal-Commerce-Protocol/python-sdk
- **Samples Repository**: https://github.com/Universal-Commerce-Protocol/samples
- **UCP Specification**: https://ucp.dev

### SDK Installation

The SDK is included in this project as a cloned repository and installed as an editable package:

```bash
# SDK is already cloned in sdk/python/
# Install it as an editable package:
cd sdk/python
pip install -e .

# Or install from requirements.txt:
pip install -r requirements.txt
```

The `requirements.txt` includes:
```
-e ./sdk/python
```

### SDK Usage Examples

**Products Module:**
```python
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse

class Product(ItemResponse):
    """Extends SDK ItemResponse with additional fields."""
    description: str = ""
    currency: str = "USD"
    category: Optional[str] = None
    in_stock: bool = True
```

**Checkout Module:**
```python
from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse
from ucp_sdk.models.schemas.shopping.types.buyer import Buyer

# Create checkout session using SDK types
checkout_response = CheckoutResponse(
    ucp=ResponseCheckout(...),
    id=session_id,
    line_items=[LineItemResponse(...)],
    buyer=Buyer(...),
    totals=[TotalResponse(...)],
    ...
)
```

**Profile Module:**
```python
from ucp_sdk.models.discovery.profile_schema import UcpDiscoveryProfile, Payment
from ucp_sdk.models._internal import DiscoveryProfile, Discovery, Version

# Create discovery profile using SDK types
profile = UcpDiscoveryProfile(
    ucp=DiscoveryProfile(
        version=Version(root="2026-01-11"),
        capabilities=[Discovery(...)],
        services=Services(root={})
    ),
    payment=Payment(handlers=[...])
)
```

### Benefits of SDK Integration

1. **Full Specification Compliance**: All types match the official UCP specification exactly
2. **Automatic Validation**: Pydantic models provide automatic schema validation
3. **Type Safety**: Full type hints and IDE support
4. **Future-Proof**: Easy updates when UCP specification evolves
5. **Production Ready**: Official SDK ensures compatibility with all UCP platforms

### UCP Version

This prototype uses UCP version **2026-01-11** as specified in the official documentation and SDK.

### Key UCP Headers

The implementation includes proper UCP headers:

- `UCP-Agent`: Agent profile identifier
- `request-signature`: Request signature for security
- `idempotency-key`: For idempotent operations
- `request-id`: Unique request identifier

### Capabilities Implemented

1. **dev.ucp.shopping.product_discovery**: Product search and browsing
2. **dev.ucp.shopping.checkout**: Checkout session management with discount support

### Payment Handlers

The prototype includes a mock payment handler configuration using SDK types. In production, integrate with:
- Google Pay
- Stripe
- Adyen
- Other UCP-compatible payment providers

### Updating the SDK

To update to the latest SDK version:

```bash
cd sdk/python
git pull origin main
pip install -e . --upgrade
```



## 🤝 Contributing

This is a prototype for demonstration purposes. For production implementations, refer to:
- [Official UCP Documentation](https://developers.google.com/merchant/ucp)
- [UCP GitHub Repository](https://github.com/Universal-Commerce-Protocol)
- [UCP Playground](https://ucp.dev/playground/)

## 📄 License

This prototype is provided as-is for educational and demonstration purposes.

## 🔗 Resources

- [UCP Official Blog Post](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp)
- [Google UCP Integration Guide](https://developers.google.com/merchant/ucp)
- [UCP Playground](https://ucp.dev/playground/)
- [UCP GitHub](https://github.com/Universal-Commerce-Protocol)

## 🙏 Acknowledgments

- Google and the UCP development team
- Industry partners: Shopify, Etsy, Wayfair, Target, Walmart, and others
- The open-source community

---

**Built with ❤️ to demonstrate the power of Universal Commerce Protocol**


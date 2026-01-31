"""
Product catalog and product discovery functionality for UCP.
Uses official UCP SDK types.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse


# Use SDK ItemResponse as base, extend with additional fields via extra="allow"
class Product(ItemResponse):
    """UCP-compliant product model using SDK ItemResponse."""
    description: str = ""
    currency: str = "USD"
    category: Optional[str] = None
    in_stock: bool = True
    technical_info: Optional[Dict[str, Any]] = None
    average_rating: float = 0.0
    rating_count: int = 0
    comments: List[Dict[str, Any]] = []


def _load_products_from_json() -> List[Product]:
    """Load products from JSON file."""
    json_path = Path(__file__).parent / "products.json"
    
    if not json_path.exists():
        # Return empty list if JSON file doesn't exist
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    # Convert JSON data to Product objects
    products = []
    for data in products_data:
        product = Product(**data)
        products.append(product)
    
    return products


# Load product catalog from JSON file
PRODUCT_CATALOG = _load_products_from_json()


def get_product(product_id: str) -> Optional[Product]:
    """Get a product by ID."""
    for product in PRODUCT_CATALOG:
        if product.id == product_id:
            return product
    return None


def search_products(query: Optional[str] = None, category: Optional[str] = None) -> List[Product]:
    """Search products by query and/or category."""
    results = PRODUCT_CATALOG.copy()
    
    if query:
        query_lower = query.lower()
        results = [
            p for p in results
            if query_lower in p.title.lower() or query_lower in p.description.lower()
        ]
    
    if category:
        results = [p for p in results if p.category == category]
    
    return results


def get_all_products() -> List[Product]:
    """Get all products."""
    return PRODUCT_CATALOG


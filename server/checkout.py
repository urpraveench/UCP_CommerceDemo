"""
Checkout session management for UCP using official SDK types.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse
from ucp_sdk.models.schemas.shopping.types.buyer import Buyer
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse
from ucp_sdk.models.schemas.shopping.discount_resp import AppliedDiscount, Allocation
from ucp_sdk.models.schemas.shopping.payment_resp import PaymentResponse
from ucp_sdk.models._internal import ResponseCheckout
from .products import get_product


class CheckoutSession:
    """Manages a checkout session using UCP SDK types."""
    
    def __init__(self, session_id: str, currency: str = "USD"):
        self.id = session_id
        self.currency = currency
        self.line_items: List[LineItemResponse] = []
        self.buyer: Optional[Buyer] = None
        self.status = "draft"
        self.discounts: Dict[str, Any] = {}
        self.payment = PaymentResponse(handlers=[])
        self.created_at = datetime.now()
    
    def add_line_item(self, product_id: str, quantity: int = 1) -> LineItemResponse:
        """Add a product to the checkout session."""
        product = get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        line_item_id = str(uuid.uuid4())
        subtotal = product.price * quantity
        
        # Create item using SDK ItemResponse
        item = ItemResponse(
            id=product.id,
            title=product.title,
            price=product.price,
            image_url=product.image_url
        )
        
        # Create totals using SDK TotalResponse
        totals = [
            TotalResponse(type="subtotal", amount=subtotal),
            TotalResponse(type="total", amount=subtotal)
        ]
        
        # Create line item using SDK LineItemResponse
        line_item = LineItemResponse(
            id=line_item_id,
            item=item,
            quantity=quantity,
            totals=totals
        )
        
        self.line_items.append(line_item)
        return line_item
    
    def update_line_item(self, line_item_id: str, quantity: Optional[int] = None):
        """Update a line item in the checkout session."""
        for item in self.line_items:
            if item.id == line_item_id:
                if quantity is not None:
                    item.quantity = quantity
                    subtotal = item.item.price * quantity
                    item.totals = [
                        TotalResponse(type="subtotal", amount=subtotal),
                        TotalResponse(type="total", amount=subtotal)
                    ]
                return item
        raise ValueError(f"Line item {line_item_id} not found")
    
    def apply_discount(self, discount_code: str) -> Dict[str, Any]:
        """Apply a discount code to the checkout."""
        # Sample discount codes
        DISCOUNTS = {
            "10OFF": {"title": "10% Off", "percent": 10},
            "SAVE20": {"title": "20% Off", "percent": 20},
            "FREESHIP": {"title": "Free Shipping", "amount": 500}  # $5.00
        }
        
        if discount_code not in DISCOUNTS:
            raise ValueError(f"Invalid discount code: {discount_code}")
        
        discount_info = DISCOUNTS[discount_code]
        
        # Calculate subtotal
        subtotal = sum(item.totals[0].amount for item in self.line_items)
        
        # Apply discount
        if "percent" in discount_info:
            discount_amount = int(subtotal * discount_info["percent"] / 100)
        else:
            discount_amount = discount_info["amount"]
        
        # Store discount using SDK types
        if "codes" not in self.discounts:
            self.discounts["codes"] = []
        if discount_code not in self.discounts["codes"]:
            self.discounts["codes"].append(discount_code)
        
        # Create AppliedDiscount using SDK type
        applied_discount = AppliedDiscount(
            code=discount_code,
            title=discount_info["title"],
            amount=discount_amount,
            automatic=False,
            allocations=[Allocation(path="subtotal", amount=discount_amount)]
        )
        
        self.discounts["applied"] = [applied_discount]
        
        return self.discounts
    
    def calculate_totals(self) -> List[TotalResponse]:
        """Calculate totals for the checkout session using SDK types."""
        subtotal = sum(item.totals[0].amount for item in self.line_items)
        
        totals = [TotalResponse(type="subtotal", amount=subtotal)]
        
        # Apply discounts
        if "applied" in self.discounts:
            for discount in self.discounts["applied"]:
                if isinstance(discount, AppliedDiscount):
                    totals.append(TotalResponse(
                        type="discount",
                        amount=discount.amount
                    ))
                else:
                    # Handle dict format for backward compatibility
                    totals.append(TotalResponse(
                        type="discount",
                        amount=discount.get("amount", 0)
                    ))
        
        # Calculate final total
        discount_total = sum(
            d.amount for d in totals if d.type == "discount"
        )
        final_total = max(0, subtotal - discount_total)
        totals.append(TotalResponse(type="total", amount=final_total))
        
        return totals
    
    def set_buyer(self, full_name: str, email: str):
        """Set buyer information using SDK Buyer type."""
        self.buyer = Buyer(
            full_name=full_name,
            email=email
        )
    
    def to_ucp_response(self) -> CheckoutResponse:
        """Convert checkout session to UCP SDK CheckoutResponse."""
        totals = self.calculate_totals()
        
        # Create UCP response header using SDK types
        from ucp_sdk.models._internal import Response, Version
        ucp_header = ResponseCheckout(
            version=Version(root="2026-01-11"),
            capabilities=[
                Response(
                    name="dev.ucp.shopping.checkout",
                    version=Version(root="2026-01-11")
                )
            ]
        )
        
        # Convert discounts to dict format for response
        discounts_dict = {}
        if "codes" in self.discounts:
            discounts_dict["codes"] = self.discounts["codes"]
        if "applied" in self.discounts:
            # Convert AppliedDiscount objects to dicts
            applied = []
            for discount in self.discounts["applied"]:
                if isinstance(discount, AppliedDiscount):
                    applied.append(discount.model_dump(exclude_none=True))
                else:
                    applied.append(discount)
            discounts_dict["applied"] = applied
        
        return CheckoutResponse(
            ucp=ucp_header,
            id=self.id,
            line_items=self.line_items,
            buyer=self.buyer,
            status=self.status,
            currency=self.currency,
            totals=totals,
            links=[],
            payment=self.payment,
            **discounts_dict  # Add discounts as extra fields
        )


# In-memory storage for checkout sessions
_checkout_sessions: Dict[str, CheckoutSession] = {}


def create_checkout_session(
    line_items: List[Dict[str, Any]],
    currency: str = "USD",
    buyer: Optional[Dict[str, Any]] = None
) -> CheckoutSession:
    """Create a new checkout session."""
    session_id = str(uuid.uuid4())
    session = CheckoutSession(session_id, currency)
    
    # Add line items
    for item in line_items:
        product_id = item["item"]["id"]
        quantity = item.get("quantity", 1)
        session.add_line_item(product_id, quantity)
    
    # Set buyer if provided
    if buyer:
        session.set_buyer(
            buyer.get("full_name", ""),
            buyer.get("email", "")
        )
    
    session.status = "ready_for_complete"
    _checkout_sessions[session_id] = session
    return session


def get_checkout_session(session_id: str) -> Optional[CheckoutSession]:
    """Get a checkout session by ID."""
    return _checkout_sessions.get(session_id)


def update_checkout_session(
    session_id: str,
    line_items: Optional[List[Dict[str, Any]]] = None,
    discounts: Optional[Dict[str, Any]] = None,
    buyer: Optional[Dict[str, Any]] = None
) -> CheckoutSession:
    """Update an existing checkout session."""
    session = get_checkout_session(session_id)
    if not session:
        raise ValueError(f"Checkout session {session_id} not found")
    
    # Update line items if provided
    if line_items:
        session.line_items = []
        for item in line_items:
            product_id = item["item"]["id"]
            quantity = item.get("quantity", 1)
            session.add_line_item(product_id, quantity)
    
    # Apply discounts if provided
    if discounts and "codes" in discounts:
        for code in discounts["codes"]:
            try:
                session.apply_discount(code)
            except ValueError:
                pass  # Ignore invalid discount codes
    
    # Update buyer if provided
    if buyer:
        session.set_buyer(
            buyer.get("full_name", ""),
            buyer.get("email", "")
        )
    
    return session


def complete_checkout_session(session_id: str) -> CheckoutSession:
    """Complete a checkout session."""
    session = get_checkout_session(session_id)
    if not session:
        raise ValueError(f"Checkout session {session_id} not found")
    
    session.status = "completed"
    return session

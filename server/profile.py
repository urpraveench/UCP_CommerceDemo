"""
Business profile and capability declarations for UCP using official SDK types.
"""
from typing import Dict, Any
from ucp_sdk.models.discovery.profile_schema import UcpDiscoveryProfile, Payment
from ucp_sdk.models.schemas.shopping.types import payment_handler_resp
from ucp_sdk.models._internal import DiscoveryProfile, Discovery, Version, Services
from pydantic import AnyUrl


UCP_VERSION = "2026-01-11"
BUSINESS_NAME = "Demo Store"
BUSINESS_ID = "demo-store-001"
SERVER_URL = "http://localhost:8000"


def get_business_profile() -> Dict[str, Any]:
    """
    Generate UCP business profile for agent discovery using SDK types.
    This is served at /.well-known/ucp endpoint.
    """
    # Create capabilities using SDK Discovery type
    capabilities = [
        Discovery(
            name="dev.ucp.shopping.product_discovery",
            version=Version(root=UCP_VERSION),
            spec=AnyUrl("https://ucp.dev/specs/shopping/product-discovery"),
            config={}
        ),
        Discovery(
            name="dev.ucp.shopping.checkout",
            version=Version(root=UCP_VERSION),
            spec=AnyUrl("https://ucp.dev/specs/shopping/checkout"),
            config={}
        )
    ]
    
    # Create UCP header using SDK DiscoveryProfile
    ucp_header = DiscoveryProfile(
        version=Version(root=UCP_VERSION),
        services=Services(root={}),  # Empty services for now
        capabilities=capabilities
    )
    
    # Create payment handler using SDK types
    payment_handler = payment_handler_resp.PaymentHandlerResponse(
        id="mock_payment_handler",
        name="dev.ucp.mock_payment",
        version=UCP_VERSION,
        spec=AnyUrl("https://ucp.dev/specs/mock"),
        config_schema=AnyUrl("https://ucp.dev/schemas/mock.json"),
        instrument_schemas=[
            AnyUrl("https://ucp.dev/schemas/shopping/types/card_payment_instrument.json")
        ],
        config={
            "supported_tokens": ["success_token", "fail_token"]
        }
    )
    
    payment = Payment(handlers=[payment_handler])
    
    # Create profile using SDK UcpDiscoveryProfile
    profile = UcpDiscoveryProfile(
        ucp=ucp_header,
        payment=payment
    )
    
    # Convert to dict and add business info (not in SDK schema but useful for demo)
    profile_dict = profile.model_dump(exclude_none=True)
    profile_dict["business"] = {
        "id": BUSINESS_ID,
        "name": BUSINESS_NAME,
        "url": SERVER_URL
    }
    
    # Add bindings to capabilities (using extra="allow" in SDK models)
    if "capabilities" in profile_dict.get("ucp", {}):
        for cap in profile_dict["ucp"]["capabilities"]:
            if cap.get("name") == "dev.ucp.shopping.product_discovery":
                cap["bindings"] = [{
                    "type": "rest",
                    "methods": ["GET"],
                    "url": f"{SERVER_URL}/products"
                }]
            elif cap.get("name") == "dev.ucp.shopping.checkout":
                cap["bindings"] = [{
                    "type": "rest",
                    "methods": ["POST", "PUT"],
                    "url": f"{SERVER_URL}/checkout-sessions"
                }]
    
    return profile_dict

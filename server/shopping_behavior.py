"""
Shopping behavior tracking and analysis module.
Tracks user preferences and patterns to provide context for AI agent product selection.
"""
from typing import List, Dict, Any, Optional
from collections import Counter
from .products import get_product, Product


class ShoppingBehaviorTracker:
    """Tracks and analyzes user shopping behavior."""
    
    def __init__(self):
        self.searched_products: List[str] = []
        self.viewed_products: List[str] = []
        self.cart_products: List[str] = []
        self.explicit_preferences: List[str] = []
        self.search_queries: List[str] = []
        self.categories_browsed: List[str] = []
    
    def track_search(self, query: Optional[str] = None, category: Optional[str] = None, products: List[Product] = None):
        """Track a product search."""
        if query:
            self.search_queries.append(query.lower())
        if category:
            self.categories_browsed.append(category)
        if products:
            for product in products:
                if product.id not in self.searched_products:
                    self.searched_products.append(product.id)
    
    def track_view(self, product_id: str):
        """Track a product view."""
        if product_id not in self.viewed_products:
            self.viewed_products.append(product_id)
    
    def track_cart_addition(self, product_id: str):
        """Track a product added to cart."""
        if product_id not in self.cart_products:
            self.cart_products.append(product_id)
    
    def track_explicit_preference(self, preference_text: str):
        """Track explicit user preference from conversation."""
        self.explicit_preferences.append(preference_text)
    
    def analyze_behavior(self) -> Dict[str, Any]:
        """Analyze tracked behavior and return insights."""
        insights = {
            "price_range": self._analyze_price_range(),
            "brand_preferences": self._analyze_brands(),
            "category_preferences": self._analyze_categories(),
            "rating_preferences": self._analyze_ratings(),
            "delivery_preferences": self._analyze_delivery(),
            "shopping_pattern": self._analyze_shopping_pattern(),
            "explicit_preferences": self.explicit_preferences.copy()
        }
        return insights
    
    def _analyze_price_range(self) -> Optional[Dict[str, float]]:
        """Analyze price range from viewed/searched/cart products."""
        all_product_ids = set(self.searched_products + self.viewed_products + self.cart_products)
        if not all_product_ids:
            return None
        
        prices = []
        for product_id in all_product_ids:
            product = get_product(product_id)
            if product and product.price:
                prices.append(product.price / 100.0)  # Convert cents to dollars
        
        if not prices:
            return None
        
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "median": sorted(prices)[len(prices) // 2]
        }
    
    def _analyze_brands(self) -> List[str]:
        """Analyze brand preferences from products."""
        all_product_ids = set(self.cart_products + self.viewed_products)
        brands = []
        
        for product_id in all_product_ids:
            product = get_product(product_id)
            if product and product.technical_info:
                brand = product.technical_info.get("Brand")
                if brand:
                    # Remove "(Local)" suffix if present
                    brand_clean = brand.replace(" (Local)", "").strip()
                    if brand_clean:
                        brands.append(brand_clean)
        
        # Return most common brands
        brand_counts = Counter(brands)
        return [brand for brand, _ in brand_counts.most_common(3)]
    
    def _analyze_categories(self) -> List[str]:
        """Analyze category preferences."""
        all_product_ids = set(self.searched_products + self.viewed_products + self.cart_products)
        categories = []
        
        for product_id in all_product_ids:
            product = get_product(product_id)
            if product and product.category:
                categories.append(product.category)
        
        # Also include categories from browsing
        categories.extend(self.categories_browsed)
        
        category_counts = Counter(categories)
        return [cat for cat, _ in category_counts.most_common(3)]
    
    def _analyze_ratings(self) -> Optional[Dict[str, float]]:
        """Analyze rating preferences."""
        all_product_ids = set(self.cart_products + self.viewed_products)
        ratings = []
        
        for product_id in all_product_ids:
            product = get_product(product_id)
            if product and product.average_rating:
                ratings.append(product.average_rating)
        
        if not ratings:
            return None
        
        return {
            "min": min(ratings),
            "avg": sum(ratings) / len(ratings)
        }
    
    def _analyze_delivery(self) -> List[str]:
        """Analyze delivery preferences."""
        all_product_ids = set(self.cart_products + self.viewed_products)
        delivery_options = []
        
        for product_id in all_product_ids:
            product = get_product(product_id)
            if product and product.technical_info:
                delivery = product.technical_info.get("Delivery")
                if delivery:
                    delivery_options.append(delivery)
        
        delivery_counts = Counter(delivery_options)
        return [delivery for delivery, _ in delivery_counts.most_common(2)]
    
    def _analyze_shopping_pattern(self) -> str:
        """Analyze overall shopping pattern."""
        price_range = self._analyze_price_range()
        brands = self._analyze_brands()
        ratings = self._analyze_ratings()
        
        patterns = []
        
        # Budget-conscious pattern
        if price_range and price_range["avg"] < 50:
            patterns.append("budget-conscious")
        
        # Premium shopper pattern
        if price_range and price_range["avg"] > 200:
            patterns.append("premium-focused")
        
        # Brand-loyal pattern
        if len(brands) == 1 and len(self.cart_products) > 0:
            patterns.append("brand-loyal")
        
        # Quality-focused pattern
        if ratings and ratings["min"] >= 4.0:
            patterns.append("quality-focused")
        
        # Comparison shopper pattern
        if len(self.viewed_products) > len(self.cart_products) * 2:
            patterns.append("comparison-shopper")
        
        return ", ".join(patterns) if patterns else "general shopper"
    
    def generate_behavior_summary(self) -> Optional[str]:
        """Generate natural language summary of shopping behavior."""
        insights = self.analyze_behavior()
        
        if not any([
            insights["price_range"],
            insights["brand_preferences"],
            insights["category_preferences"],
            insights["explicit_preferences"]
        ]):
            return None
        
        summary_parts = []
        
        # Explicit preferences
        if insights["explicit_preferences"]:
            summary_parts.append(f"The user has expressed preferences: {', '.join(insights['explicit_preferences'][-3:])}")
        
        # Price range
        if insights["price_range"]:
            price = insights["price_range"]
            if price["avg"] < 30:
                summary_parts.append("The user tends to shop for budget-friendly products")
            elif price["avg"] > 150:
                summary_parts.append("The user prefers premium products")
            else:
                summary_parts.append(f"The user typically shops for products in the ${price['min']:.0f}-${price['max']:.0f} range")
        
        # Brand preferences
        if insights["brand_preferences"]:
            brands = ", ".join(insights["brand_preferences"])
            summary_parts.append(f"The user shows preference for {brands} brands")
        
        # Category preferences
        if insights["category_preferences"]:
            categories = ", ".join(insights["category_preferences"])
            summary_parts.append(f"The user frequently browses {categories} categories")
        
        # Rating preferences
        if insights["rating_preferences"]:
            min_rating = insights["rating_preferences"]["min"]
            if min_rating >= 4.0:
                summary_parts.append("The user prefers highly-rated products (4+ stars)")
            elif min_rating >= 3.0:
                summary_parts.append("The user considers products with 3+ star ratings")
        
        # Delivery preferences
        if insights["delivery_preferences"]:
            delivery = ", ".join(insights["delivery_preferences"])
            summary_parts.append(f"The user prefers {delivery} delivery options")
        
        # Shopping pattern
        pattern = insights["shopping_pattern"]
        if pattern != "general shopper":
            summary_parts.append(f"Shopping pattern: {pattern}")
        
        return ". ".join(summary_parts) + "." if summary_parts else None


def extract_behavior_from_conversation(
    conversation_history: List[Dict[str, str]],
    cart: List[Dict[str, Any]],
    searched_products: Optional[List[Dict[str, Any]]] = None
) -> ShoppingBehaviorTracker:
    """Extract shopping behavior from conversation history and cart."""
    tracker = ShoppingBehaviorTracker()
    
    # Track cart products
    for item in cart:
        product_id = item.get("id")
        if product_id:
            tracker.track_cart_addition(product_id)
    
    # Track searched products
    if searched_products:
        for product_data in searched_products:
            product_id = product_data.get("id")
            if product_id:
                tracker.track_view(product_id)
    
    # Extract explicit preferences from conversation
    for msg in conversation_history:
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            
            # Budget preferences
            if any(word in content for word in ["budget", "cheap", "affordable", "inexpensive", "low price"]):
                tracker.track_explicit_preference("prefers budget-friendly products")
            if any(word in content for word in ["premium", "expensive", "high-end", "luxury", "quality"]):
                tracker.track_explicit_preference("prefers premium products")
            
            # Brand preferences
            if "brand" in content or "branded" in content:
                tracker.track_explicit_preference("has brand preferences")
            
            # Delivery preferences
            if "same day" in content or "fast delivery" in content:
                tracker.track_explicit_preference("prefers fast delivery")
            if "delivery" in content:
                tracker.track_explicit_preference("considers delivery options")
            
            # Rating preferences
            if "rating" in content or "star" in content or "review" in content:
                tracker.track_explicit_preference("considers product ratings")
    
    return tracker



from server.products import search_products
import json

print("--- Testing 'desk' ---")
results_desk = search_products(query="desk")
print(f"Count: {len(results_desk)}")
for p in results_desk:
    print(f" - {p.title}")

print("\n--- Testing 'lamp' ---")
results_lamp = search_products(query="lamp")
print(f"Count: {len(results_lamp)}")
for p in results_lamp:
    print(f" - {p.title}")

print("\n--- Testing 'desk lamp' ---")
results_desk_lamp = search_products(query="desk lamp")
print(f"Count: {len(results_desk_lamp)}")
for p in results_desk_lamp:
    print(f" - {p.title}")

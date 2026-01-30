"""
Generate sample data files for restaurant analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Create data directory
os.makedirs('data', exist_ok=True)

# Generate Store to Kitchen Report
np.random.seed(42)
dates = pd.date_range('2026-01-01', '2026-01-31')

items_daily = {
    'Basmati Rice': {'base': 10, 'var': 3, 'unit': 'Kg'},
    'Toor Dal': {'base': 4, 'var': 1.5, 'unit': 'Kg'},
    'Urad Dal': {'base': 5, 'var': 1.5, 'unit': 'Kg'},
    'Chana Dal': {'base': 2, 'var': 1, 'unit': 'Kg'},
    'Paneer': {'base': 7, 'var': 2, 'unit': 'Kg'},
    'Curd': {'base': 5.5, 'var': 1.5, 'unit': 'Kg'},
    'Ghee': {'base': 2, 'var': 0.5, 'unit': 'Kg'},
    'Onion': {'base': 8, 'var': 2, 'unit': 'Kg'},
    'Tomato': {'base': 7, 'var': 2, 'unit': 'Kg'},
    'Potato': {'base': 6, 'var': 2, 'unit': 'Kg'},
    'Green Peas': {'base': 2.5, 'var': 1, 'unit': 'Kg'},
    'Capsicum': {'base': 2, 'var': 1, 'unit': 'Kg'},
    'Coconut': {'base': 12, 'var': 4, 'unit': 'Pcs'},
    'Curry Leaves': {'base': 0.3, 'var': 0.1, 'unit': 'Kg'},
    'Idli Rice': {'base': 7, 'var': 2, 'unit': 'Kg'},
    'Cooking Oil': {'base': 5, 'var': 1.5, 'unit': 'Ltr'},
    'Atta (Wheat Flour)': {'base': 5.5, 'var': 1.5, 'unit': 'Kg'},
    'Semolina (Rava)': {'base': 2, 'var': 0.8, 'unit': 'Kg'},
}

categories = {
    'Basmati Rice': 'Grains', 'Toor Dal': 'Pulses', 'Urad Dal': 'Pulses',
    'Chana Dal': 'Pulses', 'Paneer': 'Dairy', 'Curd': 'Dairy', 'Ghee': 'Dairy',
    'Onion': 'Vegetables', 'Tomato': 'Vegetables', 'Potato': 'Vegetables',
    'Green Peas': 'Vegetables', 'Capsicum': 'Vegetables', 'Coconut': 'Vegetables',
    'Curry Leaves': 'Vegetables', 'Idli Rice': 'Grains', 'Cooking Oil': 'Oil',
    'Atta (Wheat Flour)': 'Grains', 'Semolina (Rava)': 'Grains'
}

stk_data = []
for date in dates:
    weekend_factor = 1.3 if date.dayofweek >= 5 else 1.0
    for item, props in items_daily.items():
        qty = round(props['base'] * weekend_factor + np.random.uniform(-props['var'], props['var']), 1)
        qty = max(0.5, qty)
        stk_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Item Name': item,
            'Category': categories[item],
            'Quantity Issued': qty,
            'Unit': props['unit']
        })

stk_df = pd.DataFrame(stk_data)
stk_df.to_csv('data/store_to_kitchen_report.csv', index=False)
print(f"Created store_to_kitchen_report.csv with {len(stk_df)} records")

# Generate Sales Report with menu items
menu_items = [
    # South Indian
    {'name': 'Masala Dosa', 'category': 'South Indian', 'price': 120, 'food_cost': 35, 'popularity': 'high'},
    {'name': 'Plain Dosa', 'category': 'South Indian', 'price': 80, 'food_cost': 20, 'popularity': 'high'},
    {'name': 'Idli Sambar (4 pcs)', 'category': 'South Indian', 'price': 70, 'food_cost': 18, 'popularity': 'high'},
    {'name': 'Medu Vada (2 pcs)', 'category': 'South Indian', 'price': 60, 'food_cost': 15, 'popularity': 'medium'},
    {'name': 'Uttapam', 'category': 'South Indian', 'price': 100, 'food_cost': 28, 'popularity': 'medium'},
    {'name': 'Pongal', 'category': 'South Indian', 'price': 90, 'food_cost': 25, 'popularity': 'low'},
    {'name': 'Rava Dosa', 'category': 'South Indian', 'price': 110, 'food_cost': 30, 'popularity': 'medium'},
    {'name': 'Set Dosa (3 pcs)', 'category': 'South Indian', 'price': 90, 'food_cost': 40, 'popularity': 'low'},
    # North Indian
    {'name': 'Paneer Butter Masala', 'category': 'North Indian', 'price': 280, 'food_cost': 85, 'popularity': 'high'},
    {'name': 'Dal Makhani', 'category': 'North Indian', 'price': 220, 'food_cost': 55, 'popularity': 'high'},
    {'name': 'Chole Bhature', 'category': 'North Indian', 'price': 160, 'food_cost': 45, 'popularity': 'high'},
    {'name': 'Palak Paneer', 'category': 'North Indian', 'price': 260, 'food_cost': 80, 'popularity': 'medium'},
    {'name': 'Aloo Paratha', 'category': 'North Indian', 'price': 80, 'food_cost': 25, 'popularity': 'high'},
    {'name': 'Kadai Paneer', 'category': 'North Indian', 'price': 270, 'food_cost': 90, 'popularity': 'medium'},
    {'name': 'Veg Biryani', 'category': 'North Indian', 'price': 200, 'food_cost': 60, 'popularity': 'high'},
    {'name': 'Mixed Veg Curry', 'category': 'North Indian', 'price': 180, 'food_cost': 70, 'popularity': 'low'},
    {'name': 'Malai Kofta', 'category': 'North Indian', 'price': 290, 'food_cost': 100, 'popularity': 'low'},
    {'name': 'Butter Naan', 'category': 'North Indian', 'price': 50, 'food_cost': 15, 'popularity': 'high'},
    {'name': 'Roti', 'category': 'North Indian', 'price': 25, 'food_cost': 8, 'popularity': 'high'},
    {'name': 'Jeera Rice', 'category': 'North Indian', 'price': 120, 'food_cost': 35, 'popularity': 'medium'},
]

popularity_range = {'high': (15, 35), 'medium': (8, 18), 'low': (3, 10)}

sales_data = []
for date in dates:
    weekend_factor = 1.4 if date.dayofweek >= 5 else 1.0
    for item in menu_items:
        low, high = popularity_range[item['popularity']]
        qty = int(np.random.randint(low, high) * weekend_factor)
        revenue = qty * item['price']
        cost = qty * item['food_cost']
        profit = revenue - cost
        sales_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Item Name': item['name'],
            'Category': item['category'],
            'Quantity Sold': qty,
            'Price': item['price'],
            'Revenue': revenue,
            'Food Cost': cost,
            'Profit': profit
        })

sales_df = pd.DataFrame(sales_data)
sales_df.to_csv('data/sales_report.csv', index=False)
print(f"Created sales_report.csv with {len(sales_df)} records")

# Generate Recipe/BOM data
recipes = [
    # Masala Dosa
    ('Masala Dosa', 'Idli Rice', 0.08, 'Kg'),
    ('Masala Dosa', 'Urad Dal', 0.03, 'Kg'),
    ('Masala Dosa', 'Potato', 0.1, 'Kg'),
    ('Masala Dosa', 'Onion', 0.05, 'Kg'),
    ('Masala Dosa', 'Cooking Oil', 0.02, 'Ltr'),
    ('Masala Dosa', 'Curry Leaves', 0.002, 'Kg'),
    # Plain Dosa
    ('Plain Dosa', 'Idli Rice', 0.08, 'Kg'),
    ('Plain Dosa', 'Urad Dal', 0.03, 'Kg'),
    ('Plain Dosa', 'Cooking Oil', 0.015, 'Ltr'),
    # Idli Sambar
    ('Idli Sambar (4 pcs)', 'Idli Rice', 0.1, 'Kg'),
    ('Idli Sambar (4 pcs)', 'Urad Dal', 0.04, 'Kg'),
    ('Idli Sambar (4 pcs)', 'Toor Dal', 0.05, 'Kg'),
    ('Idli Sambar (4 pcs)', 'Onion', 0.03, 'Kg'),
    ('Idli Sambar (4 pcs)', 'Tomato', 0.02, 'Kg'),
    # Medu Vada
    ('Medu Vada (2 pcs)', 'Urad Dal', 0.08, 'Kg'),
    ('Medu Vada (2 pcs)', 'Cooking Oil', 0.05, 'Ltr'),
    ('Medu Vada (2 pcs)', 'Curry Leaves', 0.002, 'Kg'),
    # Uttapam
    ('Uttapam', 'Idli Rice', 0.1, 'Kg'),
    ('Uttapam', 'Urad Dal', 0.04, 'Kg'),
    ('Uttapam', 'Onion', 0.05, 'Kg'),
    ('Uttapam', 'Tomato', 0.03, 'Kg'),
    ('Uttapam', 'Capsicum', 0.02, 'Kg'),
    # Pongal
    ('Pongal', 'Basmati Rice', 0.1, 'Kg'),
    ('Pongal', 'Toor Dal', 0.03, 'Kg'),
    ('Pongal', 'Ghee', 0.03, 'Kg'),
    # Rava Dosa
    ('Rava Dosa', 'Semolina (Rava)', 0.08, 'Kg'),
    ('Rava Dosa', 'Onion', 0.03, 'Kg'),
    ('Rava Dosa', 'Curry Leaves', 0.002, 'Kg'),
    ('Rava Dosa', 'Cooking Oil', 0.02, 'Ltr'),
    # Set Dosa
    ('Set Dosa (3 pcs)', 'Idli Rice', 0.12, 'Kg'),
    ('Set Dosa (3 pcs)', 'Urad Dal', 0.05, 'Kg'),
    ('Set Dosa (3 pcs)', 'Cooking Oil', 0.02, 'Ltr'),
    # Paneer Butter Masala
    ('Paneer Butter Masala', 'Paneer', 0.15, 'Kg'),
    ('Paneer Butter Masala', 'Tomato', 0.12, 'Kg'),
    ('Paneer Butter Masala', 'Onion', 0.08, 'Kg'),
    ('Paneer Butter Masala', 'Ghee', 0.03, 'Kg'),
    ('Paneer Butter Masala', 'Curd', 0.03, 'Kg'),
    # Dal Makhani
    ('Dal Makhani', 'Urad Dal', 0.1, 'Kg'),
    ('Dal Makhani', 'Tomato', 0.05, 'Kg'),
    ('Dal Makhani', 'Ghee', 0.04, 'Kg'),
    ('Dal Makhani', 'Curd', 0.02, 'Kg'),
    # Chole Bhature
    ('Chole Bhature', 'Chana Dal', 0.12, 'Kg'),
    ('Chole Bhature', 'Atta (Wheat Flour)', 0.1, 'Kg'),
    ('Chole Bhature', 'Onion', 0.05, 'Kg'),
    ('Chole Bhature', 'Tomato', 0.04, 'Kg'),
    ('Chole Bhature', 'Cooking Oil', 0.08, 'Ltr'),
    # Palak Paneer
    ('Palak Paneer', 'Paneer', 0.12, 'Kg'),
    ('Palak Paneer', 'Onion', 0.05, 'Kg'),
    ('Palak Paneer', 'Tomato', 0.03, 'Kg'),
    ('Palak Paneer', 'Ghee', 0.02, 'Kg'),
    # Aloo Paratha
    ('Aloo Paratha', 'Atta (Wheat Flour)', 0.1, 'Kg'),
    ('Aloo Paratha', 'Potato', 0.12, 'Kg'),
    ('Aloo Paratha', 'Ghee', 0.02, 'Kg'),
    # Kadai Paneer
    ('Kadai Paneer', 'Paneer', 0.15, 'Kg'),
    ('Kadai Paneer', 'Capsicum', 0.08, 'Kg'),
    ('Kadai Paneer', 'Onion', 0.06, 'Kg'),
    ('Kadai Paneer', 'Tomato', 0.08, 'Kg'),
    # Veg Biryani
    ('Veg Biryani', 'Basmati Rice', 0.15, 'Kg'),
    ('Veg Biryani', 'Onion', 0.08, 'Kg'),
    ('Veg Biryani', 'Potato', 0.05, 'Kg'),
    ('Veg Biryani', 'Green Peas', 0.03, 'Kg'),
    ('Veg Biryani', 'Curd', 0.04, 'Kg'),
    ('Veg Biryani', 'Ghee', 0.03, 'Kg'),
    # Mixed Veg Curry
    ('Mixed Veg Curry', 'Potato', 0.08, 'Kg'),
    ('Mixed Veg Curry', 'Green Peas', 0.05, 'Kg'),
    ('Mixed Veg Curry', 'Onion', 0.05, 'Kg'),
    ('Mixed Veg Curry', 'Tomato', 0.06, 'Kg'),
    ('Mixed Veg Curry', 'Capsicum', 0.04, 'Kg'),
    # Malai Kofta
    ('Malai Kofta', 'Paneer', 0.12, 'Kg'),
    ('Malai Kofta', 'Potato', 0.08, 'Kg'),
    ('Malai Kofta', 'Onion', 0.06, 'Kg'),
    ('Malai Kofta', 'Tomato', 0.08, 'Kg'),
    ('Malai Kofta', 'Curd', 0.05, 'Kg'),
    ('Malai Kofta', 'Ghee', 0.03, 'Kg'),
    # Butter Naan
    ('Butter Naan', 'Atta (Wheat Flour)', 0.08, 'Kg'),
    ('Butter Naan', 'Ghee', 0.015, 'Kg'),
    ('Butter Naan', 'Curd', 0.02, 'Kg'),
    # Roti
    ('Roti', 'Atta (Wheat Flour)', 0.05, 'Kg'),
    ('Roti', 'Ghee', 0.005, 'Kg'),
    # Jeera Rice
    ('Jeera Rice', 'Basmati Rice', 0.12, 'Kg'),
    ('Jeera Rice', 'Ghee', 0.02, 'Kg'),
]

bom_df = pd.DataFrame(recipes, columns=['Menu Item', 'Ingredient', 'Quantity Required', 'Unit'])
bom_df.to_csv('data/recipes_bom.csv', index=False)
print(f"Created recipes_bom.csv with {len(bom_df)} records")

print("\n✅ All sample data files generated successfully!")

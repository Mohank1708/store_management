"""
Restaurant Data Analysis Tool
Analyzes Pet Pooja style restaurant reports for:
1. Leakage & Waste Analysis
2. Theoretical vs. Actual Consumption (Variance)
3. Purchase Price Trend Analysis
4. Menu Engineering (Stars, Plow Horses, Puzzles, Dogs)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class RestaurantAnalyzer:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.load_data()
    
    def load_data(self):
        """Load all required CSV files"""
        self.purchase_df = pd.read_csv(f'{self.data_dir}/purchase_report.csv')
        self.stk_df = pd.read_csv(f'{self.data_dir}/store_to_kitchen_report.csv')
        self.sales_df = pd.read_csv(f'{self.data_dir}/sales_report.csv')
        self.bom_df = pd.read_csv(f'{self.data_dir}/recipes_bom.csv')
        
        # Convert dates
        self.purchase_df['Date'] = pd.to_datetime(self.purchase_df['Date'])
        self.stk_df['Date'] = pd.to_datetime(self.stk_df['Date'])
        self.sales_df['Date'] = pd.to_datetime(self.sales_df['Date'])
        
        print(f"Loaded Purchase Report: {len(self.purchase_df)} records")
        print(f"Loaded Store to Kitchen: {len(self.stk_df)} records")
        print(f"Loaded Sales Report: {len(self.sales_df)} records")
        print(f"Loaded Recipe BOM: {len(self.bom_df)} records")
    
    def leakage_waste_analysis(self):
        """
        Analysis 1: Compare total items purchased vs items issued to kitchen
        Formula: Leakage % = (Purchased - Issued) / Purchased * 100
        """
        print("\n" + "="*60)
        print("ANALYSIS 1: LEAKAGE & WASTE ANALYSIS")
        print("="*60)
        
        # Aggregate purchases by item
        purchased = self.purchase_df.groupby('Item Name').agg({
            'Quantity': 'sum',
            'Amount': 'sum',
            'Unit': 'first'
        }).rename(columns={'Quantity': 'Total Purchased'})
        
        # Aggregate issues by item
        issued = self.stk_df.groupby('Item Name').agg({
            'Quantity Issued': 'sum'
        }).rename(columns={'Quantity Issued': 'Total Issued'})
        
        # Merge and calculate leakage
        analysis = purchased.join(issued, how='outer').fillna(0)
        analysis['Difference'] = analysis['Total Purchased'] - analysis['Total Issued']
        analysis['Leakage %'] = (analysis['Difference'] / analysis['Total Purchased'] * 100).round(2)
        analysis['Value Lost (Rs)'] = (analysis['Difference'] / analysis['Total Purchased'] * analysis['Amount']).round(2)
        
        # Sort by leakage percentage
        analysis = analysis.sort_values('Leakage %', ascending=False)
        
        # Print results
        print("\nItem-wise Leakage Analysis:")
        print("-" * 80)
        print(f"{'Item':<25} {'Purchased':>12} {'Issued':>12} {'Leakage %':>10} {'Value Lost':>12}")
        print("-" * 80)
        
        for item, row in analysis.iterrows():
            status = "HIGH ALERT" if row['Leakage %'] > 15 else "WARNING" if row['Leakage %'] > 10 else ""
            print(f"{item:<25} {row['Total Purchased']:>12.1f} {row['Total Issued']:>12.1f} {row['Leakage %']:>9.1f}% {row['Value Lost (Rs)']:>11.0f} {status}")
        
        print("-" * 80)
        total_loss = analysis['Value Lost (Rs)'].sum()
        print(f"{'TOTAL VALUE LOST':<53} Rs. {total_loss:,.0f}")
        
        return analysis
    
    def variance_analysis(self):
        """
        Analysis 2: Theoretical vs. Actual Consumption
        Compare what should have been used (based on sales + recipes) vs what was actually issued
        """
        print("\n" + "="*60)
        print("ANALYSIS 2: THEORETICAL VS ACTUAL CONSUMPTION (VARIANCE)")
        print("="*60)
        
        # Calculate theoretical consumption from sales
        sales_qty = self.sales_df.groupby('Item Name')['Quantity Sold'].sum()
        
        # For each ingredient, calculate theoretical requirement
        theoretical = {}
        for _, row in self.bom_df.iterrows():
            menu_item = row['Menu Item']
            ingredient = row['Ingredient']
            qty_per_unit = row['Quantity Required']
            
            if menu_item in sales_qty.index:
                units_sold = sales_qty[menu_item]
                if ingredient not in theoretical:
                    theoretical[ingredient] = 0
                theoretical[ingredient] += units_sold * qty_per_unit
        
        theoretical_df = pd.DataFrame.from_dict(theoretical, orient='index', columns=['Theoretical Needed'])
        
        # Get actual issued
        actual = self.stk_df.groupby('Item Name')['Quantity Issued'].sum()
        actual_df = pd.DataFrame(actual).rename(columns={'Quantity Issued': 'Actual Issued'})
        
        # Merge
        variance_df = theoretical_df.join(actual_df, how='outer').fillna(0)
        variance_df['Variance'] = variance_df['Actual Issued'] - variance_df['Theoretical Needed']
        variance_df['Variance %'] = (variance_df['Variance'] / variance_df['Theoretical Needed'] * 100).round(2)
        variance_df = variance_df.replace([np.inf, -np.inf], 0)
        
        # Sort by variance
        variance_df = variance_df.sort_values('Variance %', ascending=False)
        
        print("\nIngredient-wise Variance Analysis:")
        print("-" * 85)
        print(f"{'Ingredient':<25} {'Theoretical':>12} {'Actual':>12} {'Variance':>12} {'Variance %':>12}")
        print("-" * 85)
        
        for item, row in variance_df.iterrows():
            status = "OVER-USE" if row['Variance %'] > 15 else "UNDER-USE" if row['Variance %'] < -10 else ""
            print(f"{item:<25} {row['Theoretical Needed']:>12.1f} {row['Actual Issued']:>12.1f} {row['Variance']:>+12.1f} {row['Variance %']:>+11.1f}% {status}")
        
        print("-" * 85)
        print("\nKey Insights:")
        high_variance = variance_df[variance_df['Variance %'] > 15]
        if len(high_variance) > 0:
            print(f"  - {len(high_variance)} ingredients have >15% over-usage (wastage/theft suspected)")
        low_variance = variance_df[variance_df['Variance %'] < -10]
        if len(low_variance) > 0:
            print(f"  - {len(low_variance)} ingredients have >10% under-usage (portion control too tight)")
        
        return variance_df
    
    def price_trend_analysis(self):
        """
        Analysis 3: Track price trends for top 5 most used ingredients
        """
        print("\n" + "="*60)
        print("ANALYSIS 3: PURCHASE PRICE TREND ANALYSIS")
        print("="*60)
        
        # Find top 5 most purchased items by value
        top_items = self.purchase_df.groupby('Item Name')['Amount'].sum().nlargest(5).index.tolist()
        
        print(f"\nTop 5 Ingredients by Purchase Value: {', '.join(top_items)}")
        print("\nPrice Trends Over Time:")
        print("-" * 70)
        
        price_trends = {}
        for item in top_items:
            item_data = self.purchase_df[self.purchase_df['Item Name'] == item].copy()
            item_data = item_data.sort_values('Date')
            
            # Get price per unit for each purchase
            first_price = item_data.iloc[0]['Rate']
            last_price = item_data.iloc[-1]['Rate']
            change = ((last_price - first_price) / first_price * 100)
            
            price_trends[item] = {
                'dates': item_data['Date'].tolist(),
                'prices': item_data['Rate'].tolist(),
                'first_price': first_price,
                'last_price': last_price,
                'change': change
            }
            
            trend = "UP" if change > 0 else "DOWN" if change < 0 else "STABLE"
            alert = "ALERT!" if abs(change) > 10 else ""
            print(f"  {item:<20}: Rs.{first_price:.0f} -> Rs.{last_price:.0f} ({change:+.1f}% {trend}) {alert}")
        
        print("-" * 70)
        print("\nRecommendations:")
        for item, data in price_trends.items():
            if data['change'] > 10:
                print(f"  - {item}: Consider finding alternative vendors or bulk purchasing")
            elif data['change'] < -5:
                print(f"  - {item}: Good time to stock up at lower prices")
        
        return price_trends
    
    def menu_engineering_analysis(self):
        """
        Analysis 4: Menu Engineering - Classify items into Stars, Plow Horses, Puzzles, Dogs
        Based on Popularity (quantity sold) and Profitability (profit margin)
        """
        print("\n" + "="*60)
        print("ANALYSIS 4: MENU ENGINEERING ANALYSIS")
        print("="*60)
        
        # Aggregate sales data by item
        menu_analysis = self.sales_df.groupby('Item Name').agg({
            'Quantity Sold': 'sum',
            'Revenue': 'sum',
            'Food Cost': 'sum',
            'Profit': 'sum',
            'Category': 'first'
        })
        
        # Calculate profit margin
        menu_analysis['Profit Margin %'] = (menu_analysis['Profit'] / menu_analysis['Revenue'] * 100).round(2)
        
        # Calculate averages for classification
        avg_popularity = menu_analysis['Quantity Sold'].mean()
        avg_profitability = menu_analysis['Profit Margin %'].mean()
        
        print(f"\nAverage Popularity (Qty Sold): {avg_popularity:.0f}")
        print(f"Average Profit Margin: {avg_profitability:.1f}%")
        
        # Classify items
        def classify_item(row):
            high_pop = row['Quantity Sold'] >= avg_popularity
            high_profit = row['Profit Margin %'] >= avg_profitability
            
            if high_pop and high_profit:
                return 'STAR'
            elif high_pop and not high_profit:
                return 'PLOW HORSE'
            elif not high_pop and high_profit:
                return 'PUZZLE'
            else:
                return 'DOG'
        
        menu_analysis['Classification'] = menu_analysis.apply(classify_item, axis=1)
        
        # Print by category
        categories = ['STAR', 'PLOW HORSE', 'PUZZLE', 'DOG']
        descriptions = {
            'STAR': 'High Profit + High Popularity - PROMOTE THESE!',
            'PLOW HORSE': 'Low Profit + High Popularity - Reduce ingredient costs',
            'PUZZLE': 'High Profit + Low Popularity - Better marketing needed',
            'DOG': 'Low Profit + Low Popularity - Consider removing'
        }
        
        for cat in categories:
            items = menu_analysis[menu_analysis['Classification'] == cat]
            print(f"\n{'='*60}")
            print(f"{cat}: {descriptions[cat]}")
            print(f"{'='*60}")
            print(f"{'Item':<25} {'Qty Sold':>10} {'Revenue':>12} {'Margin %':>10}")
            print("-" * 60)
            for item, row in items.sort_values('Revenue', ascending=False).iterrows():
                print(f"{item:<25} {row['Quantity Sold']:>10} Rs.{row['Revenue']:>10,.0f} {row['Profit Margin %']:>9.1f}%")
        
        # Summary counts
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for cat in categories:
            count = len(menu_analysis[menu_analysis['Classification'] == cat])
            print(f"  {cat}: {count} items")
        
        return menu_analysis
    
    def generate_full_report(self):
        """Run all analyses and return results"""
        print("\n" + "#"*70)
        print("#" + " "*20 + "RESTAURANT ANALYSIS REPORT" + " "*22 + "#")
        print("#" + " "*20 + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}" + " "*17 + "#")
        print("#"*70)
        
        results = {
            'leakage': self.leakage_waste_analysis(),
            'variance': self.variance_analysis(),
            'price_trends': self.price_trend_analysis(),
            'menu_engineering': self.menu_engineering_analysis()
        }
        
        print("\n" + "#"*70)
        print("#" + " "*25 + "END OF REPORT" + " "*30 + "#")
        print("#"*70)
        
        return results


if __name__ == "__main__":
    analyzer = RestaurantAnalyzer()
    results = analyzer.generate_full_report()

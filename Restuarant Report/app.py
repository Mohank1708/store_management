"""
Restaurant Analysis Dashboard - Flask Web Application
Works with only 3 reports: Purchase, Store to Kitchen, Sales
No Recipe/BOM data required
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class RestaurantAnalyzer:
    def __init__(self, purchase_df=None, stk_df=None, sales_df=None):
        self.purchase_df = purchase_df
        self.stk_df = stk_df
        self.sales_df = sales_df
    
    def load_from_files(self, data_dir='data'):
        """Load from CSV files"""
        self.purchase_df = pd.read_csv(f'{data_dir}/purchase_report.csv')
        self.stk_df = pd.read_csv(f'{data_dir}/store_to_kitchen_report.csv')
        self.sales_df = pd.read_csv(f'{data_dir}/sales_report.csv')
        self._process_dates()
    
    def _process_dates(self):
        if self.purchase_df is not None:
            self.purchase_df['Date'] = pd.to_datetime(self.purchase_df['Date'])
        if self.stk_df is not None:
            self.stk_df['Date'] = pd.to_datetime(self.stk_df['Date'])
        if self.sales_df is not None:
            self.sales_df['Date'] = pd.to_datetime(self.sales_df['Date'])
    
    def leakage_analysis(self):
        """Leakage & Waste: Compare purchased vs issued"""
        purchased = self.purchase_df.groupby('Item Name').agg({
            'Quantity': 'sum',
            'Amount': 'sum',
            'Unit': 'first'
        }).rename(columns={'Quantity': 'Total Purchased'})
        
        issued = self.stk_df.groupby('Item Name').agg({
            'Quantity Issued': 'sum'
        }).rename(columns={'Quantity Issued': 'Total Issued'})
        
        analysis = purchased.join(issued, how='outer').fillna(0)
        analysis['Difference'] = analysis['Total Purchased'] - analysis['Total Issued']
        analysis['Leakage %'] = (analysis['Difference'] / analysis['Total Purchased'] * 100).round(2)
        analysis['Value Lost'] = (analysis['Difference'] / analysis['Total Purchased'] * analysis['Amount']).round(2)
        analysis = analysis.replace([np.inf, -np.inf], 0).fillna(0)
        
        return analysis.sort_values('Leakage %', ascending=False).reset_index()
    
    def consumption_analysis(self):
        """Daily Consumption Pattern: Analyze kitchen usage trends"""
        daily = self.stk_df.groupby(['Date', 'Item Name']).agg({
            'Quantity Issued': 'sum'
        }).reset_index()
        
        # Get top 10 most used items
        top_items = self.stk_df.groupby('Item Name')['Quantity Issued'].sum().nlargest(10).index.tolist()
        
        # Calculate daily average and variance for each item
        consumption = []
        for item in top_items:
            item_data = daily[daily['Item Name'] == item]['Quantity Issued']
            consumption.append({
                'Item Name': item,
                'Total Used': float(item_data.sum()),
                'Daily Avg': float(item_data.mean()),
                'Daily Max': float(item_data.max()),
                'Daily Min': float(item_data.min()),
                'Std Dev': float(item_data.std()),
                'Consistency %': float(100 - (item_data.std() / item_data.mean() * 100)) if item_data.mean() > 0 else 0
            })
        
        return sorted(consumption, key=lambda x: x['Total Used'], reverse=True)
    
    def price_trends(self):
        """Price Trend Analysis for top ingredients"""
        top_items = self.purchase_df.groupby('Item Name')['Amount'].sum().nlargest(5).index.tolist()
        
        trends = []
        for item in top_items:
            item_data = self.purchase_df[self.purchase_df['Item Name'] == item].sort_values('Date')
            if len(item_data) > 0:
                first_price = item_data.iloc[0]['Rate']
                last_price = item_data.iloc[-1]['Rate']
                change = ((last_price - first_price) / first_price * 100) if first_price > 0 else 0
                
                trends.append({
                    'item': item,
                    'first_price': float(first_price),
                    'last_price': float(last_price),
                    'change': round(change, 2),
                    'dates': [d.strftime('%Y-%m-%d') for d in item_data['Date']],
                    'prices': item_data['Rate'].tolist()
                })
        
        return trends
    
    def menu_engineering(self):
        """Menu Engineering based on Sales only"""
        menu = self.sales_df.groupby('Item Name').agg({
            'Quantity Sold': 'sum',
            'Revenue': 'sum',
            'Food Cost': 'sum',
            'Profit': 'sum',
            'Category': 'first'
        }).reset_index()
        
        menu['Profit Margin %'] = (menu['Profit'] / menu['Revenue'] * 100).round(2)
        
        avg_pop = menu['Quantity Sold'].mean()
        avg_profit = menu['Profit Margin %'].mean()
        
        def classify(row):
            high_pop = row['Quantity Sold'] >= avg_pop
            high_profit = row['Profit Margin %'] >= avg_profit
            if high_pop and high_profit: return 'STAR'
            elif high_pop: return 'PLOW HORSE'
            elif high_profit: return 'PUZZLE'
            else: return 'DOG'
        
        menu['Classification'] = menu.apply(classify, axis=1)
        
        return {
            'data': menu.to_dict('records'),
            'avg_popularity': round(avg_pop, 0),
            'avg_profit_margin': round(avg_profit, 2)
        }
    
    def daily_sales_trend(self):
        """Daily sales revenue trend"""
        daily = self.sales_df.groupby('Date').agg({
            'Revenue': 'sum',
            'Profit': 'sum',
            'Quantity Sold': 'sum'
        }).reset_index()
        
        daily['Date'] = daily['Date'].dt.strftime('%Y-%m-%d')
        return daily.to_dict('records')
    
    def get_summary(self):
        """Summary statistics"""
        return {
            'total_revenue': float(self.sales_df['Revenue'].sum()),
            'total_profit': float(self.sales_df['Profit'].sum()),
            'total_purchase': float(self.purchase_df['Amount'].sum()),
            'total_items_sold': int(self.sales_df['Quantity Sold'].sum()),
            'date_range': {
                'start': self.sales_df['Date'].min().strftime('%d %b %Y'),
                'end': self.sales_df['Date'].max().strftime('%d %b %Y')
            }
        }

# Global analyzer
analyzer = None

def load_default_data():
    global analyzer
    analyzer = RestaurantAnalyzer()
    analyzer.load_from_files('data')
    return analyzer

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/summary')
def api_summary():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.get_summary())

@app.route('/api/leakage')
def api_leakage():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.leakage_analysis().to_dict('records'))

@app.route('/api/consumption')
def api_consumption():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.consumption_analysis())

@app.route('/api/price-trends')
def api_price_trends():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.price_trends())

@app.route('/api/menu-engineering')
def api_menu_engineering():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.menu_engineering())

@app.route('/api/daily-sales')
def api_daily_sales():
    global analyzer
    if analyzer is None:
        load_default_data()
    return jsonify(analyzer.daily_sales_trend())

@app.route('/api/upload', methods=['POST'])
def upload_files():
    global analyzer
    
    try:
        files = {}
        required = ['purchase', 'stk', 'sales']
        
        for key in required:
            if key in request.files:
                file = request.files[key]
                if file.filename:
                    if file.filename.endswith('.csv'):
                        files[key] = pd.read_csv(file)
                    elif file.filename.endswith(('.xlsx', '.xls')):
                        files[key] = pd.read_excel(file)
        
        if len(files) == 3:
            analyzer = RestaurantAnalyzer(
                purchase_df=files['purchase'],
                stk_df=files['stk'],
                sales_df=files['sales']
            )
            analyzer._process_dates()
            return jsonify({'success': True, 'message': 'Files uploaded successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Please upload all 3 required files'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/reset')
def reset_data():
    global analyzer
    load_default_data()
    return jsonify({'success': True, 'message': 'Reset to sample data'})

if __name__ == '__main__':
    load_default_data()
    print("\n" + "="*50)
    print("  Restaurant Analysis Dashboard")
    print("  Open: http://localhost:5000")
    print("  Reports: Purchase, Store-to-Kitchen, Sales")
    print("  (No Recipe/BOM required)")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)

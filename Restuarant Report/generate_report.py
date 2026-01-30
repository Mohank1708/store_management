"""
Generate HTML Report with Visual Charts for Restaurant Analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from analysis import RestaurantAnalyzer

def generate_html_report():
    """Generate a comprehensive HTML report with charts"""
    
    analyzer = RestaurantAnalyzer()
    
    # Get all analysis results
    leakage_df = analyzer.leakage_waste_analysis()
    variance_df = analyzer.variance_analysis()
    price_trends = analyzer.price_trend_analysis()
    menu_df = analyzer.menu_engineering_analysis()
    
    # Calculate summary statistics
    total_purchase_value = analyzer.purchase_df['Amount'].sum()
    total_revenue = analyzer.sales_df['Revenue'].sum()
    total_profit = analyzer.sales_df['Profit'].sum()
    total_leakage = leakage_df['Value Lost (Rs)'].sum()
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurant Analysis Report - January 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e8e8e8;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}
        .card h3 {{
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #a8a8a8;
            margin-bottom: 10px;
        }}
        .card .value {{
            font-size: 2em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .card.alert {{
            border-color: #ff6b6b;
            background: rgba(255,107,107,0.1);
        }}
        .card.alert .value {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .card.success {{
            border-color: #51cf66;
            background: rgba(81,207,102,0.1);
        }}
        .card.success .value {{
            background: linear-gradient(135deg, #51cf66, #40c057);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(102, 126, 234, 0.5);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 span {{
            font-size: 0.7em;
            padding: 5px 12px;
            background: rgba(102, 126, 234, 0.3);
            border-radius: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(102, 126, 234, 0.2);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.05);
        }}
        .chart-container {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .badge.star {{ background: linear-gradient(135deg, #ffd700, #ffaa00); color: #000; }}
        .badge.plow {{ background: linear-gradient(135deg, #4dabf7, #339af0); color: #fff; }}
        .badge.puzzle {{ background: linear-gradient(135deg, #845ef7, #7048e8); color: #fff; }}
        .badge.dog {{ background: linear-gradient(135deg, #868e96, #495057); color: #fff; }}
        .badge.alert {{ background: linear-gradient(135deg, #ff6b6b, #ee5a5a); color: #fff; }}
        .badge.warning {{ background: linear-gradient(135deg, #ffa94d, #ff922b); color: #000; }}
        .badge.success {{ background: linear-gradient(135deg, #51cf66, #40c057); color: #000; }}
        .menu-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        .menu-category {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
        }}
        .menu-category h3 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .menu-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        @media (max-width: 768px) {{
            .menu-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Restaurant Analysis Report</h1>
            <p>Vegetarian Restaurant | North & South Indian Cuisine | January 2026</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
        </div>

        <div class="summary-cards">
            <div class="card success">
                <h3>Total Revenue</h3>
                <div class="value">Rs. {total_revenue:,.0f}</div>
            </div>
            <div class="card success">
                <h3>Total Profit</h3>
                <div class="value">Rs. {total_profit:,.0f}</div>
            </div>
            <div class="card">
                <h3>Purchase Value</h3>
                <div class="value">Rs. {total_purchase_value:,.0f}</div>
            </div>
            <div class="card alert">
                <h3>Estimated Leakage Loss</h3>
                <div class="value">Rs. {total_leakage:,.0f}</div>
            </div>
        </div>

        <!-- Analysis 1: Leakage & Waste -->
        <div class="section">
            <h2>Analysis 1: Leakage & Waste <span>Purchase vs Kitchen Issue</span></h2>
            <p style="margin-bottom: 20px; opacity: 0.8;">Compares total items purchased against items issued to kitchen to identify potential wastage, theft, or spoilage.</p>
            
            <div class="chart-container">
                <canvas id="leakageChart" height="300"></canvas>
            </div>
            
            <table style="margin-top: 30px;">
                <thead>
                    <tr>
                        <th>Ingredient</th>
                        <th>Purchased</th>
                        <th>Issued</th>
                        <th>Difference</th>
                        <th>Leakage %</th>
                        <th>Value Lost</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add leakage table rows
    for item, row in leakage_df.head(15).iterrows():
        status_class = "alert" if row['Leakage %'] > 15 else "warning" if row['Leakage %'] > 10 else "success"
        status_text = "HIGH" if row['Leakage %'] > 15 else "MEDIUM" if row['Leakage %'] > 10 else "OK"
        html_content += f"""
                    <tr>
                        <td>{item}</td>
                        <td>{row['Total Purchased']:.1f}</td>
                        <td>{row['Total Issued']:.1f}</td>
                        <td>{row['Difference']:.1f}</td>
                        <td>{row['Leakage %']:.1f}%</td>
                        <td>Rs. {row['Value Lost (Rs)']:,.0f}</td>
                        <td><span class="badge {status_class}">{status_text}</span></td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>

        <!-- Analysis 2: Variance Analysis -->
        <div class="section">
            <h2>Analysis 2: Theoretical vs Actual Consumption <span>Variance Analysis</span></h2>
            <p style="margin-bottom: 20px; opacity: 0.8;">Compares theoretical ingredient requirements (based on sales & recipes) against actual kitchen issues. Positive variance indicates over-usage.</p>
            
            <div class="chart-container">
                <canvas id="varianceChart" height="300"></canvas>
            </div>
            
            <table style="margin-top: 30px;">
                <thead>
                    <tr>
                        <th>Ingredient</th>
                        <th>Theoretical Need</th>
                        <th>Actual Issued</th>
                        <th>Variance</th>
                        <th>Variance %</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add variance table rows
    for item, row in variance_df.head(12).iterrows():
        if row['Variance %'] > 15:
            status_class = "alert"
            status_text = "OVER-USE"
        elif row['Variance %'] < -10:
            status_class = "warning"
            status_text = "UNDER-USE"
        else:
            status_class = "success"
            status_text = "NORMAL"
        html_content += f"""
                    <tr>
                        <td>{item}</td>
                        <td>{row['Theoretical Needed']:.1f}</td>
                        <td>{row['Actual Issued']:.1f}</td>
                        <td>{row['Variance']:+.1f}</td>
                        <td>{row['Variance %']:+.1f}%</td>
                        <td><span class="badge {status_class}">{status_text}</span></td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>

        <!-- Analysis 3: Price Trends -->
        <div class="section">
            <h2>Analysis 3: Purchase Price Trends <span>Top 5 Ingredients</span></h2>
            <p style="margin-bottom: 20px; opacity: 0.8;">Tracks price changes of the most-purchased ingredients over the month.</p>
            
            <div class="chart-container">
                <canvas id="priceChart" height="250"></canvas>
            </div>
            
            <table style="margin-top: 30px;">
                <thead>
                    <tr>
                        <th>Ingredient</th>
                        <th>Start Price</th>
                        <th>End Price</th>
                        <th>Change %</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add price trend table rows
    for item, data in price_trends.items():
        change = data['change']
        if change > 10:
            status_class = "alert"
            rec = "Find alternative vendors"
        elif change > 5:
            status_class = "warning"
            rec = "Monitor closely"
        elif change < -5:
            status_class = "success"
            rec = "Stock up now"
        else:
            status_class = "success"
            rec = "Price stable"
        html_content += f"""
                    <tr>
                        <td>{item}</td>
                        <td>Rs. {data['first_price']:.0f}</td>
                        <td>Rs. {data['last_price']:.0f}</td>
                        <td><span class="badge {status_class}">{change:+.1f}%</span></td>
                        <td>{rec}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>

        <!-- Analysis 4: Menu Engineering -->
        <div class="section">
            <h2>Analysis 4: Menu Engineering <span>BCG Matrix</span></h2>
            <p style="margin-bottom: 20px; opacity: 0.8;">Classifies menu items based on popularity and profitability to guide menu optimization decisions.</p>
            
            <div class="menu-grid">
"""
    
    # Menu Engineering Categories
    categories = [
        ('STAR', 'star', '⭐ Stars', 'High Profit + High Popularity - PROMOTE!'),
        ('PLOW HORSE', 'plow', '🐴 Plow Horses', 'High Popularity, Low Profit - Reduce Costs'),
        ('PUZZLE', 'puzzle', '🧩 Puzzles', 'High Profit, Low Popularity - Market Better'),
        ('DOG', 'dog', '🐕 Dogs', 'Low Profit + Low Popularity - Consider Removing')
    ]
    
    for cat, cls, title, desc in categories:
        items = menu_df[menu_df['Classification'] == cat].sort_values('Revenue', ascending=False)
        html_content += f"""
                <div class="menu-category">
                    <h3><span class="badge {cls}">{cat}</span> {title.split(' ', 1)[1] if ' ' in title else title}</h3>
                    <p style="font-size: 0.85em; opacity: 0.7; margin-bottom: 15px;">{desc}</p>
"""
        for item, row in items.iterrows():
            html_content += f"""
                    <div class="menu-item">
                        <span>{item}</span>
                        <span>Rs. {row['Revenue']:,.0f} | {row['Profit Margin %']:.0f}%</span>
                    </div>
"""
        html_content += """
                </div>
"""
    
    # Prepare chart data
    leakage_labels = leakage_df.head(10).index.tolist()
    leakage_purchased = leakage_df.head(10)['Total Purchased'].tolist()
    leakage_issued = leakage_df.head(10)['Total Issued'].tolist()
    
    variance_labels = variance_df.head(10).index.tolist()
    variance_theoretical = variance_df.head(10)['Theoretical Needed'].tolist()
    variance_actual = variance_df.head(10)['Actual Issued'].tolist()
    
    # Price chart data
    price_labels = list(price_trends.keys())
    price_first = [d['first_price'] for d in price_trends.values()]
    price_last = [d['last_price'] for d in price_trends.values()]
    
    html_content += f"""
            </div>
        </div>
    </div>

    <script>
        // Leakage Chart
        new Chart(document.getElementById('leakageChart'), {{
            type: 'bar',
            data: {{
                labels: {leakage_labels},
                datasets: [
                    {{
                        label: 'Purchased',
                        data: {leakage_purchased},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Issued to Kitchen',
                        data: {leakage_issued},
                        backgroundColor: 'rgba(118, 75, 162, 0.8)',
                        borderColor: 'rgba(118, 75, 162, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#e8e8e8' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});

        // Variance Chart
        new Chart(document.getElementById('varianceChart'), {{
            type: 'bar',
            data: {{
                labels: {variance_labels},
                datasets: [
                    {{
                        label: 'Theoretical Need',
                        data: {variance_theoretical},
                        backgroundColor: 'rgba(81, 207, 102, 0.8)',
                        borderColor: 'rgba(81, 207, 102, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Actual Issued',
                        data: {variance_actual},
                        backgroundColor: 'rgba(255, 107, 107, 0.8)',
                        borderColor: 'rgba(255, 107, 107, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#e8e8e8' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});

        // Price Trend Chart
        new Chart(document.getElementById('priceChart'), {{
            type: 'bar',
            data: {{
                labels: {price_labels},
                datasets: [
                    {{
                        label: 'Start Price (Rs)',
                        data: {price_first},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'End Price (Rs)',
                        data: {price_last},
                        backgroundColor: 'rgba(255, 169, 77, 0.8)',
                        borderColor: 'rgba(255, 169, 77, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#e8e8e8' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#a8a8a8' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    # Save the report
    with open('restaurant_analysis_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nHTML Report saved to: restaurant_analysis_report.html")
    return html_content


if __name__ == "__main__":
    generate_html_report()

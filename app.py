"""
Store Management System - Flask Web Application
Role-based inventory management for vegetable restaurant
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import pandas as pd
import os
from datetime import datetime

from database import init_db, migrate_db, verify_user, get_inventory, add_item, remove_item, get_transactions, get_inventory_summary, manager_add_item, manager_update_item, manager_delete_item, cleanup_old_transactions, get_categories, add_category, update_category, delete_category
app = Flask(__name__)
app.secret_key = 'store_management_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize and migrate database on startup
init_db()
migrate_db()

# ============== Authentication Decorators ==============

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============== Authentication Routes ==============

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'manager':
            return redirect(url_for('manager_dashboard'))
        elif role == 'purchase':
            return redirect(url_for('purchase_dashboard'))
        elif role == 'kitchen':
            return redirect(url_for('kitchen_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            # Determine redirect URL based on role
            if user['role'] == 'manager':
                redirect_url = url_for('manager_dashboard')
            elif user['role'] == 'purchase':
                redirect_url = url_for('purchase_dashboard')
            else:
                redirect_url = url_for('kitchen_dashboard')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': redirect_url, 'role': user['role']})
            return redirect(redirect_url)
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

# ============== Dashboard Routes ==============

@app.route('/manager')
@login_required
@role_required(['manager'])
def manager_dashboard():
    """Manager view-only dashboard"""
    return render_template('manager.html', username=session.get('username'))

@app.route('/purchase')
@login_required
@role_required(['purchase'])
def purchase_dashboard():
    """Purchase manager dashboard"""
    return render_template('purchase.html', username=session.get('username'))

@app.route('/kitchen')
@login_required
@role_required(['kitchen'])
def kitchen_dashboard():
    """Kitchen manager dashboard"""
    return render_template('kitchen.html', username=session.get('username'))

# ============== API Routes ==============

@app.route('/api/inventory')
@login_required
def api_inventory():
    """Get current inventory"""
    inventory = get_inventory()
    # Round quantities to 3 decimal places to avoid floating point display issues
    for item in inventory:
        if 'quantity' in item:
            item['quantity'] = round(item['quantity'], 3)
        if 'total_purchased' in item:
            item['total_purchased'] = round(item['total_purchased'], 3)
    summary = get_inventory_summary()
    return jsonify({
        'inventory': inventory,
        'summary': summary,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/transactions')
@login_required
def api_transactions():
    """Get transaction history - max 30 days, with date range filter"""
    # Auto-cleanup old transactions
    cleanup_old_transactions()
    
    transaction_type = request.args.get('type')
    from_date = request.args.get('from_date')  # Format: YYYY-MM-DD
    to_date = request.args.get('to_date')  # Format: YYYY-MM-DD
    date_filter = request.args.get('date')  # Single date filter (backward compatible)
    limit = request.args.get('limit', 100, type=int)
    
    transactions = get_transactions(
        limit=limit, 
        transaction_type=transaction_type, 
        date_filter=date_filter,
        from_date=from_date,
        to_date=to_date
    )
    # Round quantities to 3 decimal places
    for t in transactions:
        if 'quantity' in t:
            t['quantity'] = round(t['quantity'], 3)
    return jsonify({'transactions': transactions})

@app.route('/api/transactions/export')
@login_required
def api_transactions_export():
    """Export transactions to Excel"""
    from io import BytesIO
    from flask import send_file
    
    transaction_type = request.args.get('type')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    transactions = get_transactions(
        limit=500,
        transaction_type=transaction_type,
        from_date=from_date,
        to_date=to_date
    )
    
    if not transactions:
        return jsonify({'error': 'No transactions to export'}), 404
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    # Rename columns for better readability
    column_map = {
        'created_at': 'Date/Time',
        'item_name': 'Item Name',
        'category': 'Category',
        'quantity': 'Quantity',
        'unit': 'Unit',
        'transaction_type': 'Type',
        'username': 'User',
        'rate': 'Rate (₹)',
        'amount': 'Amount (₹)',
        'vendor': 'Vendor',
        'notes': 'Notes'
    }
    df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
    
    # Remove internal columns
    cols_to_remove = ['id', 'user_id']
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns], errors='ignore')
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
    output.seek(0)
    
    # Generate filename
    type_label = transaction_type or 'all'
    date_label = f"{from_date}_to_{to_date}" if from_date and to_date else datetime.now().strftime('%Y-%m-%d')
    filename = f"transactions_{type_label}_{date_label}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/purchase', methods=['POST'])
@login_required
@role_required(['purchase'])
def api_purchase():
    """Add purchased items"""
    data = request.get_json()
    
    item_name = data.get('item_name')
    category = data.get('category')
    quantity = float(data.get('quantity', 0))
    unit = data.get('unit')
    rate = data.get('rate')
    amount = data.get('amount')
    vendor = data.get('vendor')
    
    if not all([item_name, category, quantity, unit]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    success = add_item(
        item_name=item_name,
        category=category,
        quantity=quantity,
        unit=unit,
        user_id=session['user_id'],
        username=session['username'],
        rate=rate,
        amount=amount,
        vendor=vendor
    )
    
    if success:
        return jsonify({'success': True, 'message': f'Added {quantity} {unit} of {item_name}'})
    return jsonify({'success': False, 'error': 'Failed to add item'}), 500

@app.route('/api/purchase/preview', methods=['POST'])
@login_required
@role_required(['purchase'])
def api_purchase_preview():
    """Preview Excel file contents before uploading"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Find item name column (flexible matching)
        item_col = None
        for col in df.columns:
            if 'item' in col.lower() or 'name' in col.lower() or 'product' in col.lower():
                item_col = col
                break
        if not item_col and len(df.columns) > 0:
            item_col = df.columns[0]  # Default to first column
        
        # Find quantity column
        qty_col = None
        for col in df.columns:
            if 'qty' in col.lower() or 'quantity' in col.lower() or 'amount' in col.lower():
                qty_col = col
                break
        
        if not item_col:
            return jsonify({'success': False, 'error': 'Could not find Item Name column'}), 400
        
        # Get existing inventory for auto-detection
        existing_inventory = {item['item_name'].lower(): item for item in get_inventory()}
        
        # Category detection keywords (order matters - first match wins)
        category_keywords = {
            'Beverages': ['juice', 'water', 'soda', 'cola', 'pepsi', 'coke', 'fanta', 'sprite', 'coffee', 'tea', 'drink', 'energy drink', 'lassi', 'buttermilk', 'milkshake', 'smoothie', 'beer', 'wine', 'alcohol'],
            'Bread': ['bread', 'bun', 'toast', 'roti', 'naan', 'paratha', 'chapati', 'pita', 'baguette', 'croissant', 'bagel', 'muffin', 'roll', 'loaf', 'pav'],
            'Dairy': ['milk', 'curd', 'paneer', 'ghee', 'butter', 'cream', 'cheese', 'yogurt', 'khoya', 'mawa', 'dahi', 'whey', 'cottage'],
            'Desserts': ['cake', 'pastry', 'sweet', 'candy', 'chocolate', 'ice cream', 'pudding', 'halwa', 'gulab jamun', 'rasgulla', 'ladoo', 'barfi', 'jalebi', 'kheer', 'custard', 'cookie', 'biscuit', 'mithai'],
            'Frozen Foods': ['frozen', 'ice', 'fries', 'nuggets', 'patty', 'samosa', 'paratha frozen', 'peas frozen', 'corn frozen', 'mixed veg frozen'],
            'Fruits': ['apple', 'banana', 'orange', 'mango', 'grape', 'papaya', 'watermelon', 'lemon', 'lime', 'pomegranate', 'guava', 'pineapple', 'strawberry', 'kiwi', 'chikoo', 'sapota', 'custard apple', 'mosambi', 'sweet lime', 'coconut', 'cherry', 'peach', 'plum'],
            'Grocery': ['rice', 'wheat', 'flour', 'atta', 'maida', 'rava', 'semolina', 'sooji', 'besan', 'gram', 'dal', 'lentil', 'chana', 'moong', 'toor', 'urad', 'rajma', 'chickpea', 'poha', 'oats', 'corn', 'millet', 'ragi', 'jowar', 'bajra', 'basmati', 'salt', 'sugar', 'jaggery', 'honey', 'oil', 'spice', 'masala', 'powder', 'pickle', 'papad', 'chips', 'vinegar', 'soya', 'tamarind', 'noodles', 'pasta', 'vermicelli'],
            'Sauce': ['sauce', 'ketchup', 'mayonnaise', 'mustard', 'chutney', 'dip', 'dressing', 'soy sauce', 'hot sauce', 'bbq', 'sriracha', 'salsa', 'pesto', 'gravy'],
            'Vegetable': ['onion', 'tomato', 'potato', 'carrot', 'capsicum', 'cabbage', 'cauliflower', 'beans', 'peas', 'brinjal', 'ladies finger', 'okra', 'spinach', 'palak', 'methi', 'coriander', 'curry leaves', 'ginger', 'garlic', 'green chilli', 'drumstick', 'beetroot', 'radish', 'cucumber', 'gourd', 'pumpkin', 'bhindi', 'aloo', 'pyaz', 'tamatar', 'shimla mirch', 'gobhi', 'gajar', 'pudina', 'mint', 'dhaniya', 'lettuce', 'celery', 'mushroom']
        }
        
        # Unit detection keywords
        unit_keywords = {
            'BTL': ['bottle', 'btl', 'drink', 'soda', 'cola', 'beer', 'wine', 'juice bottle'],
            'KG': ['rice', 'flour', 'atta', 'maida', 'sugar', 'salt', 'dal', 'vegetable', 'fruit', 'meat', 'chicken', 'fish', 'potato', 'onion', 'tomato'],
            'LTR': ['milk', 'oil', 'ghee', 'curd', 'buttermilk', 'juice', 'water', 'cream', 'lassi', 'sauce', 'ketchup', 'liter', 'litre'],
            'NOS': ['coconut', 'egg', 'lemon', 'lime', 'papaya', 'watermelon', 'pumpkin', 'cabbage', 'cauliflower', 'drumstick'],
            'PCS': ['bread', 'bun', 'roll', 'samosa', 'patty', 'nugget', 'cake', 'pastry', 'muffin', 'cookie', 'piece', 'slice'],
            'PKT': ['chips', 'biscuit', 'noodles', 'pasta', 'packet', 'pack', 'frozen', 'masala', 'spice'],
            'TIN': ['tin', 'can', 'canned', 'condensed']
        }
        
        def detect_category(item_name):
            name_lower = item_name.lower()
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        return category
            return 'Grocery'  # Default
        
        def detect_unit(item_name):
            name_lower = item_name.lower()
            for unit, keywords in unit_keywords.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        return unit
            return 'KG'  # Default
        
        # Find category and unit columns in Excel
        cat_col = None
        unit_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'category' in col_lower or 'cat' in col_lower:
                cat_col = col
            if 'unit' in col_lower:
                unit_col = col
        
        # Valid categories and units (case-insensitive matching)
        valid_categories = ['Beverages', 'Bread', 'Dairy', 'Desserts', 'Frozen Foods', 'Fruits', 'Grocery', 'Sauce', 'Vegetable']
        valid_categories_lower = {c.lower(): c for c in valid_categories}  # For case-insensitive lookup
        valid_units = ['BTL', 'KG', 'LTR', 'NOS', 'PCS', 'PKT', 'TIN']
        valid_units_lower = {u.lower(): u for u in valid_units}  # For case-insensitive lookup
        
        # Convert to list of dicts for preview
        items = []
        for idx, row in df.iterrows():
            item_name = str(row[item_col]).strip()
            if not item_name or item_name.lower() == 'nan':
                continue
            
            # Try to get quantity
            quantity = 0
            if qty_col and pd.notna(row.get(qty_col)):
                try:
                    quantity = float(row[qty_col])
                except:
                    quantity = 0
            
            # Priority 1: Read category from Excel if column exists
            category = None
            unit = None
            
            if cat_col and pd.notna(row.get(cat_col)):
                excel_cat = str(row[cat_col]).strip().lower()
                # Case-insensitive lookup
                if excel_cat in valid_categories_lower:
                    category = valid_categories_lower[excel_cat]
            
            if unit_col and pd.notna(row.get(unit_col)):
                excel_unit = str(row[unit_col]).strip().lower()
                # Case-insensitive lookup
                if excel_unit in valid_units_lower:
                    unit = valid_units_lower[excel_unit]
            
            # Priority 2: Check if item exists in inventory
            category_source = None
            if not category or not unit:
                existing = existing_inventory.get(item_name.lower())
                if existing:
                    if not category:
                        category = existing['category']
                        category_source = 'inventory'
                    if not unit:
                        unit = existing['unit']
            
            # Priority 3: Auto-detect from item name (needs review)
            auto_detected = False
            if not category:
                category = detect_category(item_name)
                auto_detected = True  # Flag for UI to show warning
                category_source = 'auto'
            if not unit:
                unit = detect_unit(item_name)
            
            # Get optional columns
            rate = None
            vendor = None
            for col in df.columns:
                if 'rate' in col.lower() or 'price' in col.lower():
                    if pd.notna(row.get(col)):
                        try:
                            rate = float(row[col])
                        except:
                            pass
                if 'vendor' in col.lower() or 'supplier' in col.lower():
                    if pd.notna(row.get(col)):
                        vendor = str(row[col])
            
            items.append({
                'item_name': item_name,
                'category': category,
                'quantity': quantity,
                'unit': unit,
                'rate': rate,
                'amount': rate * quantity if rate else None,
                'vendor': vendor,
                'auto_detected': auto_detected
            })
        
        # Check for items with auto-detected categories
        warning_items = [item['item_name'] for item in items if item.get('auto_detected')]
        
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items),
            'warning_count': len(warning_items),
            'warning_items': warning_items
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error reading file: {str(e)}'}), 500

@app.route('/api/purchase/upload', methods=['POST'])
@login_required
@role_required(['purchase'])
def api_purchase_upload():
    """Upload items from confirmed preview"""
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'success': False, 'error': 'No items to upload'}), 400
    
    items = data['items']
    added_count = 0
    errors = []
    
    for idx, item in enumerate(items):
        try:
            add_item(
                item_name=item['item_name'],
                category=item['category'],
                quantity=float(item['quantity']),
                unit=item['unit'],
                user_id=session['user_id'],
                username=session['username'],
                rate=item.get('rate'),
                amount=item.get('amount'),
                vendor=item.get('vendor')
            )
            added_count += 1
        except Exception as e:
            errors.append(f"Item {idx + 1}: {str(e)}")
    
    return jsonify({
        'success': True,
        'message': f'Successfully added {added_count} items',
        'errors': errors if errors else None
    })

@app.route('/api/kitchen', methods=['POST'])
@login_required
@role_required(['kitchen'])
def api_kitchen():
    """Remove items sent to kitchen"""
    data = request.get_json()
    
    item_name = data.get('item_name')
    quantity = float(data.get('quantity', 0))
    notes = data.get('notes')
    
    if not item_name or quantity <= 0:
        return jsonify({'success': False, 'error': 'Invalid item or quantity'}), 400
    
    success, message = remove_item(
        item_name=item_name,
        quantity=quantity,
        user_id=session['user_id'],
        username=session['username'],
        notes=notes
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@app.route('/api/items')
@login_required
def api_items():
    """Get list of item names for autocomplete - only items in stock"""
    inventory = get_inventory()
    # Only show items that have been purchased (quantity > 0)
    items = [{'name': item['item_name'], 'category': item['category'], 'unit': item['unit']} 
             for item in inventory if item['quantity'] > 0]
    return jsonify({'items': items})

# ============== Manager CRUD API ==============

@app.route('/api/manager/add', methods=['POST'])
@login_required
@role_required(['manager'])
def api_manager_add():
    """Manager adds a new item to inventory"""
    data = request.json
    
    item_name = data.get('item_name', '').strip()
    category = data.get('category', '').strip()
    quantity = data.get('quantity', 0)
    unit = data.get('unit', 'Kg').strip()
    
    if not item_name or not category:
        return jsonify({'success': False, 'error': 'Item name and category are required'}), 400
    
    success, message = manager_add_item(
        item_name=item_name,
        category=category,
        quantity=float(quantity),
        unit=unit,
        user_id=session['user_id'],
        username=session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@app.route('/api/manager/update', methods=['PUT'])
@login_required
@role_required(['manager'])
def api_manager_update():
    """Manager updates an existing inventory item"""
    data = request.json
    
    original_name = data.get('original_name', '').strip()
    item_name = data.get('item_name', '').strip()
    category = data.get('category', '').strip()
    quantity = data.get('quantity', 0)
    unit = data.get('unit', 'Kg').strip()
    
    if not original_name or not item_name or not category:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    success, message = manager_update_item(
        original_name=original_name,
        item_name=item_name,
        category=category,
        quantity=float(quantity),
        unit=unit,
        user_id=session['user_id'],
        username=session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@app.route('/api/manager/delete', methods=['DELETE'])
@login_required
@role_required(['manager'])
def api_manager_delete():
    """Manager deletes an item from inventory"""
    data = request.json
    
    item_name = data.get('item_name', '').strip()
    
    if not item_name:
        return jsonify({'success': False, 'error': 'Item name is required'}), 400
    
    success, message = manager_delete_item(
        item_name=item_name,
        user_id=session['user_id'],
        username=session['username']
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

# ============== Category Management API ==============

@app.route('/api/categories')
@login_required
def api_get_categories():
    """Get all categories"""
    categories = get_categories()
    return jsonify({'categories': categories})

@app.route('/api/categories/add', methods=['POST'])
@login_required
@role_required(['manager'])
def api_add_category():
    """Add a new category"""
    data = request.json
    name = data.get('name', '').strip()
    icon = data.get('icon', '📦').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Category name is required'}), 400
    
    success, message = add_category(name, icon)
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@app.route('/api/categories/update', methods=['PUT'])
@login_required
@role_required(['manager'])
def api_update_category():
    """Update a category"""
    data = request.json
    category_id = data.get('id')
    new_name = data.get('name', '').strip()
    new_icon = data.get('icon', '📦').strip()
    
    if not category_id or not new_name:
        return jsonify({'success': False, 'error': 'Category ID and name are required'}), 400
    
    success, message = update_category(category_id, new_name, new_icon)
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@app.route('/api/categories/delete', methods=['DELETE'])
@login_required
@role_required(['manager'])
def api_delete_category():
    """Delete a category"""
    data = request.json
    category_id = data.get('id')
    
    if not category_id:
        return jsonify({'success': False, 'error': 'Category ID is required'}), 400
    
    success, message = delete_category(category_id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400



# ============== Main ==============

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("  Store Management System")
    print("  Open: http://localhost:5001")
    print("="*60)
    print("  Users:")
    print("    - manager / ashishsir7777 (View Only)")
    print("    - purchase_manager / purchase123 (Add Items)")
    print("    - kitchen_manager / kitchen123 (Remove Items)")
    print("="*60 + "\n")
    app.run(debug=True, port=5001, host='0.0.0.0')


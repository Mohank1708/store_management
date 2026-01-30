"""
Store Management System - Flask Web Application
Role-based inventory management for vegetable restaurant
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import pandas as pd
import os
from datetime import datetime

from database import init_db, verify_user, get_inventory, add_item, remove_item, get_transactions, get_inventory_summary, manager_add_item, manager_update_item, manager_delete_item

app = Flask(__name__)
app.secret_key = 'store_management_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database on startup (for production servers)
init_db()

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
    summary = get_inventory_summary()
    return jsonify({
        'inventory': inventory,
        'summary': summary,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/transactions')
@login_required
def api_transactions():
    """Get transaction history"""
    transaction_type = request.args.get('type')
    limit = request.args.get('limit', 50, type=int)
    transactions = get_transactions(limit=limit, transaction_type=transaction_type)
    return jsonify({'transactions': transactions})

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
        
        # Validate required columns
        required_cols = ['Item Name', 'Category', 'Quantity', 'Unit']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({'success': False, 'error': f'Missing columns: {", ".join(missing_cols)}'}), 400
        
        # Convert to list of dicts for preview
        items = []
        for idx, row in df.iterrows():
            items.append({
                'item_name': str(row['Item Name']),
                'category': str(row['Category']),
                'quantity': float(row['Quantity']),
                'unit': str(row['Unit']),
                'rate': row.get('Rate') if pd.notna(row.get('Rate')) else None,
                'amount': row.get('Amount') if pd.notna(row.get('Amount')) else None,
                'vendor': str(row.get('Vendor')) if pd.notna(row.get('Vendor')) else None
            })
        
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
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
    """Get list of item names for autocomplete"""
    inventory = get_inventory()
    items = [{'name': item['item_name'], 'category': item['category'], 'unit': item['unit']} for item in inventory]
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

"""
Google Sheets Database Module
Replaces SQLite with Google Sheets for persistent storage on Render
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
import hashlib

# Google Sheets configuration
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1QL8yeuM5wPwJ4q28L3RgfK5mq_AQ4Nob9B5PiQiJbyQ')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Global client
_client = None
_spreadsheet = None


def get_spreadsheet():
    """Get or create Google Sheets connection"""
    global _client, _spreadsheet
    
    if _spreadsheet is not None:
        return _spreadsheet
    
    # Get credentials from environment variable
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    print(f"[DEBUG] GOOGLE_CREDENTIALS exists: {bool(creds_json)}")
    print(f"[DEBUG] GOOGLE_SHEET_ID: {SHEET_ID}")
    
    if creds_json:
        try:
            # Parse JSON from environment variable
            creds_dict = json.loads(creds_json)
            print(f"[DEBUG] Credentials parsed successfully, type: {creds_dict.get('type')}")
            print(f"[DEBUG] Client email: {creds_dict.get('client_email')}")
            credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            print("[DEBUG] Credentials created successfully")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse GOOGLE_CREDENTIALS JSON: {e}")
            raise
    else:
        print("[DEBUG] No GOOGLE_CREDENTIALS env var, trying credentials.json file")
        # For local development, use credentials file
        credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    
    _client = gspread.authorize(credentials)
    print("[DEBUG] gspread authorized successfully")
    
    _spreadsheet = _client.open_by_key(SHEET_ID)
    print("[DEBUG] Spreadsheet opened successfully")
    
    return _spreadsheet


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Initialize the Google Sheets with default data if empty"""
    try:
        spreadsheet = get_spreadsheet()
        
        # Initialize users sheet
        users_sheet = spreadsheet.worksheet('users')
        users_data = users_sheet.get_all_values()
        
        if len(users_data) <= 1:  # Only header or empty
            # Add headers and default users
            users_sheet.clear()
            users_sheet.append_row(['username', 'password_hash', 'role'])
            default_users = [
                ['manager', hash_password('manager123'), 'manager'],
                ['purchase_manager', hash_password('purchase123'), 'purchase_manager'],
                ['kitchen_manager', hash_password('kitchen123'), 'kitchen_manager']
            ]
            for user in default_users:
                users_sheet.append_row(user)
        
        # Initialize inventory sheet
        inventory_sheet = spreadsheet.worksheet('inventory')
        inventory_data = inventory_sheet.get_all_values()
        
        if len(inventory_data) <= 1:
            inventory_sheet.clear()
            inventory_sheet.append_row(['item_name', 'category', 'quantity', 'unit', 'total_purchased', 'last_updated'])
        
        # Initialize transactions sheet
        transactions_sheet = spreadsheet.worksheet('transactions')
        transactions_data = transactions_sheet.get_all_values()
        
        if len(transactions_data) <= 1:
            transactions_sheet.clear()
            transactions_sheet.append_row(['item_name', 'category', 'quantity', 'unit', 'type', 'user', 'timestamp', 'notes', 'rate', 'total_amount', 'vendor'])
        
        # Initialize categories sheet
        categories_sheet = spreadsheet.worksheet('categories')
        categories_data = categories_sheet.get_all_values()
        
        if len(categories_data) <= 1:
            categories_sheet.clear()
            categories_sheet.append_row(['name', 'icon'])
            default_categories = [
                ['Beverages', '🥤'],
                ['Bread', '🍞'],
                ['Dairy', '🥛'],
                ['Desserts', '🍰'],
                ['Frozen Foods', '❄️'],
                ['Fruits', '🍎'],
                ['Grocery', '🛒'],
                ['Sauce', '🫙'],
                ['Vegetable', '🥬']
            ]
            for cat in default_categories:
                categories_sheet.append_row(cat)
        
        print("Google Sheets database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def migrate_db():
    """No migration needed for Google Sheets"""
    pass


def verify_user(username, password):
    """Verify user credentials - returns dict with id, username, role"""
    try:
        print(f"[DEBUG] Attempting login for user: {username}")
        spreadsheet = get_spreadsheet()
        users_sheet = spreadsheet.worksheet('users')
        users = users_sheet.get_all_records()
        
        print(f"[DEBUG] Found {len(users)} users in sheet")
        
        password_hash = hash_password(password)
        print(f"[DEBUG] Entered password hash: {password_hash}")
        
        for idx, user in enumerate(users):
            stored_hash = str(user.get('password_hash', '')).strip()
            stored_username = str(user.get('username', '')).strip()
            
            print(f"[DEBUG] Checking user: '{stored_username}'")
            print(f"[DEBUG] Match username: {stored_username == username}, Match hash: {stored_hash == password_hash}")
            
            if stored_username == username and stored_hash == password_hash:
                print(f"[DEBUG] Login successful! Role: {user['role']}")
                # Return dict with id, username, role as expected by app.py
                return {
                    'id': idx + 1,  # Use row index as ID
                    'username': stored_username,
                    'role': user['role']
                }
        
        print(f"[DEBUG] No matching user found")
        return None
    except Exception as e:
        print(f"[ERROR] Error verifying user: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_inventory():
    """Get all inventory items"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        items = inventory_sheet.get_all_records()
        
        # Convert to proper format
        result = []
        for idx, item in enumerate(items, start=2):  # Start from 2 (row 1 is header)
            result.append({
                'id': idx,
                'item_name': item.get('item_name', ''),
                'category': item.get('category', ''),
                'quantity': float(item.get('quantity', 0)) if item.get('quantity') else 0,
                'unit': item.get('unit', 'KG'),
                'total_purchased': float(item.get('total_purchased', 0)) if item.get('total_purchased') else 0,
                'last_updated': item.get('last_updated', '')
            })
        
        return result
    except Exception as e:
        print(f"Error getting inventory: {e}")
        return []


def add_item(item_name, category, quantity, unit, username, rate=0, vendor='', notes=''):
    """Add item to inventory (purchase)"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        transactions_sheet = spreadsheet.worksheet('transactions')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_amount = float(quantity) * float(rate) if rate else 0
        
        # Check if item exists
        items = inventory_sheet.get_all_records()
        item_found = False
        
        for idx, item in enumerate(items, start=2):
            if item['item_name'].lower() == item_name.lower():
                # Update existing item
                new_quantity = float(item.get('quantity', 0)) + float(quantity)
                new_total = float(item.get('total_purchased', 0)) + float(quantity)
                
                inventory_sheet.update_cell(idx, 3, new_quantity)  # quantity column
                inventory_sheet.update_cell(idx, 5, new_total)  # total_purchased column
                inventory_sheet.update_cell(idx, 6, timestamp)  # last_updated column
                item_found = True
                break
        
        if not item_found:
            # Add new item
            inventory_sheet.append_row([
                item_name, category, float(quantity), unit, float(quantity), timestamp
            ])
        
        # Log transaction
        transactions_sheet.append_row([
            item_name, category, float(quantity), unit, 'purchase', username, 
            timestamp, notes, float(rate), total_amount, vendor
        ])
        
        return True
    except Exception as e:
        print(f"Error adding item: {e}")
        return False


def remove_item(item_name, quantity, username, notes=''):
    """Remove item from inventory (issue to kitchen)"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        transactions_sheet = spreadsheet.worksheet('transactions')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        items = inventory_sheet.get_all_records()
        
        for idx, item in enumerate(items, start=2):
            if item['item_name'].lower() == item_name.lower():
                current_qty = float(item.get('quantity', 0))
                
                if current_qty >= float(quantity):
                    new_quantity = current_qty - float(quantity)
                    inventory_sheet.update_cell(idx, 3, new_quantity)
                    inventory_sheet.update_cell(idx, 6, timestamp)
                    
                    # Log transaction
                    transactions_sheet.append_row([
                        item_name, item.get('category', ''), float(quantity), 
                        item.get('unit', 'KG'), 'issue', username, timestamp, notes, 0, 0, ''
                    ])
                    
                    return True
                else:
                    return False
        
        return False
    except Exception as e:
        print(f"Error removing item: {e}")
        return False


def get_transactions(transaction_type=None, limit=100, date_filter=None, from_date=None, to_date=None):
    """Get transactions with optional type and date filters"""
    try:
        spreadsheet = get_spreadsheet()
        transactions_sheet = spreadsheet.worksheet('transactions')
        transactions = transactions_sheet.get_all_records()
        
        # Filter by type if specified
        if transaction_type:
            transactions = [t for t in transactions if t.get('type') == transaction_type]
        
        # Filter by single date
        if date_filter:
            transactions = [t for t in transactions if t.get('timestamp', '').startswith(date_filter)]
        
        # Filter by date range
        if from_date:
            transactions = [t for t in transactions if t.get('timestamp', '')[:10] >= from_date]
        if to_date:
            transactions = [t for t in transactions if t.get('timestamp', '')[:10] <= to_date]
        
        # Sort by timestamp descending and limit
        transactions = sorted(transactions, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
        
        return transactions
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []


def get_inventory_summary():
    """Get inventory summary statistics"""
    try:
        inventory = get_inventory()
        
        total_items = len(inventory)
        in_stock = len([i for i in inventory if i['quantity'] > 0])
        out_of_stock = len([i for i in inventory if i['quantity'] <= 0])
        low_stock = len([i for i in inventory if 0 < i['quantity'] <= 5])
        
        return {
            'total_items': total_items,
            'in_stock': in_stock,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock
        }
    except Exception as e:
        print(f"Error getting summary: {e}")
        return {'total_items': 0, 'in_stock': 0, 'out_of_stock': 0, 'low_stock': 0}


def manager_add_item(item_name, category, quantity, unit):
    """Manager adds item directly to inventory"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if item exists
        items = inventory_sheet.get_all_records()
        
        for idx, item in enumerate(items, start=2):
            if item['item_name'].lower() == item_name.lower():
                # Update existing
                new_quantity = float(item.get('quantity', 0)) + float(quantity)
                inventory_sheet.update_cell(idx, 3, new_quantity)
                inventory_sheet.update_cell(idx, 6, timestamp)
                return True
        
        # Add new
        inventory_sheet.append_row([item_name, category, float(quantity), unit, float(quantity), timestamp])
        return True
    except Exception as e:
        print(f"Error in manager_add_item: {e}")
        return False


def manager_update_item(item_id, **kwargs):
    """Manager updates an item"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        
        row = item_id  # item_id is the row number
        
        if 'item_name' in kwargs:
            inventory_sheet.update_cell(row, 1, kwargs['item_name'])
        if 'category' in kwargs:
            inventory_sheet.update_cell(row, 2, kwargs['category'])
        if 'quantity' in kwargs:
            inventory_sheet.update_cell(row, 3, float(kwargs['quantity']))
        if 'unit' in kwargs:
            inventory_sheet.update_cell(row, 4, kwargs['unit'])
        
        inventory_sheet.update_cell(row, 6, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return True
    except Exception as e:
        print(f"Error updating item: {e}")
        return False


def manager_delete_item(item_id):
    """Manager deletes an item"""
    try:
        spreadsheet = get_spreadsheet()
        inventory_sheet = spreadsheet.worksheet('inventory')
        
        inventory_sheet.delete_rows(item_id)
        return True
    except Exception as e:
        print(f"Error deleting item: {e}")
        return False


def cleanup_old_transactions(days=30):
    """Delete transactions older than specified days"""
    try:
        from datetime import timedelta
        spreadsheet = get_spreadsheet()
        transactions_sheet = spreadsheet.worksheet('transactions')
        transactions = transactions_sheet.get_all_values()
        
        if len(transactions) <= 1:  # Only header
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Find rows to delete (go in reverse to avoid index shifting)
        rows_to_delete = []
        for idx, row in enumerate(transactions[1:], start=2):  # Skip header
            if len(row) >= 7:  # Ensure timestamp column exists
                timestamp = row[6]  # timestamp is column 7 (index 6)
                if timestamp and timestamp[:10] < cutoff_date:
                    rows_to_delete.append(idx)
        
        # Delete rows in reverse order to maintain correct indices
        deleted = 0
        for row_idx in reversed(rows_to_delete):
            transactions_sheet.delete_rows(row_idx)
            deleted += 1
        
        print(f"Cleaned up {deleted} transactions older than {days} days")
        return deleted
    except Exception as e:
        print(f"Error cleaning up transactions: {e}")
        return 0


def get_categories():
    """Get all categories"""
    try:
        spreadsheet = get_spreadsheet()
        categories_sheet = spreadsheet.worksheet('categories')
        categories = categories_sheet.get_all_records()
        
        result = []
        for idx, cat in enumerate(categories, start=2):
            result.append({
                'id': idx,
                'name': cat.get('name', ''),
                'icon': cat.get('icon', '📦')
            })
        
        return result
    except Exception as e:
        print(f"Error getting categories: {e}")
        return []


def add_category(name, icon='📦'):
    """Add a new category"""
    try:
        spreadsheet = get_spreadsheet()
        categories_sheet = spreadsheet.worksheet('categories')
        categories_sheet.append_row([name, icon])
        return True
    except Exception as e:
        print(f"Error adding category: {e}")
        return False


def update_category(category_id, name=None, icon=None):
    """Update a category"""
    try:
        spreadsheet = get_spreadsheet()
        categories_sheet = spreadsheet.worksheet('categories')
        
        if name:
            categories_sheet.update_cell(category_id, 1, name)
        if icon:
            categories_sheet.update_cell(category_id, 2, icon)
        
        return True
    except Exception as e:
        print(f"Error updating category: {e}")
        return False


def delete_category(category_id):
    """Delete a category"""
    try:
        spreadsheet = get_spreadsheet()
        categories_sheet = spreadsheet.worksheet('categories')
        categories_sheet.delete_rows(category_id)
        return True
    except Exception as e:
        print(f"Error deleting category: {e}")
        return False

"""
Store Management System Database
SQLite database with users, inventory, and transactions
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta

DATABASE_PATH = 'store_management.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database with tables and default users"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create store inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL,
            total_purchased REAL NOT NULL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rate REAL,
            amount REAL,
            vendor TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT DEFAULT '📦',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize default categories
    default_categories = [
        ('Beverages', '🥤'),
        ('Bread', '🍞'),
        ('Dairy', '🥛'),
        ('Desserts', '🍰'),
        ('Frozen Foods', '❄️'),
        ('Fruits', '🍎'),
        ('Grocery', '🛒'),
        ('Sauce', '🫙'),
        ('Vegetable', '🥬')
    ]
    
    for name, icon in default_categories:
        try:
            cursor.execute('INSERT INTO categories (name, icon) VALUES (?, ?)', (name, icon))
        except sqlite3.IntegrityError:
            pass  # Category already exists
    
    # Create default users
    default_users = [
        ('manager', 'ashishsir7777', 'manager'),
        ('purchase_manager', 'purchase123', 'purchase'),
        ('kitchen_manager', 'kitchen123', 'kitchen')
    ]
    
    for username, password, role in default_users:
        try:
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, hash_password(password), role)
            )
        except sqlite3.IntegrityError:
            pass  # User already exists
    
    # Initialize default inventory items (empty - items will be added via purchases)
    default_items = []
    
    for item_name, category, quantity, unit in default_items:
        cursor.execute('''
            INSERT OR IGNORE INTO store_inventory (item_name, category, quantity, unit)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM store_inventory WHERE item_name = ?)
        ''', (item_name, category, quantity, unit, item_name))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def migrate_db():
    """Add total_purchased column if it doesn't exist (for existing databases)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT total_purchased FROM store_inventory LIMIT 1')
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        cursor.execute('ALTER TABLE store_inventory ADD COLUMN total_purchased REAL NOT NULL DEFAULT 0')
        # Initialize total_purchased from current quantity for existing items
        cursor.execute('UPDATE store_inventory SET total_purchased = quantity WHERE total_purchased = 0 AND quantity > 0')
        conn.commit()
        print("Database migrated: added total_purchased column")
    
    conn.close()

def get_low_stock_items(threshold_percent=10):
    """Get items where current quantity is below threshold% of total purchased"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT item_name, category, quantity, unit, total_purchased,
               (total_purchased * ? / 100.0) as threshold
        FROM store_inventory 
        WHERE total_purchased > 0 
        AND quantity < (total_purchased * ? / 100.0)
        ORDER BY item_name
    ''', (threshold_percent, threshold_percent))
    
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def verify_user(username, password):
    """Verify user credentials and return user data"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, role FROM users WHERE username = ? AND password = ?',
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_inventory():
    """Get all inventory items"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM store_inventory ORDER BY category, item_name')
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def add_item(item_name, category, quantity, unit, user_id, username, rate=None, amount=None, vendor=None):
    """Add items to inventory (purchase)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Round quantity to 3 decimal places to avoid floating point issues
    quantity = round(quantity, 3)
    
    # Check if item exists
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if existing:
        # Calculate new quantities with rounding
        new_qty = round(existing['quantity'] + quantity, 3)
        new_total = round(existing['total_purchased'] + quantity, 3)
        # Update quantity and total purchased
        cursor.execute(
            'UPDATE store_inventory SET quantity = ?, total_purchased = ?, last_updated = ? WHERE item_name = ?',
            (new_qty, new_total, datetime.now(), item_name)
        )
    else:
        # Insert new item
        cursor.execute(
            'INSERT INTO store_inventory (item_name, category, quantity, unit, total_purchased, last_updated) VALUES (?, ?, ?, ?, ?, ?)',
            (item_name, category, quantity, unit, quantity, datetime.now())
        )
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, rate, amount, vendor, created_at)
        VALUES (?, ?, ?, ?, 'purchase', ?, ?, ?, ?, ?, ?)
    ''', (item_name, category, quantity, unit, user_id, username, rate, amount, vendor, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True

def remove_item(item_name, quantity, user_id, username, notes=None):
    """Remove items from inventory (sent to kitchen)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Round input quantity to 3 decimal places
    quantity = round(quantity, 3)
    
    # Check if item exists and has enough quantity
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return False, "Item not found in inventory"
    
    # Round existing quantity for comparison (handle floating point errors)
    available_qty = round(existing['quantity'], 3)
    
    # Use small tolerance for comparison to handle floating point errors
    if available_qty + 0.001 < quantity:
        conn.close()
        return False, f"Not enough stock. Available: {available_qty} {existing['unit']}"
    
    # Calculate new quantity and round it
    new_quantity = round(available_qty - quantity, 3)
    # Ensure we don't go negative due to floating point
    if new_quantity < 0:
        new_quantity = 0
    
    # Update quantity with rounded value
    cursor.execute(
        'UPDATE store_inventory SET quantity = ?, last_updated = ? WHERE item_name = ?',
        (new_quantity, datetime.now(), item_name)
    )
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
        VALUES (?, ?, ?, ?, 'kitchen', ?, ?, ?, ?)
    ''', (item_name, existing['category'], quantity, existing['unit'], user_id, username, notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True, "Items removed successfully"

def get_transactions(limit=50, transaction_type=None, date_filter=None, from_date=None, to_date=None):
    """Get transaction history - only from last 30 days, with date range support"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate 30 days ago
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Build query dynamically based on filters
    query = "SELECT * FROM transactions WHERE created_at >= ?"
    params = [thirty_days_ago]
    
    if transaction_type:
        query += " AND transaction_type = ?"
        params.append(transaction_type)
    
    # Date range filter (from_date to to_date)
    if from_date and to_date:
        query += " AND DATE(created_at) >= ? AND DATE(created_at) <= ?"
        params.extend([from_date, to_date])
    elif from_date:
        query += " AND DATE(created_at) >= ?"
        params.append(from_date)
    elif to_date:
        query += " AND DATE(created_at) <= ?"
        params.append(to_date)
    elif date_filter:
        # Single date filter (backward compatible)
        query += " AND DATE(created_at) = ?"
        params.append(date_filter)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions

def cleanup_old_transactions():
    """Delete transactions older than 30 days"""
    conn = get_db()
    cursor = conn.cursor()
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor.execute('DELETE FROM transactions WHERE DATE(created_at) < ?', (thirty_days_ago,))
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    return deleted

def get_inventory_summary():
    """Get inventory summary by category"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, 
               COUNT(*) as item_count,
               SUM(CASE WHEN quantity > 0 THEN 1 ELSE 0 END) as in_stock,
               SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) as out_of_stock
        FROM store_inventory 
        GROUP BY category
        ORDER BY category
    ''')
    summary = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return summary

# ============== Manager CRUD Operations ==============

def manager_add_item(item_name, category, quantity, unit, user_id, username):
    """Manager adds a new item directly to inventory"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if item already exists
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return False, "Item already exists. Use edit to modify."
    
    # Add new item
    cursor.execute('''
        INSERT INTO store_inventory (item_name, category, quantity, unit, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', (item_name, category, quantity, unit, datetime.now()))
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
        VALUES (?, ?, ?, ?, 'manager_add', ?, ?, 'Added by manager', ?)
    ''', (item_name, category, quantity, unit, user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True, "Item added successfully"

def manager_update_item(original_name, item_name, category, quantity, unit, user_id, username):
    """Manager updates an existing inventory item"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if item exists and get current quantity
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (original_name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return False, "Item not found"
    
    old_quantity = existing['quantity']
    
    # If renaming, check the new name doesn't already exist
    if original_name != item_name:
        cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
        if cursor.fetchone():
            conn.close()
            return False, "An item with that name already exists"
    
    # Update item
    cursor.execute('''
        UPDATE store_inventory 
        SET item_name = ?, category = ?, quantity = ?, unit = ?, last_updated = ?
        WHERE item_name = ?
    ''', (item_name, category, quantity, unit, datetime.now(), original_name))
    
    # Log transaction ONLY if quantity changed
    quantity_diff = quantity - old_quantity
    if quantity_diff != 0:
        # Determine if it's an addition or reduction
        if quantity_diff > 0:
            txn_type = 'purchase'  # Added stock
        else:
            txn_type = 'kitchen'   # Reduced stock
            quantity_diff = abs(quantity_diff)  # Store as positive
        
        cursor.execute('''
            INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Adjusted by Manager', ?)
        ''', (item_name, category, quantity_diff, unit, txn_type, user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True, "Item updated successfully"

def manager_delete_item(item_name, user_id, username):
    """Manager deletes an item from inventory"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if item exists
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return False, "Item not found"
    
    # Delete item
    cursor.execute('DELETE FROM store_inventory WHERE item_name = ?', (item_name,))
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
        VALUES (?, ?, ?, ?, 'manager_delete', ?, ?, 'Deleted by manager', ?)
    ''', (existing['item_name'], existing['category'], existing['quantity'], existing['unit'], user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True, "Item deleted successfully"

# ============== Category Management Functions ==============

def get_categories():
    """Get all categories"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories

def add_category(name, icon='📦'):
    """Add a new category"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO categories (name, icon) VALUES (?, ?)', (name, icon))
        conn.commit()
        conn.close()
        return True, "Category added successfully"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Category already exists"

def update_category(category_id, new_name, new_icon):
    """Update an existing category"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get old category name
    cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
    old_cat = cursor.fetchone()
    if not old_cat:
        conn.close()
        return False, "Category not found"
    
    old_name = old_cat['name']
    
    # Check if new name already exists (and it's not the same category)
    cursor.execute('SELECT id FROM categories WHERE name = ? AND id != ?', (new_name, category_id))
    if cursor.fetchone():
        conn.close()
        return False, "A category with that name already exists"
    
    # Update category
    cursor.execute('UPDATE categories SET name = ?, icon = ? WHERE id = ?', (new_name, new_icon, category_id))
    
    # Update all inventory items with old category name
    cursor.execute('UPDATE store_inventory SET category = ? WHERE category = ?', (new_name, old_name))
    
    conn.commit()
    conn.close()
    return True, "Category updated successfully"

def delete_category(category_id):
    """Delete a category (only if no items use it)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get category name
    cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
    cat = cursor.fetchone()
    if not cat:
        conn.close()
        return False, "Category not found"
    
    # Check if any items use this category
    cursor.execute('SELECT COUNT(*) as count FROM store_inventory WHERE category = ?', (cat['name'],))
    count = cursor.fetchone()['count']
    if count > 0:
        conn.close()
        return False, f"Cannot delete: {count} items use this category"
    
    # Delete category
    cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    
    conn.commit()
    conn.close()
    return True, "Category deleted successfully"

if __name__ == '__main__':
    init_db()

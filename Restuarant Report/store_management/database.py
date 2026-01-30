"""
Store Management System Database
SQLite database with users, inventory, and transactions
"""

import sqlite3
import hashlib
from datetime import datetime

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
    
    # Initialize default inventory items
    default_items = [
        ('Basmati Rice', 'Grains', 0, 'Kg'),
        ('Idli Rice', 'Grains', 0, 'Kg'),
        ('Atta (Wheat Flour)', 'Grains', 0, 'Kg'),
        ('Maida', 'Grains', 0, 'Kg'),
        ('Semolina (Rava)', 'Grains', 0, 'Kg'),
        ('Paneer', 'Dairy', 0, 'Kg'),
        ('Curd', 'Dairy', 0, 'Kg'),
        ('Ghee', 'Dairy', 0, 'Kg'),
        ('Onion', 'Vegetables', 0, 'Kg'),
        ('Tomato', 'Vegetables', 0, 'Kg'),
        ('Potato', 'Vegetables', 0, 'Kg'),
        ('Green Peas', 'Vegetables', 0, 'Kg'),
        ('Capsicum', 'Vegetables', 0, 'Kg'),
        ('Coconut', 'Vegetables', 0, 'Pcs'),
        ('Curry Leaves', 'Vegetables', 0, 'Kg'),
        ('Mustard Seeds', 'Spices', 0, 'Kg'),
        ('Cumin Seeds', 'Spices', 0, 'Kg'),
        ('Red Chilli Powder', 'Spices', 0, 'Kg'),
        ('Turmeric Powder', 'Spices', 0, 'Kg'),
        ('Garam Masala', 'Spices', 0, 'Kg'),
        ('Coriander Powder', 'Spices', 0, 'Kg'),
        ('Cooking Oil', 'Oil', 0, 'Ltr'),
    ]
    
    for item_name, category, quantity, unit in default_items:
        cursor.execute('''
            INSERT OR IGNORE INTO store_inventory (item_name, category, quantity, unit)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM store_inventory WHERE item_name = ?)
        ''', (item_name, category, quantity, unit, item_name))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

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
    
    # Check if item exists
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if existing:
        # Update quantity
        cursor.execute(
            'UPDATE store_inventory SET quantity = quantity + ?, last_updated = ? WHERE item_name = ?',
            (quantity, datetime.now(), item_name)
        )
    else:
        # Insert new item
        cursor.execute(
            'INSERT INTO store_inventory (item_name, category, quantity, unit, last_updated) VALUES (?, ?, ?, ?, ?)',
            (item_name, category, quantity, unit, datetime.now())
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
    
    # Check if item exists and has enough quantity
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (item_name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return False, "Item not found in inventory"
    
    if existing['quantity'] < quantity:
        conn.close()
        return False, f"Not enough stock. Available: {existing['quantity']} {existing['unit']}"
    
    # Update quantity
    cursor.execute(
        'UPDATE store_inventory SET quantity = quantity - ?, last_updated = ? WHERE item_name = ?',
        (quantity, datetime.now(), item_name)
    )
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
        VALUES (?, ?, ?, ?, 'kitchen', ?, ?, ?, ?)
    ''', (item_name, existing['category'], quantity, existing['unit'], user_id, username, notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return True, "Items removed successfully"

def get_transactions(limit=50, transaction_type=None):
    """Get transaction history"""
    conn = get_db()
    cursor = conn.cursor()
    
    if transaction_type:
        cursor.execute(
            'SELECT * FROM transactions WHERE transaction_type = ? ORDER BY created_at DESC LIMIT ?',
            (transaction_type, limit)
        )
    else:
        cursor.execute(
            'SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
    
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions

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
    
    # Check if item exists
    cursor.execute('SELECT * FROM store_inventory WHERE item_name = ?', (original_name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return False, "Item not found"
    
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
    
    # Log transaction
    cursor.execute('''
        INSERT INTO transactions (item_name, category, quantity, unit, transaction_type, user_id, username, notes, created_at)
        VALUES (?, ?, ?, ?, 'manager_edit', ?, ?, 'Edited by manager', ?)
    ''', (item_name, category, quantity, unit, user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
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

if __name__ == '__main__':
    init_db()

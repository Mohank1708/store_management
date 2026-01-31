"""
Telegram Alert System for Low Stock Notifications
Sends alerts when inventory items fall below 10% of total purchased quantity
"""

import requests
from datetime import datetime

# Telegram Configuration
BOT_TOKEN = "8536189070:AAHXsID8fwdNqBopBGhn-IC7BYFbZjyjesk"
CHAT_ID = "5623652286"

def send_telegram_message(message):
    """Send a message via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_low_stock_alert(item_name, current_qty, threshold, unit):
    """Send alert for a specific low stock item"""
    message = f"""🚨 <b>LOW STOCK ALERT</b> 🚨

<b>Item:</b> {item_name}
<b>Current Stock:</b> {current_qty:.1f} {unit}
<b>Threshold (10%):</b> {threshold:.1f} {unit}

⚠️ Please restock soon!
📅 {datetime.now().strftime('%d %b %Y, %I:%M %p')}"""
    
    return send_telegram_message(message)

def send_bulk_alert(low_stock_items):
    """Send a single alert for multiple low stock items"""
    if not low_stock_items:
        return True
    
    items_list = "\n".join([
        f"• <b>{item['item_name']}</b>: {item['quantity']:.1f} {item['unit']} (min: {item['threshold']:.1f})"
        for item in low_stock_items
    ])
    
    message = f"""🚨 <b>LOW STOCK ALERT</b> 🚨

{len(low_stock_items)} items are below 10% stock:

{items_list}

⚠️ Please restock these items!
📅 {datetime.now().strftime('%d %b %Y, %I:%M %p')}"""
    
    return send_telegram_message(message)

def test_connection():
    """Test Telegram bot connection"""
    message = f"""✅ <b>Bhagath Store Alert System Connected!</b>

Your low stock alerts are now active.
You will receive notifications when any item falls below 10% of total purchased quantity.

📅 {datetime.now().strftime('%d %b %Y, %I:%M %p')}"""
    
    return send_telegram_message(message)

# system_notifications.py
from datetime import datetime

def send_welcome_notification(data, user_id, username):
    """নতুন ব্যবহারকারীর জন্য স্বাগতম নোটিফিকেশন তৈরি করে।"""
    data['notification_counter'] += 1
    notification = {
        "id": data['notification_counter'],
        "message": f"স্বাগতম, {username}! আমাদের ওয়েবসাইটে আপনার অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে।",
        "user_id": user_id,
        "is_global": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender": "System",
        "type": "system"
    }
    data['notifications'].append(notification)
    return data

def send_system_warning(data, message, user_id=None):
    """
    সিস্টেম ওয়ার্নিং বা কোনো বার্তা পাঠায়।
    user_id দিলে নির্দিষ্ট ব্যবহারকারী পাবে, না দিলে সবাই পাবে।
    """
    data['notification_counter'] += 1
    notification = {
        "id": data['notification_counter'],
        "message": message,
        "user_id": user_id,
        "is_global": user_id is None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender": "System",
        "type": "system"
    }
    data['notifications'].append(notification)
    return data
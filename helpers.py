import json
import os
import uuid
from functools import wraps
from flask import session, redirect, url_for, flash
from datetime import datetime, timedelta

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "users": [], 
            "notifications": [], 
            "notes": [],
            "guest_usage": {},
            "user_counter": 0, 
            "notification_counter": 0, 
            "note_counter": 0,
            "rate_limit_settings": {
                "notes": {"limit": 15, "period_hours": 12},
                "facebook_downloader": {"limit": 15, "period_hours": 12},
                "instagram_downloader": {"limit": 15, "period_hours": 12}
            }
        }
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"users": [], "notifications": [], "notes": [], "guest_usage": {}, "user_counter": 0, "notification_counter": 0, "note_counter": 0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_by_id(user_id):
    data = load_data()
    for user in data.get('users', []):
        if user.get('id') == user_id:
            return user
    return None

def get_app_statistics():
    data = load_data()
    stats = {
        "total_users": len(data.get("users", [])),
        "total_notes": len(data.get("notes", [])),
        "total_notifications": len(data.get("notifications", []))
    }
    return stats

def get_unread_notification_count(user_id):
    data = load_data()
    user = get_user_by_id(user_id)
    if not user:
        return 0
    read_ids = set(user.get("read_notification_ids", []))
    relevant_notifications = [
        n for n in data.get('notifications', [])
        if n.get('is_global') or n.get('user_id') == user_id
    ]
    unread_count = sum(1 for n in relevant_notifications if n['id'] not in read_ids)
    return unread_count

def increment_user_usage(user_id, tool_name):
    data = load_data()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if user:
        if 'usage_tracking' not in user:
            user['usage_tracking'] = {}
        if tool_name not in user['usage_tracking']:
             user['usage_tracking'][tool_name] = {'count': 0, 'reset_time': datetime.now().isoformat()}
        user['usage_tracking'][tool_name]['count'] += 1
        save_data(data)

def increment_guest_usage(guest_id, tool_name):
    data = load_data()
    if 'guest_usage' not in data: data['guest_usage'] = {}
    if guest_id not in data['guest_usage']: data['guest_usage'][guest_id] = {}
    if tool_name not in data['guest_usage'][guest_id]:
        data['guest_usage'][guest_id][tool_name] = {
            'count_1h': 0, 'reset_time_1h': datetime.now().isoformat(),
            'count_12h': 0, 'reset_time_12h': datetime.now().isoformat()
        }
    data['guest_usage'][guest_id][tool_name]['count_1h'] += 1
    data['guest_usage'][guest_id][tool_name]['count_12h'] += 1
    save_data(data)

def rate_limited(tool_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = load_data()
            if 'user_id' in session:
                user = get_user_by_id(session['user_id'])
                if not user: return redirect(url_for('auth.login'))
                settings = data.get("rate_limit_settings", {}).get(tool_name, {"limit": 15, "period_hours": 12})
                if 'usage_tracking' not in user: user['usage_tracking'] = {}
                if tool_name not in user['usage_tracking']:
                    user['usage_tracking'][tool_name] = {'count': 0, 'reset_time': datetime.now().isoformat()}
                usage_info = user['usage_tracking'][tool_name]
                reset_time = datetime.fromisoformat(usage_info['reset_time'])
                if datetime.now() > reset_time + timedelta(hours=settings['period_hours']):
                    usage_info['count'] = 0
                    usage_info['reset_time'] = datetime.now().isoformat()
                    save_data(data)
                if usage_info['count'] >= settings['limit']:
                    remaining_time = (reset_time + timedelta(hours=settings['period_hours'])) - datetime.now()
                    hours, rem = divmod(remaining_time.seconds, 3600)
                    minutes, _ = divmod(rem, 60)
                    flash(f"আপনি এই টুলটি ব্যবহারের দৈনিক সীমায় পৌঁছে গেছেন। অনুগ্রহ করে প্রায় {hours} ঘণ্টা {minutes} মিনিট পর আবার চেষ্টা করুন।", "error")
                    return redirect(url_for('auth.home'))
            else:
                if 'guest_id' not in session:
                    session['guest_id'] = str(uuid.uuid4())
                guest_id = session['guest_id']

                # --- KeyError ঠিক করার জন্য নতুন অংশ ---
                if 'guest_usage' not in data:
                    data['guest_usage'] = {}
                # --- শেষ ---

                if guest_id not in data['guest_usage']: data['guest_usage'][guest_id] = {}
                if tool_name not in data['guest_usage'][guest_id]:
                    data['guest_usage'][guest_id][tool_name] = {
                        'count_1h': 0, 'reset_time_1h': datetime.now().isoformat(),
                        'count_12h': 0, 'reset_time_12h': datetime.now().isoformat()
                    }
                usage = data['guest_usage'][guest_id][tool_name]
                if datetime.now() > datetime.fromisoformat(usage['reset_time_1h']) + timedelta(hours=1):
                    usage['count_1h'] = 0
                    usage['reset_time_1h'] = datetime.now().isoformat()
                if datetime.now() > datetime.fromisoformat(usage['reset_time_12h']) + timedelta(hours=12):
                    usage['count_12h'] = 0
                    usage['reset_time_12h'] = datetime.now().isoformat()
                save_data(data)
                if usage['count_1h'] >= 1 or usage['count_12h'] >= 10:
                    flash("আপনি অতিথি হিসেবে ব্যবহারের সীমায় পৌঁছে গেছেন। আরও ব্যবহার করতে অনুগ্রহ করে লগইন করুন।", "error")
                    return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("এই পেইজটি দেখার জন্য অনুগ্রহ করে লগইন করুন।", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user = get_user_by_id(session.get("user_id"))
        if not user or not user.get("is_admin"):
            flash("এই পেইজ দেখার জন্য আপনার অনুমতি নেই।", "error")
            return redirect(url_for("auth.home"))
        return f(*args, **kwargs)
    return decorated_function
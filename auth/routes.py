from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import load_data, save_data, login_required, get_user_by_id
from system_notifications import send_welcome_notification
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# login, signup, logout, home, profile, change_password রুট অপরিবর্তিত থাকবে
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        data = load_data()
        user = next((u for u in data.get('users', []) if u['username'] == username), None)
        if user and check_password_hash(user['password'], password):
            if not user.get("is_active", True):
                flash("আপনার অ্যাকাউন্টটি নিষ্ক্রিয় করা হয়েছে। অনুগ্রহ করে এডমিনের সাথে যোগাযোগ করুন।", "error")
                return redirect(url_for('auth.login'))
            if remember:
                session.permanent = True
            session['user_id'] = user['id']
            flash('সফলভাবে লগইন করেছেন!', 'success')
            return redirect(url_for('auth.home'))
        else:
            flash('ইউজারনেম বা পাসওয়ার্ড সঠিক নয়।', 'error')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        data = load_data()
        if any(u['username'] == username for u in data.get('users', [])):
            flash('এই নামে একজন ইউজার আগে থেকেই আছে।', 'error')
        else:
            data['user_counter'] = data.get('user_counter', 0) + 1
            new_user = {
                "id": data['user_counter'], "username": username, "display_name": username,
                "password": generate_password_hash(password), "is_admin": username == 'admin',
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_active": True, "read_notification_ids": [], "usage_tracking": {}
            }
            data.setdefault('users', []).append(new_user)
            data = send_welcome_notification(data, new_user['id'], new_user['username'])
            save_data(data)
            session['user_id'] = new_user['id']
            flash('অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে!', 'success')
            return redirect(url_for('auth.home'))
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('আপনি সফলভাবে লগআউট করেছেন।', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def home():
    return render_template("index.html")

@auth_bp.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    data = load_data()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if user:
        relevant_notification_ids = {n['id'] for n in data.get('notifications', []) if n.get('is_global') or n.get('user_id') == user_id}
        read_ids = set(user.get("read_notification_ids", []))
        read_ids.update(relevant_notification_ids)
        user["read_notification_ids"] = list(read_ids)
        save_data(data)

    all_user_notifications = [n for n in data.get('notifications', []) if n.get('is_global') or n.get('user_id') == user_id]
    
    recent_notifications = []
    for n in all_user_notifications:
        timestamp_str = n.get('timestamp')
        if not timestamp_str: continue
        try:
            notification_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - notification_time < timedelta(days=15):
                if datetime.now() - notification_time < timedelta(hours=1):
                    n['is_new'] = True
                recent_notifications.append(n)
        except (ValueError, TypeError):
            continue
            
    recent_notifications.sort(key=lambda x: x['id'], reverse=True)
    
    # পরিসংখ্যান (stats) পাঠানোর অংশটি সরিয়ে দেওয়া হয়েছে
    return render_template('notifications.html', notifications=recent_notifications)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        new_display_name = request.form.get('display_name')
        if new_display_name and len(new_display_name) >= 3:
            data = load_data()
            for u in data['users']:
                if u['id'] == user['id']:
                    u['display_name'] = new_display_name
                    break
            save_data(data)
            flash('আপনার নাম সফলভাবে পরিবর্তন করা হয়েছে।', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('প্রদর্শনের নাম কমপক্ষে ৩ অক্ষরের হতে হবে।', 'error')
    return render_template('profile.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user = get_user_by_id(session['user_id'])
        if not check_password_hash(user['password'], current_password):
            flash('আপনার বর্তমান পাসওয়ার্ডটি সঠিক নয়।', 'error')
        elif new_password != confirm_password:
            flash('নতুন পাসওয়ার্ড এবং কনফার্ম পাসওয়ার্ড মিলছে না।', 'error')
        else:
            data = load_data()
            for u in data['users']:
                if u['id'] == user['id']:
                    u['password'] = generate_password_hash(new_password)
                    break
            save_data(data)
            flash('আপনার পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে।', 'success')
            return redirect(url_for('auth.profile'))
    return render_template('change_password.html')
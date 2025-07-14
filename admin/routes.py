from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from helpers import load_data, save_data, admin_required, get_app_statistics, get_user_by_id
from system_notifications import send_system_warning
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    stats = get_app_statistics()
    return render_template('admin_dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_required
def user_list():
    data = load_data()
    users = data.get('users', [])
    return render_template('admin_user_list.html', users=users)

@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    data = load_data()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if user:
        user['is_admin'] = not user.get('is_admin', False)
        save_data(data)
        flash(f"'{user['username']}' এর এডমিন স্ট্যাটাস পরিবর্তন করা হয়েছে।", 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/toggle_active/<int:user_id>', methods=['POST'])
@admin_required
def toggle_active(user_id):
    data = load_data()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if user:
        user['is_active'] = not user.get('is_active', True)
        save_data(data)
        flash(f"'{user['username']}' এর অ্যাকাউন্ট স্ট্যাটাস পরিবর্তন করা হয়েছে।", 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/broadcast', methods=['GET', 'POST'])
@admin_required
def broadcast():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            data = load_data()
            updated_data = send_system_warning(data, message)
            save_data(updated_data)
            flash("সিস্টেম ব্রডকাস্ট সফলভাবে পাঠানো হয়েছে।", "success")
            return redirect(url_for('admin.broadcast'))
        else:
            flash("বার্তা খালি রাখা যাবে না।", "error")
    return render_template('admin_broadcast.html')

@admin_bp.route('/notification', methods=['GET', 'POST'])
@admin_required
def send_notification():
    data = load_data()
    if request.method == 'POST':
        message = request.form.get('message')
        target_user_id = request.form.get('target_user')
        admin_user = get_user_by_id(session['user_id'])
        if not message:
            flash('নোটিফিকেশন বার্তা খালি রাখা যাবে না।', 'error')
        else:
            data['notification_counter'] = data.get('notification_counter', 0) + 1
            new_notification = {
                "id": data['notification_counter'], "message": message, "user_id": None, "is_global": False,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sender": admin_user['username'], "type": "admin"
            }
            if target_user_id == 'all':
                new_notification['is_global'] = True
                flash('সকল ইউজারের কাছে নোটিফিকেশন পাঠানো হয়েছে।', 'success')
            else:
                new_notification['user_id'] = int(target_user_id)
                flash('নির্দিষ্ট ইউজারের কাছে নোটিফিকেশন পাঠানো হয়েছে।', 'success')
            data.setdefault('notifications', []).append(new_notification)
            save_data(data)
            return redirect(url_for('admin.send_notification'))
    normal_users = [u for u in data.get('users', []) if not u.get('is_admin')]
    return render_template('admin_notification.html', all_users=normal_users)

@admin_bp.route('/rate-limits', methods=['GET', 'POST'])
@admin_required
def rate_limits():
    data = load_data()
    if request.method == 'POST':
        tool_name = request.form.get('tool_name')
        limit = request.form.get('limit')
        period_hours = request.form.get('period_hours')
        if tool_name and limit and period_hours:
            if 'rate_limit_settings' not in data:
                data['rate_limit_settings'] = {}
            data['rate_limit_settings'][tool_name] = {"limit": int(limit), "period_hours": int(period_hours)}
            save_data(data)
            flash(f"'{tool_name}' টুলের রেট লিমিট আপডেট করা হয়েছে।", "success")
        else:
            flash("সবগুলো ফিল্ড পূরণ করুন।", "error")
        return redirect(url_for('admin.rate_limits'))
    settings = data.get('rate_limit_settings', {})
    return render_template('admin_rate_limits.html', settings=settings)
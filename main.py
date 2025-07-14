from flask import Flask, session
from helpers import get_user_by_id, get_unread_notification_count
from datetime import timedelta # <-- নতুন ইম্পোর্ট

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'a_very_secret_key_for_your_app'

    # "Remember Me" এর জন্য সেশনের সময়কাল ৩০ দিন নির্ধারণ
    app.permanent_session_lifetime = timedelta(days=30)

    # ব্লুপ্রিন্ট রেজিস্টার করা
    from auth.routes import auth_bp
    from admin.routes import admin_bp
    from notes.routes import notes_bp
    from static_pages.routes import static_pages_bp
    from facebook_downloader.routes import fb_dl_bp
    from instagram_downloader.routes import ig_dl_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(static_pages_bp)
    app.register_blueprint(fb_dl_bp)
    app.register_blueprint(ig_dl_bp)

    @app.context_processor
    def inject_user_and_notifications():
        """সব টেমপ্লেটে ইউজার এবং না পড়া নোটিফিকেশনের সংখ্যা পাঠিয়ে দেয়।"""
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])
            unread_count = get_unread_notification_count(session['user_id'])
            return dict(user=user, unread_count=unread_count)
        return dict(user=None, unread_count=0)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080)
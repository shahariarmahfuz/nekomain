from flask_login import UserMixin
from database import db # এই লাইনটি পরিবর্তন করা হয়েছে

# ইউজার টেবিলের জন্য মডেল
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# নোটিফিকেশন টেবিলের জন্য মডেল
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_global = db.Column(db.Boolean, default=False)
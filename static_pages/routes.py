from flask import Blueprint, render_template

static_pages_bp = Blueprint('static_pages', __name__)

@static_pages_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('pages/privacy_policy.html')

@static_pages_bp.route('/contact-us')
def contact_us():
    return render_template('pages/contact_us.html')

@static_pages_bp.route('/about-me')
def about_me():
    return render_template('pages/about_me.html')
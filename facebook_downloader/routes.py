import os
import requests
from flask import Blueprint, render_template, request, session, flash, jsonify
from helpers import rate_limited, increment_user_usage, increment_guest_usage
from datetime import datetime

fb_dl_bp = Blueprint('facebook_downloader', __name__, url_prefix='/tool')

API_URL = "https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink"
API_KEY = os.getenv('RAPIDAPI_KEY') 

@fb_dl_bp.route('/facebook-downloader', methods=['GET', 'POST'])
@rate_limited("facebook_downloader")
def download_video():
    # POST রিকোয়েস্ট এখন AJAX এর মাধ্যমে আসবে
    if request.method == 'POST':
        data = request.get_json()
        video_link = data.get('video_link')

        if not video_link:
            return jsonify({"error": True, "message": "Sorry, the link is empty. Please try again."}), 400

        if not API_KEY:
            return jsonify({"error": True, "message": "API key is not configured. Please contact the administrator."}), 500

        payload = {"url": video_link}
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "social-download-all-in-one.p.rapidapi.com"
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
            response.raise_for_status() 
            api_data = response.json()

            if api_data.get("error"):
                # কাস্টম এরর মেসেজ পাঠানো হচ্ছে
                return jsonify({"error": True, "message": "Sorry, not found. Please try again."}), 404
            else:
                duration_ms = api_data.get('duration', 0)
                if duration_ms and duration_ms > 0:
                    total_seconds = duration_ms // 1000
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    api_data['formatted_duration'] = f"{minutes} min {seconds} sec"
                else:
                    api_data['formatted_duration'] = "N/A"

                if api_data.get("medias"):
                    for media in api_data["medias"]:
                        if media.get('url'):
                            media['url'] = f"{media['url']}&dl=1"

                # সফল ব্যবহারের পর কাউন্ট বাড়ানো
                if 'user_id' in session:
                    increment_user_usage(session['user_id'], "facebook_downloader")
                else:
                    increment_guest_usage(session['guest_id'], "facebook_downloader")

                return jsonify(api_data)

        except requests.exceptions.RequestException:
            # নেটওয়ার্ক বা API এরর এর জন্য কাস্টম মেসেজ
            return jsonify({"error": True, "message": "Sorry, could not connect to the service. Please try again later."}), 500

    # GET রিকোয়েস্টে পেজটি দেখানো হবে
    return render_template('facebook_downloader.html')
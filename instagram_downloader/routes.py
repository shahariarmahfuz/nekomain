import os
import requests
import uuid
import threading
from flask import Blueprint, render_template, request, session, flash, url_for, jsonify
from helpers import rate_limited, increment_user_usage, increment_guest_usage

ig_dl_bp = Blueprint('instagram_downloader', __name__, url_prefix='/tool')

API_URL = "https://instagram-reels-downloader-api.p.rapidapi.com/download"
API_KEY = os.getenv('RAPIDAPI_KEY')
THUMBNAIL_DIR = os.path.join('static', 'thumbnails')

@ig_dl_bp.route('/instagram-downloader', methods=['GET', 'POST'])
@rate_limited("instagram_downloader")
def download_reel():
    if request.method == 'POST':
        data = request.get_json()
        video_link = data.get('video_link')

        if not video_link:
            return jsonify({"error": True, "message": "Sorry, the link is empty. Please try again."}), 400
        if not API_KEY:
            return jsonify({"error": True, "message": "API key is not configured."}), 500

        querystring = {"url": video_link}
        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "instagram-reels-downloader-api.p.rapidapi.com"
        }

        try:
            response = requests.get(API_URL, headers=headers, params=querystring, timeout=20)
            response.raise_for_status()
            api_response = response.json()

            if api_response.get("success"):
                results = api_response.get("data")

                thumbnail_url = results.get('thumbnail')
                if thumbnail_url:
                    try:
                        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
                        image_response = requests.get(thumbnail_url, stream=True, timeout=15)
                        image_response.raise_for_status()
                        file_extension = os.path.splitext(thumbnail_url.split('?')[0])[-1] or '.jpg'
                        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                        save_path = os.path.join(THUMBNAIL_DIR, unique_filename)
                        with open(save_path, 'wb') as f:
                            for chunk in image_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        results['local_thumbnail'] = url_for('static', filename=f'thumbnails/{unique_filename}')
                        threading.Timer(300, os.remove, args=[save_path]).start()
                    except Exception as img_e:
                        print(f"Thumbnail download error: {img_e}")
                        results['local_thumbnail'] = None

                if results and results.get("medias"):
                    for media in results["medias"]:
                        if media.get("url"):
                            media['url'] = f"{media['url']}&dl=1"

                if 'user_id' in session:
                    increment_user_usage(session['user_id'], "instagram_downloader")
                else:
                    increment_guest_usage(session['guest_id'], "instagram_downloader")

                return jsonify(results)
            else:
                return jsonify({"error": True, "message": "Sorry, not found. Please try again."}), 404
        except requests.exceptions.RequestException:
            return jsonify({"error": True, "message": "Sorry, could not connect to the service."}), 500

    return render_template('instagram_downloader.html')
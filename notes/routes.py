from flask import Blueprint, render_template, request, redirect, url_for, session
from helpers import load_data, save_data, login_required, rate_limited, increment_user_usage
from datetime import datetime

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET', 'POST'])
@login_required
@rate_limited("notes")
def my_notes():
    user_id = session['user_id']
    data = load_data()

    if request.method == 'POST':
        note_content = request.form.get('note_content')
        if note_content:
            data.setdefault('notes', [])
            data.setdefault('note_counter', 0)
            data['note_counter'] += 1
            new_note = {
                "id": data['note_counter'],
                "user_id": user_id,
                "content": note_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data['notes'].append(new_note)
            save_data(data)

            # এখানে সঠিক ফাংশনটির নাম ব্যবহার করা হয়েছে
            increment_user_usage(user_id, "notes")

            return redirect(url_for('notes.my_notes'))

    user_notes = [note for note in data.get('notes', []) if note['user_id'] == user_id]
    user_notes.sort(key=lambda x: x['id'], reverse=True)

    return render_template('notes.html', notes=user_notes)
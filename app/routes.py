from flask import render_template, request, jsonify
from app import app

# Simulated in-memory "database"
chats = {
    "ENG101": [],
    "CSC202": [],
    "MKT305": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/post-forum')
def post_forum():
    return render_template('post_forum.html')

# Units chat landing page (search & unit cards)
@app.route('/units-chat')
def units_chat():
    return render_template('units_chat.html')

@app.route('/units/<unit_code>')
def unit_chat(unit_code):
    return render_template('chat_ui.html', unit_code=unit_code)

# AJAX endpoint to get & post messages
@app.route('/units/<unit_code>/messages', methods=['GET', 'POST'])
def unit_messages(unit_code):
    if request.method == 'POST':
        new_msg = request.form.get('message')
        if new_msg:
            chats.setdefault(unit_code, []).append(new_msg)
            return jsonify({"status": "success"})
    return jsonify(chats.get(unit_code, []))

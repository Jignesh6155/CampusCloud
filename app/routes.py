from flask import render_template
from app import app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return render_template('base.html')

#route for the Post Forum page
@app.route('/post-forum')
def post_forum():
    return render_template('post_forum.html')

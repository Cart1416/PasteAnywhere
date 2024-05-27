from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for secure cookie encoding

# Ensure the userdata directory exists
if not os.path.exists('userdata'):
    os.makedirs('userdata')

def save_user(username, password):
    user_data = {
        'username': username,
        'password': generate_password_hash(password, method='pbkdf2:sha256'),
        'texts': []  # Initialize an empty list for storing texts
    }
    with open(f'userdata/{username}.json', 'w') as user_file:
        json.dump(user_data, user_file)

def load_user(username):
    try:
        with open(f'userdata/{username}.json', 'r') as user_file:
            return json.load(user_file)
    except FileNotFoundError:
        return None

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/public/<path:path>')
def public(path):
    return send_from_directory('public', path)
    
@app.route('/app')
def app_link():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login', next=request.url))
    return render_template('app.html', username=username)
    
@app.route('/app/new')
def app_new_link():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login', next=request.url))
    return render_template('app_new.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_page = request.args.get('next')
        if load_user(username):
            return "User already exists!", 400
        save_user(username, password)
        response = make_response(redirect(next_page or url_for('app_link')))
        response.set_cookie('username', username, httponly=True, samesite='Lax', secure=False)
        response.set_cookie('password', password, httponly=True, samesite='Lax', secure=False)
        return response
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_page = request.args.get('next')
        user_data = load_user(username)
        if user_data and check_password_hash(user_data['password'], password):
            response = make_response(redirect(next_page or url_for('app_link')))
            response.set_cookie('username', username, httponly=True, samesite='Lax', secure=False)
            return response
        else:
            return "Invalid username or password", 401
    else:  # If method is GET
        username = request.cookies.get('username')
        password = request.cookies.get('password')
        if username and password:
            user_data = load_user(username)
            if user_data and check_password_hash(user_data['password'], password):
                return redirect(request.args.get('next') or url_for('app_link'))
    return render_template('login.html')
    
@app.route('/api/text_add', methods=['POST'])
def text_add():
    username = request.cookies.get('username')
    text = request.json.get('text')
    if username and text:
        user_data = load_user(username)
        if user_data:
            user_data['texts'].append(text)
            with open(f'userdata/{username}.json', 'w') as user_file:
                json.dump(user_data, user_file)
            return jsonify({'message': 'Text added successfully'}), 200
    return jsonify({'error': 'Unauthorized or missing data'}), 401
    
@app.route('/api/text_get')
def text_get():
    username = request.cookies.get('username')
    if username:
        user_data = load_user(username)
        if user_data:
            texts = user_data.get('texts', [])
            return jsonify({'texts': texts}), 200
    return jsonify({'error': 'Unauthorized'}), 401
    
@app.route('/api/text_delete/<int:index>', methods=['DELETE'])
def text_delete(index):
    username = request.cookies.get('username')
    if username:
        user_data = load_user(username)
        if user_data and 0 <= index < len(user_data['texts']):
            del user_data['texts'][index]
            with open(f'userdata/{username}.json', 'w') as user_file:
                json.dump(user_data, user_file)
            return jsonify({'message': 'Text deleted successfully'}), 200
    return jsonify({'error': 'Unauthorized or invalid index'}), 401

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
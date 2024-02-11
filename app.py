import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import * # Flask, g, redirect, render_template, request, url_for
from functools import wraps
import hashlib

app = Flask(__name__)

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response

def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    print(cursor)
    rows = cursor.fetchall()
    print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one: 
            return rows[0]
        return rows
    return None

def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' + 
        'values (?, ?, ?) returning id, name, password, api_key',
        (name, password, api_key),
        one=True)
    return u

def get_user_from_cookie(request):
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None

def get_api_key(userid):
    api_key = query_db(f"SELECT api_key FROM users WHERE id = {userid}")
    return api_key[0][0]

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Api-Key')
        print(get_api_key(request.cookies.get('user_id')))
        if not api_key or api_key != get_api_key(request.cookies.get('user_id')):  # 确保这里是实际的 API 密钥
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------

@app.route('/')
def index():
    print("index") # For debugging
    user = get_user_from_cookie(request)
    print("cookies", request.cookies)
    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)
    
    return render_with_error_handling('index.html', user=None, rooms=None)

@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room") # For debugging
    user = get_user_from_cookie(request)
    if user is None: return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db('insert into rooms (name) values (?) returning id', [name], one=True)            
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')
    
    if request.method == 'POST':
        u = new_user()
        print("u")
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp
    
    return redirect('/login')

@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)
    
    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        u = query_db('select * from users where name = ? and password = ?', [name, password], one=True)
        if user:
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', u.id)
            resp.set_cookie('user_password', u.password)
            return resp

    return render_with_error_handling('login.html', failed=True)   

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp

@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None: return redirect('/')

    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
            room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------
# POST to change the user's name
@app.route('/api/user/name', methods=['POST'])
def update_username():
    user_id = request.cookies.get('user_id')
    new_username = request.json.get('new_username')
    if not user_id or not new_username:
        return jsonify({"error": "Missing user ID or new username"}), 400
    try:
        query_db("UPDATE users SET name = ? WHERE id = ?", [new_username, user_id])
        return jsonify({"success": "Username updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST to change the user's password
@app.route('/api/user/password', methods=['POST'])
def update_password():
    user_id = request.cookies.get('user_id')
    new_password = request.json.get('new_password')
    if not user_id or not new_password:
        return jsonify({"error": "Missing user ID or new password"}), 400
    try:
        query_db("UPDATE users SET password = ? WHERE id = ?", [new_password, user_id])
        response = make_response(jsonify({"success": "password updated successfully"}))
        response.set_cookie('user_password', new_password)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# POST to change the name of a room
@app.route('/api/rooms/<int:room_id>', methods=['POST'])
def update_room_name(room_id):
    user = get_user_from_cookie(request)
    if user is None:
        return {}, 403
    name = request.json.get('name')
    query_db("update rooms set name = ? where id = ?", [name, room_id])
    return {}, 200

# GET to get all the messages in a room
@app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
@require_api_key
def get_room_messages(room_id):
    messages = query_db("SELECT users.name, messages.body FROM messages INNER JOIN users ON messages.user_id = users.id WHERE messages.room_id = ?",
                         [room_id])
    if messages:
        return jsonify([dict(message) for message in messages]), 200
    else:
        return jsonify([]), 200

# POST to post a new message to a room
@app.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
@require_api_key
def post_message(room_id):
    body = request.json.get('body')
    user_id = request.cookies.get('user_id') 
    query_db('INSERT INTO messages (user_id, room_id, body) VALUES (?, ?, ?)', (user_id, room_id, body))
    return jsonify({"success": "Message posted"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


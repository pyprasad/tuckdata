from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pymongo import MongoClient
from bson.objectid import ObjectId
import jwt
import datetime
import secrets
import openai
import stripe
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.environ.get(
    'MONGO_URI', 'mongodb://localhost:27017/testdatagen'
)
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET', 'change-me')
app.config['OPENAI_PRICE_MULTIPLIER'] = 3
app.config['OPENAI_API_KEY'] = 'YOUR_OPENAI_KEY'
app.config['STRIPE_SECRET_KEY'] = 'YOUR_STRIPE_SECRET_KEY'
app.config['ACCESS_TOKEN_EXPIRES_MINUTES'] = int(
    os.environ.get('ACCESS_TOKEN_EXPIRES_MINUTES', '60')
)
stripe.api_key = app.config['STRIPE_SECRET_KEY']

mongo_client = MongoClient(app.config['MONGO_URI'])
mongo_db = mongo_client.get_default_database()


def login_required(f):
    """Decorator to ensure the request has a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'missing token'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def create_app():
    mongo_db.users.create_index('username', unique=True)
    return app

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing parameters'}), 400
    if mongo_db.users.find_one({'username': username}):
        return jsonify({'error': 'user exists'}), 400
    user = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'wallet': 0.0
    }
    mongo_db.users.insert_one(user)
    return jsonify({'message': 'registered'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = mongo_db.users.find_one({'username': username})
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401
    access_exp = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=app.config['ACCESS_TOKEN_EXPIRES_MINUTES']
    )
    token = jwt.encode(
        {'user_id': str(user['_id']), 'exp': access_exp},
        app.config['SECRET_KEY'],
        algorithm='HS256',
    )
    refresh_token = jwt.encode(
        {
            'user_id': str(user['_id']),
            'type': 'refresh',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
        },
        app.config['SECRET_KEY'],
        algorithm='HS256',
    )
    return jsonify({'token': token, 'refresh_token': refresh_token})

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    # With JWTs there is no server-side session to invalidate
    return jsonify({'message': 'logged out'})


@app.route('/refresh', methods=['POST'])
def refresh():
    """Issue a new access token using a refresh token."""
    data = request.json or {}
    token = data.get('refresh_token')
    if not token:
        return jsonify({'error': 'missing refresh token'}), 400
    try:
        payload = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=['HS256'],
        )
        if payload.get('type') != 'refresh':
            raise jwt.InvalidTokenError('wrong token type')
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'invalid token'}), 401

    access_exp = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=app.config['ACCESS_TOKEN_EXPIRES_MINUTES']
    )
    new_token = jwt.encode(
        {'user_id': payload['user_id'], 'exp': access_exp},
        app.config['SECRET_KEY'],
        algorithm='HS256',
    )
    return jsonify({'token': new_token})

@app.route('/secret', methods=['POST'])
@login_required
def create_secret():
    new_key = secrets.token_hex(16)
    mongo_db.secret_keys.insert_one({'key': new_key, 'user_id': ObjectId(request.user_id)})
    return jsonify({'secret_key': new_key})

@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    data = request.json
    amount = data.get('amount')
    # Here we would use Stripe to handle payment intent; omitted for brevity
    user_id = ObjectId(request.user_id)
    mongo_db.users.update_one({'_id': user_id}, {'$inc': {'wallet': amount}})
    user = mongo_db.users.find_one({'_id': user_id})
    return jsonify({'wallet': user['wallet']})

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'missing prompt'}), 400
    user = mongo_db.users.find_one({'_id': ObjectId(request.user_id)})
    if user['wallet'] <= 0:
        return jsonify({'error': 'insufficient funds'}), 402
    openai.api_key = app.config['OPENAI_API_KEY']
    # Proxy settings could be configured via environment variables
    response = openai.Completion.create(model='text-davinci-003', prompt=prompt, max_tokens=10)
    usage = response['usage']
    cost = usage['total_tokens'] * 0.01  # Example price
    total = cost * app.config['OPENAI_PRICE_MULTIPLIER']
    mongo_db.users.update_one({'_id': ObjectId(request.user_id)}, {'$inc': {'wallet': -total}})
    mongo_db.usage.insert_one({
        'user_id': ObjectId(request.user_id),
        'prompt_tokens': usage['prompt_tokens'],
        'completion_tokens': usage['completion_tokens'],
        'cost': total
    })
    user = mongo_db.users.find_one({'_id': ObjectId(request.user_id)})
    return jsonify({
        'response': response['choices'][0]['text'],
        'usage': usage,
        'cost_charged': total,
        'wallet_balance': user['wallet']
    })

@app.route('/usage', methods=['GET'])
@login_required
def get_usage():
    usages = mongo_db.usage.find({'user_id': ObjectId(request.user_id)})
    result = []
    for u in usages:
        result.append({
            'prompt_tokens': u['prompt_tokens'],
            'completion_tokens': u['completion_tokens'],
            'cost': u['cost']
        })
    return jsonify({'usage': result})

if __name__ == '__main__':
    create_app().run(debug=True)

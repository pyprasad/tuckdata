from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import openai
import stripe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testdatagen.db'
app.config['SECRET_KEY'] = 'change-me'
app.config['OPENAI_PRICE_MULTIPLIER'] = 3
app.config['OPENAI_API_KEY'] = 'YOUR_OPENAI_KEY'
app.config['STRIPE_SECRET_KEY'] = 'YOUR_STRIPE_SECRET_KEY'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    wallet = db.Column(db.Float, default=0.0)

class SecretKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt_tokens = db.Column(db.Integer)
    completion_tokens = db.Column(db.Integer)
    cost = db.Column(db.Float)

def create_app():
    db.create_all()
    return app

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing parameters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'user exists'}), 400
    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'registered'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'invalid credentials'}), 401
    token = secrets.token_hex(16)
    SecretKey.query.filter_by(user_id=user.id).delete()
    secret = SecretKey(key=token, user_id=user.id)
    db.session.add(secret)
    db.session.commit()
    return jsonify({'token': token})

@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'missing token'}), 401
    key = SecretKey.query.filter_by(key=token).first()
    if key:
        db.session.delete(key)
        db.session.commit()
    return jsonify({'message': 'logged out'})

@app.route('/secret', methods=['POST'])
def create_secret():
    token = request.headers.get('Authorization')
    key = SecretKey.query.filter_by(key=token).first()
    if not key:
        return jsonify({'error': 'invalid token'}), 401
    new_key = SecretKey(key=secrets.token_hex(16), user_id=key.user_id)
    db.session.add(new_key)
    db.session.commit()
    return jsonify({'secret_key': new_key.key})

@app.route('/deposit', methods=['POST'])
def deposit():
    token = request.headers.get('Authorization')
    key = SecretKey.query.filter_by(key=token).first()
    if not key:
        return jsonify({'error': 'invalid token'}), 401
    data = request.json
    amount = data.get('amount')
    # Here we would use Stripe to handle payment intent; omitted for brevity
    user = User.query.get(key.user_id)
    user.wallet += amount
    db.session.commit()
    return jsonify({'wallet': user.wallet})

@app.route('/generate', methods=['POST'])
def generate():
    token = request.headers.get('Authorization')
    key = SecretKey.query.filter_by(key=token).first()
    if not key:
        return jsonify({'error': 'invalid token'}), 401
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'missing prompt'}), 400
    user = User.query.get(key.user_id)
    if user.wallet <= 0:
        return jsonify({'error': 'insufficient funds'}), 402
    openai.api_key = app.config['OPENAI_API_KEY']
    # Proxy settings could be configured via environment variables
    response = openai.Completion.create(model='text-davinci-003', prompt=prompt, max_tokens=10)
    usage = response['usage']
    cost = usage['total_tokens'] * 0.01  # Example price
    total = cost * app.config['OPENAI_PRICE_MULTIPLIER']
    user.wallet -= total
    db.session.add(Usage(user_id=user.id, prompt_tokens=usage['prompt_tokens'], completion_tokens=usage['completion_tokens'], cost=total))
    db.session.commit()
    return jsonify({
        'response': response['choices'][0]['text'],
        'usage': usage,
        'cost_charged': total,
        'wallet_balance': user.wallet
    })

@app.route('/usage', methods=['GET'])
def get_usage():
    token = request.headers.get('Authorization')
    key = SecretKey.query.filter_by(key=token).first()
    if not key:
        return jsonify({'error': 'invalid token'}), 401
    usages = Usage.query.filter_by(user_id=key.user_id).all()
    result = []
    for u in usages:
        result.append({'prompt_tokens': u.prompt_tokens, 'completion_tokens': u.completion_tokens, 'cost': u.cost})
    return jsonify({'usage': result})

if __name__ == '__main__':
    create_app().run(debug=True)

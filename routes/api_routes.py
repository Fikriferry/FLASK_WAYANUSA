from flask import Blueprint, jsonify, request
from models import db, User, Dalang
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

api = Blueprint("api", __name__)
auth_api = Blueprint("auth_api", __name__)

# DALANG API
@api.route('/dalang', methods=['GET'])
def get_dalang():
    dalangs = Dalang.query.all()
    return jsonify([{
        'id': d.id,
        'nama': d.nama,
        'alamat': d.alamat,
        'latitude': d.latitude,
        'longitude': d.longitude,
        'foto': d.foto
    } for d in dalangs])

# Auth API (email/password + JWT)
@auth_api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        token = create_access_token(identity=user.id)
        return jsonify({'access_token': token, 'user': {'id': user.id,'name': user.name,'email': user.email}}), 200
    return jsonify({'message':'Invalid credentials'}), 401

@auth_api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter_by(email=email).first():
        return jsonify({'message':'Email already exists'}), 400
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.id)
    return jsonify({'access_token': token,'user':{'id':user.id,'name':user.name,'email':user.email}}), 201

@auth_api.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 200
    return jsonify({'message':'User not found'}), 404
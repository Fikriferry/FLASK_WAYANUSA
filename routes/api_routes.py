from flask import Blueprint, jsonify, request
from models import db, User, Dalang
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ai_manager import get_model
import numpy as np
import io
from PIL import Image # Pastikan install: pip install Pillow

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

# PREDICTION API
@api.route('/predict-wayang', methods=['POST'])
def predict_wayang():
    # 1. Ambil model global
    model = get_model()
    
    if model is None:
        return jsonify({'error': 'Model AI belum diaktifkan oleh Admin!'}), 503

    # --- BAGIAN BARU: PENGECEKAN FILE ---
    if 'image' not in request.files:
        return jsonify({'error': 'Tidak ada file gambar yang diupload (key harus "image")'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'Nama file kosong'}), 400

    try:
        # --- BAGIAN PERBAIKAN: MEMBUAT 'processed_img' ---
        # Membaca gambar dari file upload
        image_bytes = file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB') # Pastikan mode RGB
        
        # PENTING: Ubah ukuran (224, 224) sesuai dengan input shape saat training model kamu!
        # Jika modelmu pakai 150x150, ganti jadi (150, 150)
        target_size = (150, 150) 
        img = img.resize(target_size)
        
        # Ubah ke array numpy & Normalisasi
        x = np.array(img)
        x = x / 255.0  # Normalisasi (biasanya 0-1)
        
        # Tambah dimensi batch (Model butuh input [1, 224, 224, 3])
        processed_img = np.expand_dims(x, axis=0)

        # --- PREDIKSI ---
        prediction = model.predict(processed_img)

        # --- BAGIAN PERBAIKAN: MEMBUAT 'result' ---
        # Contoh daftar nama kelas wayang (SESUAIKAN DENGAN URUTAN MODEL KAMU)
        class_names = [
            'Abimanyu', 'Anoman', 'Arjuna', 'Bagong', 'Baladewa', 
            'Bima', 'Buta', 'Cakil', 'Durna', 'Dursasana', 
            'Duryudana', 'Gareng', 'Gatotkaca', 'Karna', 'Kresna', 
            'Nakula Sadewa', 'Patih Sabrang', 'Petruk', 'Puntadewa', 'Semar', 
            'Sengkuni', 'Togog'
        ]
        
        # Ambil index dengan probabilitas tertinggi
        predicted_index = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction))
        
        predicted_label = class_names[predicted_index] if predicted_index < len(class_names) else "Unknown"

        # Definisikan variabel result agar return tidak error
        result = {
            'prediksi': predicted_label,
            'confidence': f"{confidence * 100:.2f}%",
            'raw_prediction': prediction.tolist() # Opsional untuk debug
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error prediction: {e}") # Print error di terminal agar kelihatan
        return jsonify({'error': str(e)}), 500
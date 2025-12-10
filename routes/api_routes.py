from flask import Blueprint, jsonify, request
from models import db, User, Dalang, Wayang, AIModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ai_manager import get_model
import numpy as np
import io
from PIL import Image
import google.generativeai as genai
from cepot_controller import cepot_system

# ================================
# KONFIGURASI BLUEPRINT & AI
# ================================
api = Blueprint("api", __name__)
auth_api = Blueprint("auth_api", __name__)

# --- KONFIGURASI GEMINI AI (CHATBOT) ---
# Ganti dengan API Key kamu yang valid
GEMINI_API_KEY = "AIzaSyDmUtu7mZVRVqp88QigLZOra3UUsPkUhJk" 
genai.configure(api_key=GEMINI_API_KEY)

# Inisialisasi Model Chat
chat_model = genai.GenerativeModel("gemini-2.5-flash")
chat_session = chat_model.start_chat(history=[])

# Prompt Kepribadian Cepot Tegal
SYSTEM_PROMPT = """
Instruksi: Kamu adalah Cepot, tokoh wayang golek yang lucu dengan dialek Tegal (Ngapak) yang kental.
Gunakan kata ganti 'Inyong' (Saya) dan 'Rika' atau 'Sampeyan' (Kamu).
Gaya bicara: Ceplas-ceplos, humoris, tapi tetap sopan, membantu, dan sedikit 'ngegas' yang lucu.
Jawablah pertanyaan user dengan singkat, padat, dan jelas (maksimal 3-4 kalimat).
"""

# ================================
# 1. AUTH API (LOGIN / REGISTER)
# ================================

@auth_api.route("/register", methods=["POST"])
def register():
    """Mendaftarkan user baru."""
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    new_user = User(name=name, email=email)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        token = create_access_token(identity=new_user.id)
        return jsonify({
            "access_token": token,
            "user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_api.route("/login", methods=["POST"])
def login():
    """Autentikasi user dan memberikan JWT Token."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        token = create_access_token(identity=user.id)
        return jsonify({
            "access_token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }), 200

    return jsonify({"message": "Invalid credentials"}), 401

@auth_api.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    """Mengambil profil user yang sedang login."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        return jsonify({"id": user.id, "name": user.name, "email": user.email}), 200
    return jsonify({"message": "User not found"}), 404

# ================================
# 2. DATA API (DALANG)
# ================================

@api.route("/dalang", methods=["GET"])
def get_dalang():
    """Mengambil semua data dalang dari database."""
    try:
        dalangs = Dalang.query.all()
        data = [{
            "id": d.id,
            "nama": d.nama,
            "alamat": d.alamat,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "foto": d.foto
        } for d in dalangs]
        return jsonify({"dalangs": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# 3. AI VISION API (PREDIKSI WAYANG)
# ================================

@api.route('/predict-wayang', methods=['POST'])
def predict_wayang():
    """
    Menerima gambar -> Resize -> Prediksi Model -> Ambil Info Database.
    """
    # 1. Cek Model Aktif
    active_model_db = AIModel.query.filter_by(is_active=True).first()
    if not active_model_db:
        return jsonify({'error': 'Belum ada model AI yang diaktifkan Admin.'}), 503
        
    model = get_model() # Load dari RAM
    if model is None:
        return jsonify({'error': 'Model gagal dimuat di server.'}), 500

    # 2. Validasi File
    if 'image' not in request.files:
        return jsonify({'error': 'File gambar tidak ditemukan'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nama file kosong'}), 400

    try:
        # 3. Pre-processing Gambar
        image_bytes = file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Resize sesuai input shape model (150x150)
        target_size = (150, 150) 
        img = img.resize(target_size)
        
        # Normalisasi Array
        x = np.array(img)
        x = x / 255.0  
        processed_img = np.expand_dims(x, axis=0)

        # 4. Prediksi
        prediction = model.predict(processed_img)
        predicted_index = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction))

        # 5. Mapping Label dari Database
        if active_model_db.labels:
            class_names = [label.strip() for label in active_model_db.labels.split(',')]
        else:
            return jsonify({'error': 'Model aktif tidak memiliki data label!'}), 500

        if predicted_index < len(class_names):
            predicted_label = class_names[predicted_index]
        else:
            predicted_label = "Unknown"

        # 6. Ambil Deskripsi dari Tabel Wayang
        deskripsi_text = "Deskripsi belum tersedia di database."
        if predicted_label != "Unknown":
            wayang_db = Wayang.query.filter_by(nama=predicted_label).first()
            if wayang_db:
                deskripsi_text = wayang_db.deskripsi

        return jsonify({
            'prediksi': predicted_label,
            'confidence': f"{confidence * 100:.2f}%",
            'deskripsi': deskripsi_text,
        }), 200

    except Exception as e:
        print(f"Error Vision: {e}")
        return jsonify({'error': 'Gagal memproses gambar', 'details': str(e)}), 500

# ================================
# 4. AI CHATBOT API (CEPOT)
# ================================

@api.route('/chat', methods=['POST'])
def chat_api():
    """
    Menerima pesan teks -> Kirim ke Gemini (dengan persona Cepot) -> Balas.
    """
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({'response': "Waduh, kok meneng bae? Ngomong apa kye?"}), 400

        # Gabungkan System Prompt dengan Pesan User
        final_prompt = f"{SYSTEM_PROMPT}\n\nUser bertanya: {user_message}"

        # Kirim ke Gemini
        response = chat_session.send_message(final_prompt)
        bot_reply = response.text

        # Bersihkan Markdown (* atau **) agar tampilan rapi
        bot_reply = bot_reply.replace("**", "").replace("*", "")

        return jsonify({'response': bot_reply}), 200

    except Exception as e:
        print(f"Error Chatbot: {e}")
        return jsonify({'response': "Waduh, sinyal inyong lagi laka (Error Server). Coba maning ya!"}), 500
    
# ================================
# 5. SMART WAYANG CONTROL API
# ================================

@api.route('/cepot/ports', methods=['GET'])
def get_ports():
    ports = cepot_system.get_ports()
    return jsonify({'ports': ports})

@api.route('/cepot/connect', methods=['POST'])
def connect_cepot():
    data = request.get_json()
    port = data.get('port')
    if not port:
        return jsonify({'status': 'error', 'message': 'Pilih port dulu!'})
    
    success, msg = cepot_system.connect(port)
    if success:
        return jsonify({'status': 'success', 'message': msg})
    else:
        return jsonify({'status': 'error', 'message': msg})

@api.route('/cepot/disconnect', methods=['POST'])
def disconnect_cepot():
    msg = cepot_system.disconnect()
    return jsonify({'status': 'success', 'message': msg})

@api.route('/cepot/talk', methods=['POST'])
def cepot_talk():
    # Endpoint ini dipanggil setelah Browser mendengar perintah suara
    data = request.get_json()
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'response': 'Hah? Ora krungu... (Pesan kosong)'})

    # Panggil Controller Fisik (Gemini + Gerak + Suara)
    reply = cepot_system.process_physical_interaction(user_message)
    
    return jsonify({'response': reply})
import os
from flask import Blueprint, jsonify, request, Flask
from models import db, User, Dalang, Wayang, AIModel, Video
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from ai_manager import get_model
import numpy as np
import io
from PIL import Image
import google.generativeai as genai
from cepot_controller import cepot_system
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import func
from services.rag_service import rag_service
import re # Import Regex untuk parsing link Youtube

# ================================
# KONFIGURASI BLUEPRINT
# ================================
api = Blueprint("api", __name__, url_prefix="/api")
auth_api = Blueprint("auth_api", __name__, url_prefix="/api/auth")

# ================================
# GEMINI CONFIG
# ================================
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY tidak ditemukan")

genai.configure(api_key=GEMINI_API_KEY)
chat_model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM_PROMPT = """
Instruksi: Kamu adalah Cepot, tokoh wayang golek lucu dengan dialek Tegal (Ngapak).
Gunakan kata 'Inyong' dan 'Rika' / 'Sampeyan'.
Jawaban singkat, lucu, sopan, maksimal 3-4 kalimat.
"""

# ================================
# AUTH API
# ================================
@auth_api.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email sudah terdaftar"}), 400

    user = User(name=data["name"], email=data["email"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }), 201


@auth_api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "Login gagal"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email}
    })


@auth_api.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)


    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 200



# ================================
# DATA API
# ================================
@api.route("/dalang", methods=["GET"])
def get_dalang():
    dalangs = Dalang.query.all()
    return jsonify({
        "data": [{
            "id": d.id,
            "nama": d.nama,
            "alamat": d.alamat,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "foto": d.foto
        } for d in dalangs]
    })


@api.route("/wayang", methods=["GET"])
def get_wayang():
    wayangs = Wayang.query.all()
    return jsonify({
        "data": [{
            "id": w.id,
            "nama": w.nama,
            "file": w.file_path
        } for w in wayangs]
    })


# ================================
# AI VISION
# ================================
@api.route("/predict-wayang", methods=["POST"])
def predict_wayang():
    print("PREDICT CALLED")
    active_model = AIModel.query.filter_by(is_active=True).first()
    if not active_model:
        return jsonify({"error": "Model AI belum diaktifkan"}), 503

    model = get_model()
    if model is None:
        return jsonify({"error": "Model gagal dimuat"}), 500

    if "image" not in request.files:
        return jsonify({"error": "File tidak ditemukan"}), 400

    img = Image.open(io.BytesIO(request.files["image"].read())).convert("RGB")
    img = img.resize((150, 150))
    x = np.expand_dims(np.array(img) / 255.0, axis=0)

    prediction = model.predict(x)
    idx = int(np.argmax(prediction))
    confidence = float(np.max(prediction))

    labels = [l.strip() for l in active_model.labels.split(",")]
    
    # === SOLUSI: LOGIC THRESHOLD ===
    # Jika confidence di bawah 70%, anggap bukan wayang
    THRESHOLD = 0.75
    
    if confidence < THRESHOLD:
        return jsonify({
            "prediksi": "Objek Tidak Dikenali",
            "confidence": f"{confidence*100:.2f}% (Terlalu Rendah)",
            "deskripsi": "Maaf, sistem tidak yakin ini gambar wayang. Pastikan foto wayang terlihat jelas, pencahayaan cukup, dan background tidak terlalu ramai."
        })

    # Jika lolos threshold, baru ambil data dari DB
    label = labels[idx] if idx < len(labels) else "Unknown"
    wayang = Wayang.query.filter(func.lower(Wayang.nama) == func.lower(label)).first()

    return jsonify({
        "prediksi": label,
        "confidence": f"{confidence*100:.2f}%",
        "deskripsi": wayang.deskripsi if wayang else "Deskripsi belum tersedia."
    })


# ================================
# CHATBOT CEPOT (FIXED)
# ================================
@api.route("/chat", methods=["POST"])
@jwt_required(optional=True)
def chat_api():
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"response": "Waduh, kok meneng bae?"}), 400

    # 🔥 SESSION BARU (AMAN MULTI USER)
    chat = chat_model.start_chat(history=[])
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {message}"

    response = chat.send_message(prompt)
    reply = response.text.replace("*", "")

    return jsonify({"response": reply})

# --- API 1: Build Database (Jalankan ini dulu via Postman/Browser) ---
@api.route("/rag/build", methods=["GET"])
def build_rag():
    try:
        rag_service.build_index()
        return jsonify({"message": "Database Wayang berhasil dibangun!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API 2: Chatbot Versi 2 (RAG) ---
@api.route("/chat-rag", methods=["POST"])
# @jwt_required(optional=True) # Aktifkan jwt jika perlu
def chat_rag_api():
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"response": "Waduh, kok meneng bae?"}), 400

    try:
        # Panggil fungsi RAG
        reply = rag_service.get_answer(message)
        return jsonify({"response": reply})
    except Exception as e:
        print(e)
        return jsonify({"response": "Maaf, Ki Sabda sedang pusing (Error Server)."}), 500


# ================================
# SMART WAYANG (SIAP ADMIN)
# ================================
@api.route("/cepot/ports")
def cepot_ports():
    return jsonify({"ports": cepot_system.get_ports()})


@api.route("/cepot/connect", methods=["POST"])
def cepot_connect():
    port = request.json.get("port")
    success, msg = cepot_system.connect(port)
    return jsonify({"success": success, "message": msg})


@api.route("/cepot/disconnect", methods=["POST"])
def cepot_disconnect():
    return jsonify({"message": cepot_system.disconnect()})


@api.route("/cepot/talk", methods=["POST"])
def cepot_talk():
    msg = request.json.get("message")
    if not msg:
        return jsonify({"response": "Ora krungu..."})

    reply = cepot_system.process_physical_interaction(msg)
    return jsonify({"response": reply})

# ================================
# VIDEO WAYANG
# ================================

# --- HELPER: Fungsi Ekstrak ID Youtube ---
def extract_youtube_id(url):
    """
    Mengambil ID unik (misal: J_t9G2bWqYA) dari link Youtube panjang/pendek.
    """
    if not url: return None
    # Regex untuk menangani berbagai format link youtube
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

# 1. GET ALL VIDEOS (Untuk ditampilkan di Flutter)
@api.route('/videos', methods=['GET'])
def get_videos():
    try:
        videos = db.session.query(Video).order_by(Video.id.desc()).all()
        output = []
        
        for vid in videos:
            video_id = extract_youtube_id(vid.youtube_link)
            
            # Kita format datanya biar Flutter tinggal pakai
            video_data = {
                'id': vid.id,
                'title': vid.judul,
                'youtube_link': vid.youtube_link,
                'youtube_id': video_id, # ID ini penting buat player Flutter
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/0.jpg" if video_id else None,
                'channel': "Wayanusa Official" # Default channel name (karena di DB ga ada kolom channel)
            }
            output.append(video_data)

        return jsonify({
            'status': 'success', 
            'total': len(output),
            'data': output
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
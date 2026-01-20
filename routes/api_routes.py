import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask import Blueprint, jsonify, request, Flask, url_for
from models import db, User, Dalang, Wayang, AIModel, Video, Article
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
# from services.rag_service import rag_service
try:
    from services.rag_service import rag_service
except Exception as e:
    rag_service = None
    print("⚠️ RAG Service dimatikan sementara:", e)
import re # Import Regex untuk parsing link Youtube
from werkzeug.utils import secure_filename
import uuid
from langchain_core.messages import HumanMessage, SystemMessage

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
Instruksi: Kamu adalah Asisten Pintar bernama "Cepot" yang ahli tentang budaya Wayang.
        Jawab pertanyaan berdasarkan konteks berikut ini. Jika jawaban di luar konteks wayang,
        katakan "Maaf, Cepot tidak bisa menjawab karena pertanyaan di luar konteks wayang.
"""

# ================================
# BLUEPRINT DEFINITIONS (WAJIB)
# ================================
api = Blueprint("api", __name__)
auth_api = Blueprint("auth_api", __name__)


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

@auth_api.route("/google/android", methods=["POST"])
def google_login_android():
    data = request.get_json()
    token = data.get("id_token")

    try:
        # Load client_id from environment variable and parse JSON
        client_config = json.loads(os.getenv("GOOGLE_CLIENT_ID_ANDROID"))
        client_id = client_config["installed"]["client_id"]

        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            client_id
        )

        email = idinfo["email"]
        name = idinfo.get("name")
        google_id = idinfo["sub"]

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                password_hash="-"
            )
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(identity=user.id)

        return jsonify({
            "success": True,
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 401


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
# CHATBOT CEPOT (SAFE MODE)
# ================================
@api.route('/chat-smart', methods=['POST'])
def chat_smart():
    if rag_service is None:
        return jsonify({
            "response": "🤖 Fitur chatbot sedang dinonaktifkan sementara."
        }), 503

    data = request.get_json()
    message = data.get("message")
    mode = data.get("mode", "rag")

    if not message:
        return jsonify({"response": "Waduh, kok meneng bae? (Pesan kosong)"}), 400

    try:
        if mode == 'gemini':
            from langchain.schema import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=message)
            ]

            ai_response = rag_service.llm.invoke(messages)
            reply_text = ai_response.content
        else:
            reply_text = rag_service.get_answer(message)

        clean_reply = reply_text.replace("*", "")
        return jsonify({"response": clean_reply})

    except Exception as e:
        print(f"Error Chat Smart: {e}")
        return jsonify({"response": "Cepot lagi pusing euy 😵"}), 500


@api.route("/rag/build", methods=["GET"])
def build_rag():
    return jsonify({
        "message": "Fitur RAG sedang dinonaktifkan sementara."
    }), 503

@api.route("/chat-rag", methods=["POST"])
def chat_rag_api():
    return jsonify({
        "response": "Fitur AI sedang nonaktif."
    }), 503



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

# ==========================================
# HELPER: SAVE THUMBNAIL (API VERSION)
# ==========================================
def save_thumbnail_api(file):
    """
    Simpan file gambar dari request API ke folder static.
    Mengembalikan nama file unik atau None jika gagal.
    """
    if not file or file.filename == '':
        return None
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Cek ekstensi
    if '.' not in file.filename or \
       file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return None

    # Buat nama file unik (UUID + Secure Filename)
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Path folder upload (Absolute Path lebih aman)
    # Sesuaikan base_dir dengan lokasi app.py kamu
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    upload_folder = os.path.join(base_dir, 'static', 'uploads', 'thumbnails')
    
    os.makedirs(upload_folder, exist_ok=True)
    
    # Simpan File
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return unique_filename

# ==========================================
# API ENDPOINTS: ARTIKEL
# ==========================================

# 1. GET ALL ARTICLES (List Berita)
@api.route('/articles', methods=['GET'])
def get_articles():
    try:
        # Urutkan artikel terbaru paling atas
        articles = Article.query.order_by(Article.created_at.desc()).all()
        output = []

        for art in articles:
            # Generate URL Gambar Lengkap (http://ip-server:port/static/...)
            thumbnail_url = None
            if art.thumbnail:
                # request.host_url otomatis mendeteksi IP/Domain server
                thumbnail_url = f"{request.host_url}static/uploads/thumbnails/{art.thumbnail}"
            else:
                # Gambar Default jika tidak ada thumbnail
                thumbnail_url = "https://via.placeholder.com/300x200?text=No+Image"

            # Bersihkan tag HTML dari content untuk preview (misal dari Summernote)
            import re
            clean_text = re.sub('<[^<]+?>', '', art.content or '')

            data = {
                'id': art.id,
                'title': art.title,
                'content_preview': clean_text[:100] + '...' if len(clean_text) > 100 else clean_text,
                'source_link': art.source_link,
                'thumbnail': thumbnail_url,
                'created_at': art.created_at.strftime('%d %B %Y'), # Contoh: 10 Januari 2026
                'created_at_iso': art.created_at.isoformat() # Format ISO untuk parsing di Flutter
            }
            output.append(data)

        return jsonify({
            'status': 'success',
            'total': len(output),
            'data': output
        }), 200

    except Exception as e:
        print(f"Error Get Articles: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# 2. GET SINGLE ARTICLE (Detail Berita)
@api.route('/articles/<int:id>', methods=['GET'])
def get_article_detail(id):
    try:
        art = Article.query.get(id)
        if not art:
            return jsonify({'status': 'error', 'message': 'Artikel tidak ditemukan'}), 404

        thumbnail_url = None
        if art.thumbnail:
            thumbnail_url = f"{request.host_url}static/uploads/thumbnails/{art.thumbnail}"
        else:
            thumbnail_url = "https://via.placeholder.com/600x400?text=No+Image"

        data = {
            'id': art.id,
            'title': art.title,
            'content': art.content, # Kirim HTML mentah biar Flutter render pake WebView/HtmlWidget
            'source_link': art.source_link,
            'thumbnail': thumbnail_url,
            'created_at': art.created_at.strftime('%d %B %Y, %H:%M WIB')
        }

        return jsonify({'status': 'success', 'data': data}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# 3. CREATE ARTICLE (Tambah Berita via API)
@api.route('/articles', methods=['POST'])
def create_article():
    try:
        # Ambil data form-data
        title = request.form.get('title')
        content = request.form.get('content')
        source_link = request.form.get('source_link')
        file = request.files.get('thumbnail') # Key di postman/flutter: 'thumbnail'

        # Validasi Input
        if not title or not content:
            return jsonify({'status': 'error', 'message': 'Judul dan Konten wajib diisi!'}), 400

        # Upload Gambar (Opsional)
        thumbnail_filename = None
        if file:
            thumbnail_filename = save_thumbnail_api(file)
            if not thumbnail_filename:
                return jsonify({'status': 'error', 'message': 'Format gambar tidak didukung!'}), 400

        # Simpan ke Database
        new_article = Article(
            title=title,
            content=content,
            source_link=source_link,
            thumbnail=thumbnail_filename
        )

        db.session.add(new_article)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Artikel berhasil diterbitkan!',
            'data': {
                'id': new_article.id,
                'title': new_article.title,
                'thumbnail': thumbnail_filename
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error Create Article: {e}")
        return jsonify({'status': 'error', 'message': "Gagal menyimpan artikel."}), 500


# 4. DELETE ARTICLE (Hapus Berita)
@api.route('/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    try:
        art = Article.query.get(id)
        if not art:
            return jsonify({'status': 'error', 'message': 'Artikel tidak ditemukan'}), 404

        # Hapus File Gambar Fisik (Bersih-bersih storage)
        if art.thumbnail:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, 'static', 'uploads', 'thumbnails', art.thumbnail)
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass # Abaikan jika gagal hapus file, yg penting data db hilang

        db.session.delete(art)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Artikel berhasil dihapus permanen'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
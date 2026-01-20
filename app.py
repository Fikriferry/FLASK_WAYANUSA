from flask import Flask
from models import db
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from ai_manager import init_ai_model

# Routes
# Pastikan file-file ini ada di folder 'routes'
from routes.web_routes import web_routes
from routes.api_routes import api, auth_api
from routes.auth_routes import auth_routes, init_oauth
from routes.quiz_routes import quiz_routes
from routes.leaderboard_wayang_routes import leaderboard_wayang_bp

# ================================ #
#          LOAD ENV FILE           #
# ================================ #
load_dotenv()

app = Flask(__name__)

# ================================ #
#             CONFIG               #
# ================================ #
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "rahasia_default_kalau_env_kosong") # Tambah fallback biar ga error
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# JWT Secret
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt_secret_fallback")

# CORS
# Izinkan akses dari semua asal (*) untuk endpoint API
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# JWT
jwt = JWTManager(app)

# Init OAuth Google
init_oauth(app)

# Init DB
db.init_app(app)

# Ensure upload dir exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ================================ #
#       REGISTER BLUEPRINTS        #
# ================================ #

app.register_blueprint(web_routes)

# 🔥 PERBAIKAN DISINI: 
# Hapus url_prefix karena di dalam file api_routes.py SUDAH ADA url_prefix="/api"
# Jika dipasang dua-duanya, url jadinya: /api/api/wayang-game (Dobel!)
app.register_blueprint(api) 

# Sama juga untuk auth_api, hapus prefix disini kalau di file aslinya sudah ada
app.register_blueprint(auth_api) 

app.register_blueprint(auth_routes)
app.register_blueprint(quiz_routes, url_prefix="/api/quiz") # Kalau di file quiz_routes BELUM ada prefix, biarkan ini.
app.register_blueprint(leaderboard_wayang_bp)

# ================================ #
#             RUN APP              #
# ================================ #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # Inisialisasi AI
    # Pastikan model AI ada, atau handle error di dalam init_ai_model
    try:
        init_ai_model(app)
    except Exception as e:
        print(f"⚠️ Warning: Gagal load AI Model: {e}")
    
    print("🚀 Menjalankan Server di Port 8000...")
    # Host 0.0.0.0 penting agar bisa diakses dari luar (Ngrok/HP)
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)
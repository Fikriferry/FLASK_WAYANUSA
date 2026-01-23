import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Import Models
from models import db, User 
from ai_manager import init_ai_model

# Import Blueprints
from routes.web_routes import web_routes as web_bp 
from routes.api_routes import api, auth_api
from routes.auth_routes import auth_routes, init_oauth
from routes.quiz_routes import quiz_routes
from routes.leaderboard_wayang_routes import leaderboard_wayang_bp

# 1. LOAD ENV
load_dotenv()

app = Flask(__name__)

# 2. CONFIG
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "rahasia_super_aman")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOTO'] = 'static/uploads/profile_pics'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt_fallback")

# Config Sesi (Penting biar gak logout sendiri)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 3600 * 24 * 7

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOTO'], exist_ok=True)

# 3. INIT EXTENSIONS (Urutan Sangat Penting!)
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)
init_oauth(app)

# 🔥🔥 BAGIAN INI YANG MEMPERBAIKI ERROR KAMU 🔥🔥
login_manager = LoginManager()
login_manager.init_app(app)

# Pastikan nama fungsi login sesuai dengan yang ada di web_routes.py
# Kalau di web_routes namanya 'def login_user_route', pakai ini:
login_manager.login_view = 'web.login_user_route' 
login_manager.login_message = "Silakan login dulu."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# 🔥🔥 END FIX 🔥🔥

# 4. REGISTER BLUEPRINTS
app.register_blueprint(web_bp) 
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(auth_api, url_prefix='/api/auth')
app.register_blueprint(auth_routes)
app.register_blueprint(quiz_routes, url_prefix="/api/quiz")
app.register_blueprint(leaderboard_wayang_bp)

# 5. RUN SERVER
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    try:
        init_ai_model(app)
    except Exception as e:
        print(f"⚠️ Warning AI: {e}")

    print("🚀 Server Jalan di Port 8000...")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)
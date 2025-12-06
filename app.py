from flask import Flask
from models import db
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from ai_manager import init_ai_model # Import AI Model Manager

# Routes
from routes.web_routes import web_routes
from routes.api_routes import api, auth_api
from routes.auth_routes import auth_routes, init_oauth  # Authlib Google OAuth

# ================================ #
#          LOAD ENV FILE           #
# ================================ #
load_dotenv()

app = Flask(__name__)

# ================================ #
#             CONFIG               #
# ================================ #
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# JWT SECRET
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
# JWT
jwt = JWTManager(app)

# Init OAuth (Google OAuth pakai env juga)
init_oauth(app)

# Init DB
db.init_app(app)
with app.app_context():
    db.create_all()  # Ini akan membuat semua tabel (User, Dalang, AIModel) jika belum ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_ai_model(app)

# ================================ #
#       REGISTER BLUEPRINTS        #
# ================================ #
app.register_blueprint(web_routes)
app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(auth_api, url_prefix="/api/auth")
app.register_blueprint(auth_routes)  # Google OAuth

# ================================ #
#             RUN APP              #
# ================================ #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)

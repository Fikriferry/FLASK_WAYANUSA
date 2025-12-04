from flask import Flask
from models import db
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Routes
from routes.web_routes import web_routes
from routes.api_routes import api, auth_api
from routes.auth_routes import auth_routes, init_oauth  # Authlib Google OAuth

app = Flask(__name__)

# ================================ #
#             CONFIG               #
# ================================ #
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_admin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# JWT SECRET
app.config["JWT_SECRET_KEY"] = "ganti_dengan_key_yang_aman"
jwt = JWTManager(app)

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Init OAuth
init_oauth(app)

# Init DB
db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

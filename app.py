from flask import Flask
from models import db
import os
from flask_cors import CORS   # <-- TAMBAHKAN INI

# Import blueprints
from routes.web_routes import web_routes
from routes.api_routes import api_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_admin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Aktifkan CORS untuk Flutter Web
CORS(app, resources={r"/api/*": {"origins": "*"}})  # <-- WAJIB UNTUK FLUTTER WEB

# Init database
db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(web_routes)
app.register_blueprint(api_routes, url_prefix="/api")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
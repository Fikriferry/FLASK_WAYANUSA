from flask import Blueprint, redirect, url_for, session, flash
from authlib.integrations.flask_client import OAuth
from models import db, User
import os

auth_routes = Blueprint("auth_routes", __name__)

oauth = OAuth()
google = None

def init_oauth(app):
    """
    Inisialisasi OAuth Google
    """
    global google
    oauth.init_app(app)

    google = oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v2/",
        client_kwargs={"scope": "openid email profile"},
        jwks_uri='https://www.googleapis.com/oauth2/v3/certs'
    )

@auth_routes.route("/login/google")
def login_google():
    """
    Redirect ke halaman login Google
    """
    redirect_uri = url_for("auth_routes.authorized_google", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_routes.route("/login/google/authorized")
def authorized_google():
    """
    Callback setelah login Google berhasil
    """
    try:
        token = google.authorize_access_token()
        resp = google.get("userinfo")
        user_info = resp.json()

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            flash("Email tidak ditemukan!", "error")
            return redirect(url_for("web.login_user"))

        # Cek apakah user sudah ada
        user = User.query.filter_by(email=email).first()
        if not user:
            # Buat user baru jika belum ada
            user = User(name=name, email=email, password_hash="-")
            db.session.add(user)
            db.session.commit()

        # Set session
        session["user_logged_in"] = True
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        flash("Login Google berhasil!", "success")
        return redirect(url_for("web.home"))

    except Exception as e:
        flash(f"Login Google gagal: {str(e)}", "error")
        return redirect(url_for("web.login_user"))

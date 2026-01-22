from flask import Blueprint, redirect, url_for, session, flash
from authlib.integrations.flask_client import OAuth
from models import db, User
import os

auth_routes = Blueprint("auth_routes", __name__)

oauth = OAuth()
google = None

def init_oauth(app):
    """
    Inisialisasi OAuth Google (WEB)
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
        client_kwargs={
            "scope": "openid email profile",
            "device_id": "flask-wayanusa-app",
            "device_name": "Flask Wayanusa Development Server"
        },
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs"
    )



@auth_routes.route("/login/google")
def login_google():
    from flask import request, session
    scheme = request.scheme
    host = request.host

    # Store the original host for redirect after authorization
    session['original_host'] = host

    # Use the host the user is accessing from as redirect URI for localhost/127.0.0.1
    if host.startswith('127.0.0.1') or host.startswith('localhost'):
        redirect_uri = f"{scheme}://{host}/login/google/authorized"
    else:
        # For other IPs, use localhost (though Google blocks private IPs anyway)
        redirect_uri = "https://monoclinic-superboldly-tobi.ngrok-free.dev/login/google/authorized"

    print(f"DEBUG: Host accessed: {host}, Redirect URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)


@auth_routes.route("/login/google/authorized")
def authorized_google():
    try:
        token = google.authorize_access_token()
        resp = google.get("userinfo")
        user_info = resp.json()

        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("id")  # boleh, aman untuk WEB

        if not email:
            flash("Email tidak ditemukan!", "error")
            return redirect(url_for("web.login_user"))

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

        session["user_logged_in"] = True
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        flash("Login Google berhasil!", "success")

        # Redirect back to the original host the user came from
        original_host = session.get('original_host', '127.0.0.1:8000')
        if original_host.startswith('127.0.0.1') or original_host.startswith('localhost'):
            return redirect(url_for("web.home"))
        else:
            # For other IPs, construct the URL manually
            return redirect(f"http://{original_host}/")

    except Exception as e:
        print("Google OAuth Error:", e)
        flash("Login Google gagal", "error")
        return redirect(url_for("web.login_user"))

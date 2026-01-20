from flask import Blueprint, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token
from models import db, User
import os
import json

auth_api = Blueprint("auth_api", __name__)

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
            requests.Request(),
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

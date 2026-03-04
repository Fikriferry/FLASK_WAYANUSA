from flask import Blueprint, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token
from models import db, User
import os
import json

auth_api = Blueprint("auth_api", __name__)


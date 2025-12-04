from flask import Blueprint, jsonify, url_for, request
from models import db, Dalang
import os
from werkzeug.utils import secure_filename

api_routes = Blueprint("api", __name__)

UPLOAD_FOLDER = "static/uploads"


def get_foto_url(filename):
    if filename:
        return url_for('web.uploaded_file', filename=filename, _external=True)
    return None


# GET ALL
@api_routes.route('/dalang', methods=['GET'])
def api_get_all_dalang():
    dalangs = Dalang.query.all()
    result = []
    for d in dalangs:
        result.append({
            "id": d.id,
            "nama": d.nama,
            "alamat": d.alamat,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "foto_url": get_foto_url(d.foto)
        })
    return jsonify(result)


# GET ONE
@api_routes.route('/dalang/<int:id>', methods=['GET'])
def api_get_one_dalang(id):
    d = Dalang.query.get_or_404(id)
    return jsonify({
        "id": d.id,
        "nama": d.nama,
        "alamat": d.alamat,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "foto_url": get_foto_url(d.foto)
    })

# CREATE (POST)
@api_routes.route('/dalang/create', methods=['POST'])
def api_create_dalang():

    # --- Ambil data dari JSON atau form-data ---
    if request.is_json:
        data = request.get_json()
        file = None  # JSON tidak bisa upload file
    else:
        data = request.form
        file = request.files.get('foto')

    # --- Validasi wajib ---
    nama = data.get("nama")
    if not nama:
        return jsonify({"error": "Nama wajib diisi"}), 400

    # --- Default filename ---
    filename = None

    # --- Simpan foto jika form-data dan ada file ---
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    # --- Buat object baru ---
    new_dalang = Dalang(
        nama=data.get("nama"),
        alamat=data.get("alamat"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        foto=filename
    )

    db.session.add(new_dalang)
    db.session.commit()

    return jsonify({
        "message": "Data dalang berhasil ditambahkan",
        "id": new_dalang.id
    }), 201


# UPDATE (PUT)
@api_routes.route('/dalang/update/<int:id>', methods=['PUT'])
def api_update_dalang(id):
    dalang = Dalang.query.get_or_404(id)

    nama = request.form.get("nama")
    alamat = request.form.get("alamat")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    # Validasi sama seperti di web
    if not nama or not alamat:
        return jsonify({"error": "Nama dan alamat wajib diisi"}), 400

    # Update foto jika ada
    if 'foto' in request.files:
        file = request.files['foto']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            dalang.foto = filename

    # Update data lain
    dalang.nama = nama
    dalang.alamat = alamat
    dalang.latitude = latitude
    dalang.longitude = longitude

    db.session.commit()

    return jsonify({
        "message": "Data dalang berhasil diupdate",
        "id": dalang.id
    }), 200

# DELETE
@api_routes.route('/dalang/delete/<int:id>', methods=['DELETE'])
def api_delete_dalang(id):
    dalang = Dalang.query.get(id)
    if not dalang:
        return jsonify({"error": "Data tidak ditemukan"}), 404

    # Hapus foto jika ada
    if dalang.foto:
        foto_path = os.path.join(UPLOAD_FOLDER, dalang.foto)
        if os.path.exists(foto_path):
            os.remove(foto_path)

    db.session.delete(dalang)
    db.session.commit()

    return jsonify({
        "message": "Data dalang berhasil dihapus"
    }), 200
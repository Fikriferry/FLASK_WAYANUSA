from flask import Blueprint, jsonify, url_for
from models import Dalang

api_routes = Blueprint("api", __name__)

def get_foto_url(filename):
    if filename:
        return url_for('web.uploaded_file', filename=filename, _external=True)
    return None


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
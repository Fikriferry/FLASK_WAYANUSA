# ai_manager.py
import os
from tensorflow.keras.models import load_model
from models import AIModel

# Variabel global untuk menyimpan model yang sedang jalan
_current_model = None

def init_ai_model(app):
    """Dipanggil saat aplikasi start (di app.py)"""
    global _current_model
    with app.app_context():
        # Cari model yang aktif di database
        active_data = AIModel.query.filter_by(is_active=True).first()
        
        if active_data and os.path.exists(active_data.file_path):
            print(f"[AI MANAGER] Memuat model aktif: {active_data.version_name}")
            _current_model = load_model(active_data.file_path)
        else:
            print("[AI MANAGER] Belum ada model aktif atau file tidak ditemukan.")

def reload_model(model_id):
    """Dipanggil saat Admin mengganti model"""
    global _current_model
    
    model_entry = AIModel.query.get(model_id)
    if model_entry and os.path.exists(model_entry.file_path):
        print(f"[AI MANAGER] Mengganti model ke: {model_entry.version_name}")
        # Load model baru ke memori menggantikan yang lama
        _current_model = load_model(model_entry.file_path)
        return True
    return False

def get_model():
    """Dipanggil oleh route prediksi untuk mendapatkan model"""
    return _current_model
# ai_manager.py
import os
import tensorflow as tf
from tensorflow.keras.models import load_model # <--- GUNAKAN INI (Standard)
# JANGAN PAKAI: from tf_keras.models import load_model (Ini untuk model jadul .h5)

from models import AIModel

# Variabel global
_current_model = None

def init_ai_model(app):
    """Dipanggil saat aplikasi start (di app.py)"""
    global _current_model
    
    try:
        with app.app_context():
            active_data = AIModel.query.filter_by(is_active=True).first()
            
            if active_data and os.path.exists(active_data.file_path):
                print(f"✅ [AI MANAGER] Memuat model: {active_data.version_name}")
                
                # Load model .keras
                # compile=False membuat load lebih cepat (karena kita cuma butuh predict)
                _current_model = load_model(active_data.file_path, compile=False)
                
                print("✅ [AI MANAGER] Model .keras berhasil dimuat.")
            else:
                print("⚠️ [AI MANAGER] Tidak ada model aktif atau file hilang.")
                
    except Exception as e:
        print(f"❌ [AI MANAGER] Error fatal saat load model: {e}")

def reload_model(model_id):
    """Dipanggil saat Admin mengganti model"""
    global _current_model
    try:
        model_entry = AIModel.query.get(model_id)
        if model_entry and os.path.exists(model_entry.file_path):
            print(f"🔄 [AI MANAGER] Mengganti model ke: {model_entry.version_name}")
            
            # Load model baru
            new_model = load_model(model_entry.file_path, compile=False)
            
            _current_model = new_model
            return True
            
    except Exception as e:
        print(f"❌ [AI MANAGER] Gagal reload model: {e}")
        
    return False

def get_model():
    return _current_model
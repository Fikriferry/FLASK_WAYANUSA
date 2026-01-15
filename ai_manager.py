import os
import sys
import logging
from flask import current_app

# =========================================================
# 1. KONFIGURASI MEMBUNGKAM TENSORFLOW (WAJIB PALING ATAS)
# =========================================================
# Level 3 berarti: Sembunyikan INFO, WARNING, dan ERROR (Hanya Fatal)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from tensorflow.keras.models import load_model
from models import AIModel

# Bungkam logger internal Python milik TensorFlow
tf.get_logger().setLevel(logging.ERROR)

# Variabel global
_current_model = None

# =========================================================
# 2. FUNGSI BANTUAN (HELPER)
# =========================================================

def get_absolute_path(relative_path):
    """
    Mengubah path relative (static/...) menjadi path absolut laptop/server.
    Ini memperbaiki masalah "File Tidak Ditemukan".
    """
    try:
        # Jika dijalankan dalam Flask Context
        base_path = current_app.root_path
        return os.path.join(base_path, relative_path)
    except:
        # Jika dijalankan manual
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, relative_path)

def _silence_load_model(file_path):
    """
    JURUS PAMUNGKAS: Memuat model sambil menutup mulut terminal.
    Output JSON panjang akan dibuang ke 'tong sampah' (devnull).
    """
    global _current_model
    
    # Simpan 'suara' terminal yang asli
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        # Buka saluran ke 'ketiadaan'
        devnull = open(os.devnull, 'w')
        
        # Alihkan semua output ke sana
        sys.stdout = devnull
        sys.stderr = devnull
        
        # PROSES BERAT DI SINI (Load Model)
        _current_model = load_model(file_path, compile=False)
        
        return True
    except Exception as e:
        # Jika error, kembalikan suara dulu baru teriak
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print(f"❌ [AI MANAGER] Gagal Load Keras: {e}")
        return False
    finally:
        # PENTING: Kembalikan suara terminal seperti semula
        if sys.stdout != original_stdout:
            sys.stdout = original_stdout
        if sys.stderr != original_stderr:
            sys.stderr = original_stderr
        try:
            devnull.close()
        except:
            pass

# =========================================================
# 3. FUNGSI UTAMA (INIT & RELOAD)
# =========================================================

def init_ai_model(app):
    """Dipanggil sekali saat server nyala"""
    global _current_model
    try:
        with app.app_context():
            active_data = AIModel.query.filter_by(is_active=True).first()
            
            if active_data:
                # Gunakan path absolut biar aman
                full_path = get_absolute_path(active_data.file_path)
                
                if os.path.exists(full_path):
                    print(f"✅ [AI MANAGER] Startup: {active_data.version_name}")
                    _silence_load_model(full_path)
                else:
                    print(f"⚠️ [AI MANAGER] File hilang di: {full_path}")
            else:
                print("ℹ️ [AI MANAGER] Belum ada model aktif.")
                
    except Exception as e:
        print(f"❌ [AI MANAGER] Error Startup: {e}")

def reload_model(model_id):
    """Dipanggil saat tombol 'Gunakan' diklik"""
    global _current_model
    try:
        model_entry = AIModel.query.get(model_id)
        if not model_entry:
            return False

        # Cari file dengan path absolut
        full_path = get_absolute_path(model_entry.file_path)
        
        print(f"🔍 [AI MANAGER] Mencari file...")

        if os.path.exists(full_path):
            print(f"🔄 [AI MANAGER] Loading model: {model_entry.version_name} (Mode Hening)")
            
            # Load dengan mode senyap
            success = _silence_load_model(full_path)
            
            if success:
                print("✅ [AI MANAGER] Berhasil Aktif!")
                return True
            else:
                return False
        else:
            print(f"❌ [AI MANAGER] GAGAL: File tidak ada di {full_path}")
            return False
            
    except Exception as e:
        print(f"❌ [AI MANAGER] Error Fatal: {e}")
        return False

def get_model():
    return _current_model
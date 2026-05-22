import os
import time
import serial
import asyncio
import threading
import pygame
import edge_tts
import google.generativeai as genai
import re
import serial.tools.list_ports
from dotenv import load_dotenv

# Load env variables immediately
load_dotenv()

# ==============================
# KONFIGURASI (DIAMBIL DARI FILE KAMU)
# ==============================

VOICE = "jv-ID-DimasNeural"
SPEAK_SPEED = "-10%"
SPEAK_PITCH = "+10Hz"

BAUD_RATE = 9600
AUDIO_FILE = "voice_tegal.mp3"

# Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat(history=[])

# ==============================
# UTIL
# ==============================

def clean_tts_text(text):
    return re.sub(r"[^\w\s,.!?]", "", text).strip()

# ==============================
# CEPOT CONTROLLER
# ==============================

class CepotController:
    def __init__(self):
        self.ser = None
        self.is_connected = False

        try:
            pygame.mixer.quit()
            # Gunakan standard CD quality (44100Hz) dan buffer 4096 untuk menghilangkan kresek & ketidakstabilan di Windows
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            print("✅ Audio System Ready (44100Hz, Buffer 4096)")
        except Exception as e:
            print("⚠️ Audio init error:", e)

    # ==========================
    # SERIAL
    # ==========================

    def connect(self, port):
        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=5)
            time.sleep(2)
            self.is_connected = True
            print(f"✅ Arduino Tegal Connect: {port}")
            return True, f"Terhubung ke {port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.ser:
            self.ser.close()
        self.is_connected = False
        return True, "Arduino terputus"

    # ==========================
    # EDGE TTS (SESUAI FILE ASLI)
    # ==========================

    async def bicara_async(self, teks, filepath):
        communicate = edge_tts.Communicate(
            teks,
            VOICE,
            rate=SPEAK_SPEED,
            pitch=SPEAK_PITCH
        )

        # MODE STREAM (LEBIH TAHAN FIREWALL)
        with open(filepath, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        return os.path.exists(filepath) and os.path.getsize(filepath) > 1000

    # ==========================
    # SUARA + GERAK (FALLBACK/SINKRON)
    # ==========================

    def bicara_dan_gerak(self, teks):
        teks = clean_tts_text(teks)
        print(f"🤖 Wayang: {teks}")

        filepath = AUDIO_FILE
        try:
            # Hentikan semua audio yang sedang berjalan agar tidak tumpang tindih
            pygame.mixer.stop()

            if os.path.exists(filepath):
                os.remove(filepath)
                time.sleep(0.1)
        except Exception as e:
            print("⚠️ Clean audio file warning:", e)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sukses = loop.run_until_complete(self.bicara_async(teks, filepath))
        loop.close()

        if not sukses:
            print("❌ TTS gagal total")
            return

        try:
            if self.is_connected and self.ser:
                self.ser.write(b'T')

            suara = pygame.mixer.Sound(filepath)
            channel = suara.play()

            if channel:
                while channel.get_busy():
                    time.sleep(0.1)
            else:
                time.sleep(3)

            if self.is_connected and self.ser:
                self.ser.write(b'S')

        except Exception as e:
            print("❌ Audio error:", e)
            if self.ser:
                self.ser.write(b'S')

    # ==========================
    # MOVEMENT CONTROL (FOR FRONTEND PLAYER)
    # ==========================

    def start_movement(self):
        if self.is_connected and self.ser:
            try:
                self.ser.write(b'T')
                print("🔌 Arduino Mouth Movement: STARTED")
                return True
            except Exception as e:
                print("❌ Arduino write error:", e)
        return False

    def stop_movement(self):
        if self.is_connected and self.ser:
            try:
                self.ser.write(b'S')
                print("🔌 Arduino Mouth Movement: STOPPED")
                return True
            except Exception as e:
                print("❌ Arduino write error:", e)
        return False

    # ==========================
    # API TALK (FLASK)
    # ==========================

    def talk(self, user_text):
        PROMPT_TEGAL = (
            "Kamu adalah Cepot versi Tegal. "
            "Jawablah setiap pertanyaan dengan Bahasa Indonesia yang dicampur kental dengan dialek Ngapak Tegal. "
            "WAJIB gunakan kata ganti: 'Inyong' (untuk saya), 'koen' atau 'Sampeyan' (untuk kamu). "
            "Gunakan kata khas seperti: 'Kepimen' (gimana), 'Udu' (bukan), 'Laka-laka' (luar biasa), 'Jang' (juragan), 'Wis' (sudah). "
            "Gaya bicara: Ceplas-ceplos, lucu, agak ngegas tapi akrab, seperti teman sendiri, tapi tahu segalanya. "
            "Jawab SINGKAT saja maksimal 5 kalimat biar tidak kelamaan."
        )

        try:
            response = chat.send_message(
                user_text + ". " + PROMPT_TEGAL,
                stream=False
            )

            reply = response.text.strip() if response and response.text else "Inyong ora mudeng, Rika."

            # Hasilkan file suara di static folder agar dapat diputar langsung oleh browser
            filepath = os.path.join("static", "voice_tegal.mp3")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print("⚠️ Clean static audio warning:", e)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sukses = loop.run_until_complete(self.bicara_async(reply, filepath))
            loop.close()

            if sukses:
                return {"response": reply, "audio_url": "/static/voice_tegal.mp3"}
            else:
                return {"response": reply, "audio_url": None}

        except Exception as e:
            print("❌ Gemini/TTS error:", e)
            return {"response": "Aduh sinyal e laka, Rika.", "audio_url": None}
    
    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]
    
    def process_physical_interaction(self, user_text):
        return self.talk(user_text)



# ==============================
# INSTANCE GLOBAL
# ==============================

cepot_system = CepotController()

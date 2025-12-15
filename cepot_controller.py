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
            pygame.mixer.init(frequency=24000)
            print("✅ Audio System Ready")
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

    async def bicara_async(self, teks):
        communicate = edge_tts.Communicate(
            teks,
            VOICE,
            rate=SPEAK_SPEED,
            pitch=SPEAK_PITCH
        )

        # MODE STREAM (LEBIH TAHAN FIREWALL)
        with open(AUDIO_FILE, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        return os.path.exists(AUDIO_FILE) and os.path.getsize(AUDIO_FILE) > 1000

    # ==========================
    # SUARA + GERAK
    # ==========================

    def bicara_dan_gerak(self, teks):
        teks = clean_tts_text(teks)
        print(f"🤖 Wayang: {teks}")

        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            if os.path.exists(AUDIO_FILE):
                os.remove(AUDIO_FILE)
                time.sleep(0.1)
        except:
            pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sukses = loop.run_until_complete(self.bicara_async(teks))
        loop.close()

        if not sukses:
            print("❌ TTS gagal total")
            return

        try:
            if self.is_connected and self.ser:
                self.ser.write(b'T')

            pygame.mixer.music.load(AUDIO_FILE)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.unload()

            if self.is_connected and self.ser:
                self.ser.write(b'S')

        except Exception as e:
            print("❌ Audio error:", e)
            if self.ser:
                self.ser.write(b'S')

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

            threading.Thread(
                target=self.bicara_dan_gerak,
                args=(reply,),
                daemon=True
            ).start()

            return reply

        except Exception as e:
            print("❌ Gemini error:", e)
            return "Aduh sinyal e laka, Rika."
    
    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]
    
    def process_physical_interaction(self, user_text):
        return self.talk(user_text)



# ==============================
# INSTANCE GLOBAL
# ==============================

cepot_system = CepotController()

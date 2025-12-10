import serial
import serial.tools.list_ports
import threading
import time
import asyncio
import edge_tts
import pygame
import os
import google.generativeai as genai

# --- KONFIGURASI ---
API_KEY = "AIzaSyDmUtu7mZVRVqp88QigLZOra3UUsPkUhJk" # Ganti API Key kamu
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat(history=[])

# Konfigurasi Suara (Tegal Style)
VOICE = "jv-ID-DimasNeural" 
SPEAK_SPEED = "-10%"
SPEAK_PITCH = "+10Hz"
AUDIO_FILE = "static/voice_tegal.mp3" # Simpan di static agar aman

class CepotController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        try:
            pygame.mixer.init()
        except Exception as e:
            print("Warning Audio:", e)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port_name):
        try:
            self.ser = serial.Serial(port_name, 9600, timeout=1)
            time.sleep(2)
            self.is_connected = True
            return True, f"Terhubung ke {port_name}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.ser:
            self.ser.close()
        self.is_connected = False
        return "Terputus"

    async def _generate_audio(self, text):
        """Generate audio dengan Edge TTS"""
        communicate = edge_tts.Communicate(text, VOICE, rate=SPEAK_SPEED, pitch=SPEAK_PITCH)
        await communicate.save(AUDIO_FILE)

    def speak_and_move_task(self, text):
        """Fungsi sync untuk dijalankan di thread background"""
        print(f"Wayang Bicara: {text}")

        # 1. Hapus file lama jika ada
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
            except:
                pass

        try:
            # 2. Generate Suara (Async run di dalam sync)
            asyncio.run(self._generate_audio(text))

            # 3. Sinyal Buka Mulut (Arduino)
            if self.is_connected and self.ser:
                self.ser.write(b'T') 

            # 4. Play Audio
            pygame.mixer.music.load(AUDIO_FILE)
            pygame.mixer.music.play()
            
            # Tunggu suara selesai
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()

            # 5. Sinyal Tutup Mulut
            if self.is_connected and self.ser:
                self.ser.write(b'S')

        except Exception as e:
            print(f"❌ Error Fisik: {e}")
            if self.is_connected and self.ser: self.ser.write(b'S')

    def process_physical_interaction(self, user_text):
        """Logic Utama: Gemini -> TTS -> Gerak"""
        try:
            # Prompt Tegal
            prompt_tegal = (
                f"User: {user_text}. "
                "Jawab dengan Bahasa Indonesia logat Tegal (Ngapak). "
                "Gunakan 'Inyong' dan 'Rika'. Jawab singkat lucu maksimal 2 kalimat."
            )
            
            response = chat.send_message(prompt_tegal)
            reply = response.text.replace("*", "")
            
            # Jalankan fisik di background thread agar API langsung return teks ke web
            threading.Thread(target=self.speak_and_move_task, args=(reply,)).start()
            
            return reply
        except Exception as e:
            return f"Error AI: {str(e)}"

# Instance Global
cepot_system = CepotController()
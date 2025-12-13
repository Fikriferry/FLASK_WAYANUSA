import serial
import serial.tools.list_ports
import threading
import time
import asyncio
import edge_tts
from gtts import gTTS
import pygame
import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- KONFIGURASI ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")  # Ambil API Key dari .env
if not API_KEY: 
    print("❌ Error: API Key tidak ditemukan di file .env") 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat(history=[])

# Konfigurasi Suara (Tegal Style)
VOICE = "jv-ID-DimasNeural"
SPEAK_SPEED = None
SPEAK_PITCH = None
AUDIO_FILE = "static/voice_tegal.wav" # Simpan di static agar aman

class CepotController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully in main thread")
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

    async def _generate_audio_async(self, text):
        """Generate audio dengan edge_tts"""
        print(f"Text to speak: '{text}'")
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(AUDIO_FILE)
            print(f"Audio saved to {AUDIO_FILE}")
            if os.path.exists(AUDIO_FILE):
                print(f"File exists, size: {os.path.getsize(AUDIO_FILE)} bytes")
            else:
                print("File not found after save")
        except Exception as e:
            print(f"Error in _generate_audio: {e}")
            # Fallback: create a simple beep sound
            print("Falling back to beep sound")
            try:
                import wave
                import struct
                # Create a simple beep
                sample_rate = 44100
                duration = 1  # seconds
                frequency = 800  # Hz
                num_samples = int(sample_rate * duration)
                buffer = bytearray()
                for i in range(num_samples):
                    sample = int(32767 * 0.5 * (1 + 0.5 * (i % (sample_rate // frequency) < sample_rate // (2 * frequency))))
                    buffer.extend(struct.pack('<h', sample))
                with wave.open(AUDIO_FILE, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(buffer)
                print("Beep sound created")
            except Exception as e2:
                print(f"Failed to create beep: {e2}")
                raise e  # Raise original error

    def _generate_audio(self, text):
        """Sync wrapper for async audio generation"""
        asyncio.run(self._generate_audio_async(text))

    def speak_and_move_task(self, text):
        """Fungsi sync untuk dijalankan di thread background"""
        print(f"Wayang Bicara: {text}")
        print(f"Connected: {self.is_connected}")

        # Pygame mixer already initialized in main thread
        print("Using pygame mixer from main thread")

        # 1. Hapus file lama jika ada
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
                print("Old audio file removed")
            except Exception as e:
                print(f"Failed to remove old audio: {e}")

        try:
            # 2. Generate Suara
            print("Generating audio...")
            self._generate_audio(text)
            print(f"Audio generated at {AUDIO_FILE}")

            # 3. Sinyal Buka Mulut (Arduino)
            if self.is_connected and self.ser:
                try:
                    self.ser.write(b'T')
                    print("Sent 'T' to Arduino")
                except Exception as e:
                    print(f"Failed to send 'T' to Arduino: {e}")
            else:
                print("Arduino not connected, skipping mouth open")

            # 4. Play Audio
            print("Loading audio...")
            try:
                pygame.mixer.music.load(AUDIO_FILE)
                print("Audio loaded successfully")
                pygame.mixer.music.play()
                print("Audio playing...")
                print(f"Busy status: {pygame.mixer.music.get_busy()}")
            except Exception as e:
                print(f"Error loading/playing audio: {e}")
                return

            # Tunggu suara selesai
            start_time = time.time()
            while pygame.mixer.music.get_busy() and (time.time() - start_time) < 30:  # Timeout 30 detik
                time.sleep(0.1)

            if pygame.mixer.music.get_busy():
                print("Audio timeout, stopping")
                pygame.mixer.music.stop()

            pygame.mixer.music.unload()
            print("Audio finished")

            # 5. Sinyal Tutup Mulut
            if self.is_connected and self.ser:
                try:
                    self.ser.write(b'S')
                    print("Sent 'S' to Arduino")
                except Exception as e:
                    print(f"Failed to send 'S' to Arduino: {e}")
            else:
                print("Arduino not connected, skipping mouth close")

        except Exception as e:
            print(f"❌ Error Fisik: {e}")
            if self.is_connected and self.ser:
                try:
                    self.ser.write(b'S')
                    print("Sent 'S' to Arduino on error")
                except Exception as e2:
                    print(f"Failed to send 'S' on error: {e2}")

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
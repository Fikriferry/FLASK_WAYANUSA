from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ---------------------------------------------------
# MODEL DALANG
# ---------------------------------------------------
class Dalang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    foto = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)


# ---------------------------------------------------
# MODEL USER (Untuk login user biasa)
# ---------------------------------------------------
class User(db.Model):
    __tablename__ = "user"  # (perbaikan biar tidak bentrok dengan SQL reserved word)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # Relasi User -> QuizResult
    quiz_results = db.relationship("QuizResult", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------------------------------------
# MODEL ADMIN (Login Admin)
# ---------------------------------------------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    @property
    def password(self):
        raise AttributeError("Password tidak bisa dibaca!")

    @password.setter
    def password(self, plain_password):
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------------------------------------
# MODEL VIDEO
# ---------------------------------------------------
class Video(db.Model):
    __tablename__ = "video"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    youtube_link = db.Column(db.String(255), nullable=False)
    tampil = db.Column(db.Boolean, default=True)

    @property
    def youtube_id(self):
        # Extract YouTube ID from the link
        if 'youtube.com/watch?v=' in self.youtube_link:
            return self.youtube_link.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in self.youtube_link:
            return self.youtube_link.split('youtu.be/')[1].split('?')[0]
        elif self.youtube_link and len(self.youtube_link) == 11:  # Direct video ID
            return self.youtube_link
        return None


# ---------------------------------------------------
# MODEL AI
# ---------------------------------------------------
class AIModel(db.Model):
    __tablename__ = 'ai_models'

    id = db.Column(db.Integer, primary_key=True)
    version_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    accuracy = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AIModel {self.version_name}>'


# ===================================================
# ===============  MODEL QUIZ (BARU) ================
# ===================================================

# LEVEL QUIZ (Beginner / Intermediate / Advanced / Expert)
class QuizLevel(db.Model):
    __tablename__ = "quiz_levels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    questions = db.relationship("QuizQuestion", backref="level", lazy=True)
    quiz_results = db.relationship("QuizResult", backref="level", lazy=True)


# SOAL QUIZ
class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey("quiz_levels.id"), nullable=False)

    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)


# REKAP NILAI 1 SESI QUIZ
class QuizResult(db.Model):
    __tablename__ = "quiz_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey("quiz_levels.id"), nullable=False)

    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship("UserAnswer", backref="result", lazy=True)


# JAWABAN TIAP SOAL
class UserAnswer(db.Model):
    __tablename__ = "user_answers"

    id = db.Column(db.Integer, primary_key=True)
    quiz_result_id = db.Column(db.Integer, db.ForeignKey("quiz_results.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id"), nullable=False)

    user_answer = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_link = db.Column(db.String(500), nullable=True)
    thumbnail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Wayang(db.Model):
    __tablename__ = 'wayang_info'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), unique=True, nullable=False) # Kunci utama (misal: "Arjuna")
    deskripsi = db.Column(db.Text, nullable=False) # Deskripsi panjang
    
    def __repr__(self):
        return f'<Wayang {self.nama}>'
    
class WayangGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
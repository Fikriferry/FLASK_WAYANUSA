from flask import Blueprint, request, jsonify, session
from models import db, QuizLevel, QuizQuestion, QuizResult, UserAnswer, User
import random
from datetime import datetime

quiz_routes = Blueprint("quiz_routes", __name__)


# ============================================================
# 0. GET LIST LEVEL
# ============================================================
@quiz_routes.route("/levels", methods=["GET"])
def get_levels():
    levels = QuizLevel.query.all()
    data = [{"id": l.id, "name": l.name} for l in levels]
    return jsonify({"levels": data}), 200


# ============================================================
# 1. GET QUESTIONS (10 RANDOM PER LEVEL)
# ============================================================
@quiz_routes.route("/get_questions", methods=["GET"])
def get_questions():
    level_id = request.args.get("level", type=int)

    if not level_id:
        return jsonify({"error": "level parameter is required"}), 400

    questions = QuizQuestion.query.filter_by(level_id=level_id).all()

    if not questions:
        return jsonify({"error": "No questions found for this level"}), 404

    jumlah_soal = min(10, len(questions))
    selected = random.sample(questions, jumlah_soal)

    result = []
    for q in selected:
        result.append({
            "id": q.id,
            "question": q.question,
            "a": q.option_a,
            "b": q.option_b,
            "c": q.option_c,
            "d": q.option_d,
            "correct_answer": q.correct_answer  # tetap dari db
        })

    return jsonify({
        "level_id": level_id,
        "total_questions": jumlah_soal,
        "questions": result
    }), 200


# ============================================================
# 2. SUBMIT SCORE & JAWABAN USER
# ============================================================
@quiz_routes.route("/submit", methods=["POST"])
def submit_score():
    data = request.json

    user_id = session.get("user_id") or data.get("user_id")  # fallback untuk testing
    level_id = data.get("level_id")
    score = data.get("score")
    total_questions = data.get("total_questions")
    user_answers = data.get("user_answers", [])

    # Validasi
    if not user_id or not level_id or score is None or total_questions is None:
        return jsonify({"error": "user_id, level_id, score, total_questions required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    # Simpan QuizResult
    quiz_result = QuizResult(
        user_id=user_id,
        level_id=level_id,
        score=score,
        total_questions=total_questions,
        created_at=datetime.utcnow()
    )
    db.session.add(quiz_result)
    db.session.flush()  # supaya id muncul sebelum commit

    # Simpan jawaban individu
    for ans in user_answers:
        user_answer = UserAnswer(
            quiz_result_id=quiz_result.id,
            question_id=ans["question_id"],
            user_answer=ans["user_answer"] or "",
            is_correct=ans["is_correct"]
        )
        db.session.add(user_answer)

    db.session.commit()

    return jsonify({
        "message": "Quiz submitted successfully!",
        "result_id": quiz_result.id,
        "score": score,
        "total_questions": total_questions
    }), 200


# ============================================================
# 3. GET HISTORY QUIZ USER
# ============================================================
@quiz_routes.route("/history/<int:user_id>", methods=["GET"])
def get_history(user_id):
    results = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.created_at.desc()).all()
    data = []
    for r in results:
        data.append({
            "result_id": r.id,
            "level_id": r.level_id,
            "score": r.score,
            "total_questions": r.total_questions,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"history": data}), 200


# ============================================================
# 4. GET DETAIL HASIL QUIZ
# ============================================================
@quiz_routes.route("/result_detail/<int:result_id>", methods=["GET"])
def result_detail(result_id):
    answers = UserAnswer.query.filter_by(quiz_result_id=result_id).all()

    if not answers:
        return jsonify({"error": "Result not found"}), 404

    data = []
    for a in answers:
        question = QuizQuestion.query.get(a.question_id)
        correct_answer_key = question.correct_answer.lower()
        correct_answer_text = getattr(question, f"option_{correct_answer_key}")

        data.append({
            "question": question.question,
            "options": {
                "a": question.option_a,
                "b": question.option_b,
                "c": question.option_c,
                "d": question.option_d
            },
            "correct_answer": correct_answer_text,
            "user_answer": a.user_answer,
            "is_correct": a.is_correct
        })

    return jsonify({"detail": data}), 200

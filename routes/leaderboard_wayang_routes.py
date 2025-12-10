from flask import Blueprint, request, jsonify, render_template, session
from models import db, User, QuizResult, QuizLevel
from sqlalchemy import func

leaderboard_wayang_bp = Blueprint('leaderboard_wayang', __name__)

# Placeholder image mapping based on level
LEVEL_IMG_MAP = {
    'Beginner': '/static/wayang/level1.png',
    'Intermediate': '/static/wayang/level2.png',
    'Advanced': '/static/wayang/level3.png',
    'Expert': '/static/wayang/level4.png'
}

@leaderboard_wayang_bp.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    level_name = request.args.get('level', 'Beginner')
    if level_name not in LEVEL_IMG_MAP:
        return jsonify({'error': 'Invalid level'}), 400

    # Get level id
    level = QuizLevel.query.filter_by(name=level_name).first()
    if not level:
        return jsonify({'leaderboard': []}), 200

    # Query top scores per user for the level, ordered by score desc, limit 100
    subquery = db.session.query(
        QuizResult.user_id,
        func.max(QuizResult.score).label('top_score')
    ).filter(QuizResult.level_id == level.id).group_by(QuizResult.user_id).subquery()

    results = db.session.query(
        User.id,
        User.name,
        subquery.c.top_score
    ).join(subquery, User.id == subquery.c.user_id).order_by(subquery.c.top_score.desc()).limit(100).all()

    leaderboard = []
    for rank, (user_id, name, score) in enumerate(results, start=1):
        leaderboard.append({
            'rank': rank,
            'user_id': user_id,
            'name': name,
            'faculty': 'Unknown',
            'level': level_name,
            'score': score,
            'img': LEVEL_IMG_MAP[level_name]
        })

    response = {'leaderboard': leaderboard}

    # If user logged in, calculate their rank and score
    user_id = session.get('user_id')
    if user_id:
        user_score = None
        user_rank = None
        for item in leaderboard:
            if item['user_id'] == user_id:
                user_rank = item['rank']
                user_score = item['score']
                break
        if user_rank is None:
            # If not in top 100, find their position
            user_top_score = db.session.query(func.max(QuizResult.score)).filter(
                QuizResult.user_id == user_id, QuizResult.level_id == level.id
            ).scalar()
            if user_top_score:
                # Count how many have higher score
                higher_count = db.session.query(func.count()).select_from(subquery).filter(
                    subquery.c.top_score > user_top_score
                ).scalar()
                user_rank = higher_count + 1
                user_score = user_top_score
        response['your_rank'] = user_rank
        response['your_score'] = user_score

    return jsonify(response)

@leaderboard_wayang_bp.route('/leaderboard/wayang_page', methods=['GET'])
def leaderboard_page():
    return render_template('leaderboard_wayang.html')

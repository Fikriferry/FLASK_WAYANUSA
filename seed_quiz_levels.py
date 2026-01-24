from app import app, db
from models import QuizLevel

def seed_quiz_levels():
    with app.app_context():
        # Data level quiz
        levels = [
            {'name': 'Beginner'},
            {'name': 'Intermediate'},
            {'name': 'Advanced'},
            {'name': 'Expert'}
        ]

        for level_data in levels:
            # Cek apakah sudah ada
            exists = QuizLevel.query.filter_by(name=level_data['name']).first()
            if not exists:
                new_level = QuizLevel(**level_data)
                db.session.add(new_level)
                print(f"Added level: {level_data['name']}")
            else:
                print(f"Level {level_data['name']} already exists")

        db.session.commit()
        print("Seeding quiz levels completed.")

if __name__ == "__main__":
    seed_quiz_levels()

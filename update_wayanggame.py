from app import app
from models import db, WayangGame

with app.app_context():
    # Drop the existing WayangGame table
    WayangGame.__table__.drop(db.engine, checkfirst=True)
    # Recreate the table with new columns
    WayangGame.__table__.create(db.engine)

print("WayangGame table updated successfully.")

from app import app, db
from models import WayangGame

def seed_wayanggame():
    with app.app_context():
        # Data untuk testing - menggunakan gambar yang sudah ada
        data = [
            {
                'nama': 'Arjuna',
                'thumbnail': 'images/wayang/thumbnail/arjuna_thumb.png',
                'badan': 'images/wayang/badan/badan.png',
                'tangan_kanan_atas': 'images/wayang/tangan_kanan_atas/tangan_kanan_atas.png',
                'tangan_kanan_bawah': 'images/wayang/tangan_kanan_bawah/tangan_kanan_bawah.png',
                'tangan_kiri_atas': 'images/wayang/tangan_kiri_atas/tangan_kiri_atas.png',
                'tangan_kiri_bawah': 'images/wayang/tangan_kiri_bawah/tangan_kiri_bawah.png'
            }
        ]

        for item in data:
            # Cek apakah sudah ada
            exists = WayangGame.query.filter_by(nama=item['nama']).first()
            if not exists:
                new_game = WayangGame(**item)
                db.session.add(new_game)
                print(f"Added {item['nama']}")
            else:
                print(f"{item['nama']} already exists")

        db.session.commit()
        print("Seeding completed.")

if __name__ == "__main__":
    seed_wayanggame()

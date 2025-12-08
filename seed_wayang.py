from app import app, db
from models import Wayang

# Data Awal (Sesuai Folder Dataset Kamu)
data_wayang = {
    "Abimanyu": "Putra Arjuna yang dikenal sebagai ksatria muda pemberani dan ahli strategi perang. Ia gugur secara heroik di medan perang Baratayuda saat dikeroyok Kurawa.",
    "Anoman": "Kera putih sakti mandraguna, putra Batara Guru. Ia adalah abdi setia Sri Rama dalam kisah Ramayana dan memiliki umur panjang hingga era Mahabharata.",
    "Arjuna": "Putra ketiga Pandawa yang berparas tampan dan lemah lembut. Ia adalah pemanah ulung pemilik panah Pasopati dan penengah Pandawa.",
    "Bagong": "Punakawan bungsu anak Semar. Bertubuh gemuk, bermata lebar, dan lucu. Sifatnya lugu, ceplas-ceplos, dan sering melontarkan kritik jenaka.",
    "Baladewa": "Kakak Prabu Kresna, Raja Mandura. Berwatak keras dan mudah marah, namun sangat jujur dan adil. Senjata andalannya adalah Nanggala.",
    "Bima": "Putra kedua Pandawa (Werkudara). Bertubuh tinggi besar, kuku Pancanaka, dan Gada Rujakpala. Sifatnya jujur, tegas, dan tidak basa-basi.",
    "Buta": "Istilah umum untuk Raksasa dalam pewayangan. Menggambarkan sifat angkara murka, kasar, dan menjadi musuh para ksatria.",
    "Cakil": "Tokoh raksasa dengan rahang bawah menonjol (cameh). Ia sangat lincah, namun melambangkan sifat pantang menyerah di jalan yang salah.",
    "Durna": "Guru besar ilmu perang Pandawa dan Kurawa. Sangat sakti namun sering berpihak pada Kurawa karena politik dan sumpah setianya pada negara Hastina.",
    "Dursasana": "Adik Duryudana yang berbadan gagah namun bermulut besar dan kasar. Ia melambangkan kesewenang-wenangan.",
    "Duryudana": "Raja Hastinapura dan pemimpin Kurawa. Wataknya angkuh, keras kepala, dan mudah terhasut oleh Sengkuni untuk memusuhi Pandawa.",
    "Gareng": "Anak tertua Semar. Kakinya pincang dan tangannya ceko, melambangkan kehati-hatian dalam melangkah dan tidak suka mengambil hak orang lain.",
    "Gatotkaca": "Putra Bima, ksatria Pringgandani. Dikenal dengan 'Otot kawat tulang besi', bisa terbang, dan menjadi pelindung Pandawa.",
    "Karna": "Kakak tertua Pandawa yang berada di pihak Kurawa. Pemanah sakti yang setara dengan Arjuna, dikenal sangat dermawan dan setia kawan.",
    "Kresna": "Raja Dwarawati, titisan Dewa Wisnu. Penasihat utama Pandawa yang bijaksana, ahli strategi ulung, dan pemilik senjata Cakra.",
    "Nakula Sadewa": "Putra kembar Pandawa. Nakula ahli merawat kuda dan sangat tampan, sedangkan Sadewa ahli perbintangan dan bijaksana.",
    "Patih Sabrang": "Sebutan untuk patih dari kerajaan seberang (luar Jawa/raksasa). Biasanya digambarkan gagah, brangasan, dan menjadi musuh.",
    "Petruk": "Anak kedua Semar. Berbadan tinggi, hidung panjang, dan selalu tersenyum. Ia cerdas, humoris, dan suka menyindir ketidakadilan.",
    "Puntadewa": "Putra tertua Pandawa (Yudhistira). Berdarah putih (suci), tidak pernah berbohong, sangat sabar, dan tidak memiliki musuh.",
    "Semar": "Tokoh punakawan utama, pengasuh para ksatria. Sejatinya adalah dewa (Batara Ismaya) yang turun ke bumi. Simbol kebijaksanaan rakyat.",
    "Sengkuni": "Patih Hastinapura yang licik. Ia adalah dalang di balik permusuhan Pandawa dan Kurawa, ahli siasat buruk dan adu domba.",
    "Togog": "Kakak Semar yang memihak pada musuh (raksasa). Tugasnya menasihati majikan yang jahat agar kembali ke jalan benar, meski jarang didengar."
}

def seed_database():
    with app.app_context():
        # Buat tabel jika belum ada
        db.create_all()
        
        print("Memulai proses seeding data Wayang...")
        added_count = 0
        
        for nama, deskripsi in data_wayang.items():
            # Cek apakah wayang sudah ada? (Biar tidak duplikat kalau script dijalankan 2x)
            exists = Wayang.query.filter_by(nama=nama).first()
            
            if not exists:
                new_wayang = Wayang(nama=nama, deskripsi=deskripsi)
                db.session.add(new_wayang)
                added_count += 1
                print(f"[+] Menambahkan: {nama}")
            else:
                print(f"[-] {nama} sudah ada, skip.")
        
        db.session.commit()
        print(f"\nSelesai! {added_count} data baru berhasil ditambahkan.")

if __name__ == "__main__":
    seed_database()
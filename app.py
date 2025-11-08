from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
from models import db, Dalang

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_admin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================
# DECORATOR UNTUK LOGIN ADMIN
# ============================================================
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login_admin'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ============================================================
# ROUTE UNTUK PENGGUNA (USER SIDE)
# ============================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login_user():
    return render_template('login.html')

@app.route('/register')
def register_user():
    return render_template('register.html')

@app.route('/pengenalan-wayang')
def pengenalan_wayang():
    return render_template('pengenalan_wayang.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/mencari-dalang')
def mencari_dalang():
    return render_template('mencari_dalang.html')

@app.route('/pertunjukan-wayang')
def pertunjukan_wayang():
    return render_template('pertunjukan_wayang.html')

# ============================================================
# ROUTE UNTUK ADMIN LOGIN & DASHBOARD
# ============================================================

@app.route('/admin')
def index_admin():
    # Redirect ke dashboard jika sudah login, kalau belum arahkan ke login admin
    if 'admin_logged_in' not in session:
        return redirect(url_for('login_admin'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def logout_admin():
    session.pop('admin_logged_in', None)
    flash('Logout berhasil!', 'success')
    return redirect(url_for('login_admin'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    dalang_count = Dalang.query.count()
    dalangs = Dalang.query.all()
    return render_template('admin/index.html', dalang_count=dalang_count, dalangs=dalangs)

# ============================================================
# CRUD DALANG (ADMIN)
# ============================================================

@app.route('/admin/dalang')
@login_required
def dalang_list():
    dalangs = Dalang.query.all()
    return render_template('admin/dalang_list.html', dalangs=dalangs)

@app.route('/admin/dalang/add', methods=['GET', 'POST'])
@login_required
def dalang_add():
    if request.method == 'POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not nama or not alamat:
            flash('Nama dan alamat wajib diisi!', 'error')
            return redirect(url_for('dalang_add'))

        foto = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto = filename

        new_dalang = Dalang(
            nama=nama,
            alamat=alamat,
            foto=foto,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_dalang)
        db.session.commit()
        flash('Dalang berhasil ditambahkan!', 'success')
        return redirect(url_for('dalang_list'))

    return render_template('admin/dalang_form.html', dalang=None)

@app.route('/admin/dalang/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def dalang_edit(id):
    dalang = Dalang.query.get_or_404(id)
    if request.method == 'POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not nama or not alamat:
            flash('Nama dan alamat wajib diisi!', 'error')
            return redirect(url_for('dalang_edit', id=id))

        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                dalang.foto = filename

        dalang.nama = nama
        dalang.alamat = alamat
        dalang.latitude = latitude
        dalang.longitude = longitude
        db.session.commit()
        flash('Dalang berhasil diupdate!', 'success')
        return redirect(url_for('dalang_list'))

    return render_template('admin/dalang_form.html', dalang=dalang)

@app.route('/admin/dalang/delete/<int:id>')
@login_required
def dalang_delete(id):
    dalang = Dalang.query.get_or_404(id)
    if dalang.foto:
        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], dalang.foto)
        if os.path.exists(foto_path):
            os.remove(foto_path)
    db.session.delete(dalang)
    db.session.commit()
    flash('Dalang berhasil dihapus!', 'success')
    return redirect(url_for('dalang_list'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================================
# MAIN APP RUN
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
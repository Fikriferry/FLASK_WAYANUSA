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

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Login required decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('admin_logged_in', None)
    flash('Logout berhasil!', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    dalang_count = Dalang.query.count()
    dalangs = Dalang.query.all()
    return render_template('admin/index.html', dalang_count=dalang_count, dalangs=dalangs)

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

        new_dalang = Dalang(nama=nama, alamat=alamat, foto=foto, latitude=latitude, longitude=longitude)
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
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], dalang.foto))
    db.session.delete(dalang)
    db.session.commit()
    flash('Dalang berhasil dihapus!', 'success')
    return redirect(url_for('dalang_list'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

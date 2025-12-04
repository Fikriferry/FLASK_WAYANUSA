from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import os
from models import Video


from models import db, Dalang, User, Admin

web_routes = Blueprint("web", __name__)


# -------------------------
# DECORATORS
# -------------------------
def admin_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('web.login_admin'))
        return f(*args, **kwargs)
    return wrapper


def user_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('web.login_user'))
        return f(*args, **kwargs)
    return wrapper


# -------------------------
# FRONTEND USER ROUTES
# -------------------------

@web_routes.route('/')
def home():
    return render_template('index.html')


@web_routes.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_logged_in'] = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login berhasil!', 'success')
            return redirect(url_for('web.home'))
        else:
            flash('Email atau password salah!', 'error')

    return render_template('login.html')


@web_routes.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm-password']

        if password != confirm:
            flash('Password dan konfirmasi tidak cocok!', 'error')
            return redirect(url_for('web.register_user'))

        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'error')
            return redirect(url_for('web.register_user'))

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registrasi berhasil!', 'success')
        return redirect(url_for('web.login_user'))

    return render_template('register_user.html')


@web_routes.route('/logout')
def logout_user():
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('web.home'))


@web_routes.route('/pengenalan-wayang')
def pengenalan_wayang():
    return render_template('pengenalan_wayang.html')


@web_routes.route('/quiz')
def quiz():
    return render_template('quiz.html')

@web_routes.route('/quiz/play')
def quiz_play():
    return render_template('quiz_play.html')


@web_routes.route('/mencari-dalang')
def mencari_dalang():
    return render_template('mencari_dalang.html')


@web_routes.route('/pertunjukan-wayang')
def pertunjukan_wayang():
    videos = Video.query.filter_by(tampil=True).all()
    return render_template('pertunjukan_wayang.html', videos=videos)


# -------------------------
# ADMIN ROUTES
# -------------------------

@web_routes.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if not admin or not admin.check_password(password):
            flash('Username atau password salah!', 'error')
            return redirect(url_for('web.login_admin'))

        session['admin_logged_in'] = True
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username

        return redirect(url_for('web.admin_dashboard'))

    return render_template('admin/login.html')


@web_routes.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    dalang_count = Dalang.query.count()
    dalangs = Dalang.query.all()
    return render_template('admin/index.html', dalang_count=dalang_count, dalangs=dalangs)


@web_routes.route('/admin/logout')
@admin_login_required
def logout_admin():
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('web.login_admin'))


# -------------------------
# CRUD DALANG
# -------------------------

@web_routes.route('/admin/dalang/list')
@admin_login_required
def dalang_list():
    dalangs = Dalang.query.all()
    return render_template('admin/dalang_list.html', dalangs=dalangs)


@web_routes.route('/admin/dalang/add', methods=['GET', 'POST'])
@admin_login_required
def dalang_add():
    if request.method == 'POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        foto = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                foto = filename

        new_dalang = Dalang(nama=nama, alamat=alamat, latitude=latitude, longitude=longitude, foto=foto)
        db.session.add(new_dalang)
        db.session.commit()

        flash('Dalang berhasil ditambahkan!', 'success')
        return redirect(url_for('web.admin_dashboard'))

    return render_template('admin/dalang_form.html', dalang=None)


@web_routes.route('/admin/dalang/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def dalang_edit(id):
    dalang = Dalang.query.get_or_404(id)
    if request.method == 'POST':
        dalang.nama = request.form['nama']
        dalang.alamat = request.form['alamat']
        dalang.latitude = request.form.get('latitude')
        dalang.longitude = request.form.get('longitude')

        if 'foto' in request.files:
            file = request.files['foto']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                dalang.foto = filename

        db.session.commit()
        flash('Dalang berhasil diperbarui!', 'success')
        return redirect(url_for('web.dalang_list'))

    return render_template('admin/dalang_form.html', dalang=dalang)


@web_routes.route('/admin/dalang/delete/<int:id>')
@admin_login_required
def dalang_delete(id):
    dalang = Dalang.query.get_or_404(id)
    db.session.delete(dalang)
    db.session.commit()
    flash('Dalang berhasil dihapus!', 'success')
    return redirect(url_for('web.dalang_list'))


# ----------------------------------------
# VIDEO MANAGEMENT
# ----------------------------------------



@web_routes.route('/admin/video')
@admin_login_required
def video_list():
    videos = Video.query.all()
    return render_template('admin/video_list.html', videos=videos)


@web_routes.route('/admin/video/add', methods=['GET', 'POST'])
@admin_login_required
def video_add():
    if request.method == 'POST':
        judul = request.form['judul']
        youtube_id = request.form['youtube_id']

        if not judul or not youtube_id:
            flash("Judul dan YouTube ID wajib diisi!", "error")
            return redirect(url_for('web.video_add'))

        video = Video(judul=judul, youtube_id=youtube_id)
        db.session.add(video)
        db.session.commit()

        flash("Video berhasil ditambahkan!", "success")
        return redirect(url_for('web.video_list'))

    return render_template('admin/video_add.html')


@web_routes.route('/admin/video/delete/<int:id>')
@admin_login_required
def video_delete(id):
    video = Video.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()
    flash("Video berhasil dihapus!", "success")
    return redirect(url_for('web.video_list'))

# -------------------------
# ROUTE FOTO (PENTING)
# -------------------------

@web_routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("static/uploads", filename)
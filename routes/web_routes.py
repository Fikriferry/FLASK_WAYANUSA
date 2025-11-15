from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import os

from models import db, Dalang, User, Admin

web_routes = Blueprint("web", __name__)


# ----------------------------------------
# DECORATORS
# ----------------------------------------
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


# ----------------------------------------
# FRONTEND USER ROUTES
# ----------------------------------------

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
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash('Password dan konfirmasi tidak cocok!', 'error')
            return redirect(url_for('web.register_user'))

        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'error')
            return redirect(url_for('web.register_user'))

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('web.login_user'))

    return render_template('register.html')


@web_routes.route('/logout')
def logout_user():
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Logout berhasil!', 'success')
    return redirect(url_for('web.home'))


@web_routes.route('/pengenalan-wayang')
def pengenalan_wayang():
    return render_template('pengenalan_wayang.html')


@web_routes.route('/quiz')
def quiz():
    return render_template('quiz.html')


@web_routes.route('/quiz_play')
@user_login_required
def quiz_play():
    return render_template("quiz_play.html")


@web_routes.route('/mencari-dalang')
def mencari_dalang():
    dalangs = Dalang.query.all()
    return render_template('mencari_dalang.html', dalangs=dalangs)


@web_routes.route('/pertunjukan-wayang')
def pertunjukan_wayang():
    return render_template('pertunjukan_wayang.html')


# ----------------------------------------
# ADMIN ROUTES
# ----------------------------------------

@web_routes.route('/admin')
def index_admin():
    if 'admin_logged_in' not in session:
        return redirect(url_for('web.login_admin'))
    return redirect(url_for('web.admin_dashboard'))


@web_routes.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()

        if not admin or not admin.check_password(password):
            flash('Username atau password salah!', 'error')
            return redirect(url_for('web.login_admin'))

        session.update({
            'admin_logged_in': True,
            'admin_id': admin.id,
            'admin_username': admin.username
        })

        flash('Login berhasil!', 'success')
        return redirect(url_for('web.admin_dashboard'))

    return render_template('admin/login.html')


@web_routes.route('/admin/logout')
@admin_login_required
def logout_admin():
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('web.login_admin'))


# Dashboard
@web_routes.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    dalang_count = Dalang.query.count()
    dalangs = Dalang.query.all()
    return render_template('admin/index.html', dalang_count=dalang_count, dalangs=dalangs)


# DALANG CRUD
@web_routes.route('/admin/dalang')
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

        if not nama or not alamat:
            flash('Nama dan alamat wajib diisi!', 'error')
            return redirect(url_for('web.dalang_add'))

        foto = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
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
        return redirect(url_for('web.dalang_list'))

    return render_template('admin/dalang_form.html', dalang=None)


@web_routes.route('/admin/dalang/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def dalang_edit(id):
    dalang = Dalang.query.get_or_404(id)

    if request.method == 'POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not nama or not alamat:
            flash('Nama dan alamat wajib diisi!', 'error')
            return redirect(url_for('web.dalang_edit', id=id))

        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                dalang.foto = filename

        dalang.nama = nama
        dalang.alamat = alamat
        dalang.latitude = latitude
        dalang.longitude = longitude

        db.session.commit()
        flash('Dalang berhasil diupdate!', 'success')
        return redirect(url_for('web.dalang_list'))

    return render_template('admin/dalang_form.html', dalang=dalang)


@web_routes.route('/admin/dalang/delete/<int:id>')
@admin_login_required
def dalang_delete(id):
    dalang = Dalang.query.get_or_404(id)

    if dalang.foto:
        path = os.path.join('static/uploads', dalang.foto)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(dalang)
    db.session.commit()

    flash('Dalang berhasil dihapus!', 'success')
    return redirect(url_for('web.dalang_list'))


# File Upload Serving
@web_routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("static/uploads", filename)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
import os
from models import Video, db, AIModel, Dalang, User, Admin, Article
from ai_manager import reload_model

web_routes = Blueprint("web", __name__)

# Konfigurasi folder upload (bisa ditaruh di config app)
UPLOAD_FOLDER = 'static/models_storage'
ALLOWED_EXTENSIONS = {'keras', 'h5'}

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
    # 1. FIX: Cek apakah user sudah login? Jika ya, tendang ke home
    if 'user_logged_in' in session:
        return redirect(url_for('web.home'))

    if request.method == 'POST':
        # 2. FIX: Gunakan .get() agar tidak error 400 jika input kosong/salah nama
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_logged_in'] = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login berhasil!', 'success')
            return redirect(url_for('web.home'))
        else:
            flash('Email atau password salah!', 'error')
            # 3. FIX: Redirect balik ke diri sendiri agar URL bersih (hindari resubmit form)
            return redirect(url_for('web.login_user'))

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

@web_routes.route("/pertunjukan_wayang/video/<youtube_id>")
def video_detail(youtube_id):
    if not session.get("user_logged_in"):
        return redirect(url_for("web.login_user"))

    video = Video.query.filter_by(youtube_id=youtube_id).first_or_404()
    related_videos = Video.query.filter(Video.youtube_id != youtube_id).all()
    return render_template("video_detail.html", video=video, related_videos=related_videos)

@web_routes.route('/search')
def search_video():
    q = request.args.get("q", "")

    # HINDARI: q kosong tapi masih tampil ""
    q = q.strip()

    if q:
        videos = Video.query.filter(Video.judul.like(f"%{q}%")).all()
    else:
        videos = []

    return render_template("search_video.html", q=q, videos=videos)


@web_routes.route('/artikel')
def artikel():
    artikels = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('artikel.html', artikels=artikels)


@web_routes.route('/artikel/<int:id>')
def artikel_detail(id):
    artikel = Article.query.get_or_404(id)
    return render_template('artikel_detail.html', artikel=artikel)


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
    artikel_count = Article.query.count()
    dalangs = Dalang.query.all()
    return render_template('admin/index.html', dalang_count=dalang_count, artikel_count=artikel_count, dalangs=dalangs)


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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_thumbnail(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def save_thumbnail(file):
    if file and allowed_thumbnail(file.filename):
        from datetime import datetime
        ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"artikel_{timestamp}.{ext}"
        filepath = os.path.join('static/uploads/thumbnails', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Check file size <= 2MB
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 2 * 1024 * 1024:  # 2MB
            return None, "Ukuran file maksimal 2MB!"
        file.save(filepath)
        return filename, None
    return None, "Format file tidak didukung! Hanya JPG, JPEG, PNG."

@web_routes.route('/admin/models', methods=['GET', 'POST'])
def admin_models():
    # 1. HANDLE UPLOAD MODEL BARU
    if request.method == 'POST':
        if 'model_file' not in request.files:
            flash('Tidak ada file', 'danger')
            return redirect(request.url)
        
        file = request.files['model_file']
        version_name = request.form.get('version_name')
        accuracy = request.form.get('accuracy')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Pastikan folder ada
            save_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            
            file_path = os.path.join(UPLOAD_FOLDER, filename) # Path relatif untuk DB
            full_path = os.path.join(save_dir, filename)
            
            file.save(full_path)

            # Simpan ke Database
            new_model = AIModel(
                version_name=version_name,
                file_path=file_path, # Simpan path relatif
                accuracy=accuracy,
                is_active=False
            )
            db.session.add(new_model)
            db.session.commit()
            flash('Model berhasil diupload!', 'success')
        else:
            flash('Format file salah. Harap upload .keras atau .h5', 'danger')

    # 2. TAMPILKAN LIST MODEL
    models = AIModel.query.order_by(AIModel.created_at.desc()).all()
    return render_template('admin/model_list.html', models=models)

@web_routes.route('/admin/models/activate/<int:id>')
def activate_model(id):
    # 1. Nonaktifkan semua model dulu
    AIModel.query.update({AIModel.is_active: False})
    
    # 2. Aktifkan model yang dipilih
    target = AIModel.query.get_or_404(id)
    target.is_active = True
    db.session.commit()

    # 3. HOT RELOAD: Ganti model di RAM tanpa restart server
    success = reload_model(id)
    
    if success:
        flash(f'Model "{target.version_name}" sekarang AKTIF dan digunakan!', 'success')
    else:
        flash('Gagal memuat model. File mungkin hilang.', 'danger')

    return redirect(url_for('web.admin_models'))

@web_routes.route('/admin/models/delete/<int:id>')
def delete_model(id):
    target = AIModel.query.get_or_404(id)
    
    if target.is_active:
        flash('Tidak bisa menghapus model yang sedang aktif!', 'warning')
        return redirect(url_for('web.admin_models'))

    # Hapus file fisik
    try:
        full_path = os.path.join(current_app.root_path, target.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    db.session.delete(target)
    db.session.commit()
    flash('Model berhasil dihapus.', 'success')
    return redirect(url_for('web.admin_models'))

# ----------------------------------------
# ARTIKEL MANAGEMENT
# ----------------------------------------

@web_routes.route('/admin/artikel')
@admin_login_required
def artikel_list():
    artikels = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/article_list.html', artikels=artikels)


@web_routes.route('/admin/artikel/add', methods=['GET', 'POST'])
@admin_login_required
def artikel_add():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        source_link = request.form.get('source_link')

        if not title or not content:
            flash('Judul dan konten artikel wajib diisi!', 'error')
            return redirect(url_for('web.artikel_add'))

        thumbnail = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file.filename:
                thumbnail, error = save_thumbnail(file)
                if error:
                    flash(error, 'error')
                    return redirect(url_for('web.artikel_add'))

        new_artikel = Article(title=title, content=content, source_link=source_link, thumbnail=thumbnail)
        db.session.add(new_artikel)
        db.session.commit()

        flash('Artikel berhasil ditambahkan!', 'success')
        return redirect(url_for('web.artikel_list'))

    return render_template('admin/article_form.html', artikel=None)


@web_routes.route('/admin/artikel/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def artikel_edit(id):
    artikel = Article.query.get_or_404(id)
    if request.method == 'POST':
        artikel.title = request.form.get('title')
        artikel.content = request.form.get('content')
        artikel.source_link = request.form.get('source_link')

        if not artikel.title or not artikel.content:
            flash('Judul dan konten artikel wajib diisi!', 'error')
            return redirect(url_for('web.artikel_edit', id=id))

        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file.filename:
                # Hapus thumbnail lama jika ada
                if artikel.thumbnail:
                    old_path = os.path.join('static/uploads/thumbnails', artikel.thumbnail)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # Upload thumbnail baru
                thumbnail, error = save_thumbnail(file)
                if error:
                    flash(error, 'error')
                    return redirect(url_for('web.artikel_edit', id=id))
                artikel.thumbnail = thumbnail

        db.session.commit()
        flash('Artikel berhasil diperbarui!', 'success')
        return redirect(url_for('web.artikel_list'))

    return render_template('admin/article_form.html', artikel=artikel)


@web_routes.route('/admin/artikel/delete/<int:id>')
@admin_login_required
def artikel_delete(id):
    artikel = Article.query.get_or_404(id)

    # Hapus thumbnail fisik jika ada
    if artikel.thumbnail:
        thumbnail_path = os.path.join('static/uploads/thumbnails', artikel.thumbnail)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

    db.session.delete(artikel)
    db.session.commit()
    flash('Artikel berhasil dihapus!', 'success')
    return redirect(url_for('web.artikel_list'))

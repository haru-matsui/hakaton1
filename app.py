from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from functools import wraps
import os
import markdown2
import bleach
from datetime import datetime
from io import BytesIO
from docx import Document
from docx.shared import Inches
import secrets
import imghdr

from models import db, User, Conspectus, ConspectusVersion, Rating, Comment, Favorite, CoAuthor, Report, Tag, Subject
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATARS_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['BASE_DIR'], 'db'), exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def teacher_required(f):
    """Decorator to require teacher role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'teacher':
            flash('Доступ запрещен. Требуются права преподавателя.', 'danger')
            return redirect(url_for('feed'))
        return f(*args, **kwargs)
    return decorated_function


def render_markdown(text):
    """Render markdown text to HTML with sanitization"""
    if not text:
        return ""
    
    # Ensure config values exist
    allowed_tags = getattr(Config, 'ALLOWED_TAGS', [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
        'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br'
    ])
    allowed_attributes = getattr(Config, 'ALLOWED_ATTRIBUTES', {
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title']
    })
    
    html = markdown2.markdown(text, extras=['fenced-code-blocks', 'tables', 'strike', 'task_list'])
    clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
    return clean_html


def validate_image(stream):
    """Validate that uploaded file is a valid image"""
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return format if format in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else None


# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        
        # Validation
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Пароли не совпадают.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов.', 'danger')
            return render_template('register.html')
        
        if role not in ['student', 'teacher']:
            role = 'student'
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует.', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(next_page if next_page else url_for('feed'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('login'))


# Main pages
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))


@app.route('/feed')
@login_required
def feed():
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    
    # Base query: only published, public conspectuses
    query = Conspectus.query.filter_by(is_draft=False, visibility='public')
    
    # Sorting
    if sort_by == 'popular':
        # Sort by number of ratings (simple approximation)
        conspectuses = query.all()
        conspectuses.sort(key=lambda x: x.get_rating(), reverse=True)
        conspectuses = conspectuses[(page-1)*Config.CONSPECTUSES_PER_PAGE:page*Config.CONSPECTUSES_PER_PAGE]
    elif sort_by == 'most_viewed':
        query = query.order_by(Conspectus.views_count.desc())
        conspectuses = query.paginate(page=page, per_page=Config.CONSPECTUSES_PER_PAGE, error_out=False).items
    else:  # newest
        query = query.order_by(Conspectus.created_at.desc())
        conspectuses = query.paginate(page=page, per_page=Config.CONSPECTUSES_PER_PAGE, error_out=False).items
    
    return render_template('feed.html', conspectuses=conspectuses, sort_by=sort_by, page=page)


@app.route('/search')
@login_required
def search():
    query_text = request.args.get('q', '').strip()
    subject_id = request.args.get('subject', type=int)
    tag_name = request.args.get('tag', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Conspectus.query.filter_by(is_draft=False, visibility='public')
    
    if query_text:
        query = query.filter(
            db.or_(
                Conspectus.title.ilike(f'%{query_text}%'),
                Conspectus.content.ilike(f'%{query_text}%')
            )
        )
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    if tag_name:
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag:
            query = query.filter(Conspectus.tags.contains(tag))
    
    conspectuses = query.order_by(Conspectus.created_at.desc()).paginate(
        page=page, per_page=Config.CONSPECTUSES_PER_PAGE, error_out=False
    ).items
    
    subjects = Subject.query.order_by(Subject.name).all()
    tags = Tag.query.order_by(Tag.name).all()
    
    return render_template('search.html', 
                         conspectuses=conspectuses, 
                         query=query_text,
                         subjects=subjects,
                         tags=tags,
                         selected_subject=subject_id,
                         selected_tag=tag_name,
                         page=page)


# User profile
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's conspectuses
    if current_user.id == user.id:
        # Show all own conspectuses including drafts and private
        conspectuses = Conspectus.query.filter_by(author_id=user.id).order_by(Conspectus.created_at.desc()).all()
    else:
        # Show only public published conspectuses
        conspectuses = Conspectus.query.filter_by(
            author_id=user.id, 
            is_draft=False, 
            visibility='public'
        ).order_by(Conspectus.created_at.desc()).all()
    
    return render_template('profile.html', user=user, conspectuses=conspectuses)


@app.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    if current_user.id != user_id:
        flash('Вы можете редактировать только свой профиль.', 'danger')
        return redirect(url_for('profile', user_id=user_id))
    
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        current_user.bio = bio
        
        # Handle avatar upload with validation
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                # Validate file is an image
                if not validate_image(file.stream):
                    flash('Загруженный файл не является изображением.', 'danger')
                    return render_template('edit_profile.html')
                
                # Check file size (already handled by MAX_CONTENT_LENGTH, but double check)
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset
                
                if size > app.config['MAX_CONTENT_LENGTH']:
                    flash('Файл слишком большой. Максимум 16 МБ.', 'danger')
                    return render_template('edit_profile.html')
                
                # Save file
                filename = secure_filename(f"user_{current_user.id}_{secrets.token_hex(8)}.{validate_image(file.stream)}")
                filepath = os.path.join(app.config['AVATARS_FOLDER'], filename)
                file.save(filepath)
                current_user.avatar = filename
        
        db.session.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))
    
    return render_template('edit_profile.html')


# Conspectus CRUD
@app.route('/conspectus/create', methods=['GET', 'POST'])
@login_required
def create_conspectus():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        subject_id = request.form.get('subject_id', type=int)
        tag_names = request.form.get('tags', '').strip()
        visibility = request.form.get('visibility', 'public')
        is_draft = request.form.get('is_draft', 'false') == 'true'
        
        if not title or not content:
            flash('Название и содержание обязательны.', 'danger')
            return render_template('create_conspectus.html', 
                                 subjects=Subject.query.all())
        
        # Create conspectus
        conspectus = Conspectus(
            author_id=current_user.id,
            title=title,
            content=content,
            subject_id=subject_id if subject_id else None,
            visibility=visibility,
            is_draft=is_draft
        )
        
        # Generate share link if visibility is 'link'
        if visibility == 'link':
            conspectus.generate_share_link()
        
        # Handle tags
        if tag_names:
            for tag_name in tag_names.split(','):
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    conspectus.tags.append(tag)
        
        db.session.add(conspectus)
        db.session.commit()
        
        # Create initial version
        version = ConspectusVersion(
            conspectus_id=conspectus.id,
            title=title,
            content=content
        )
        db.session.add(version)
        db.session.commit()
        
        if is_draft:
            flash('Конспект сохранен как черновик.', 'info')
        else:
            flash('Конспект успешно создан!', 'success')
        
        return redirect(url_for('view_conspectus', conspectus_id=conspectus.id))
    
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('create_conspectus.html', subjects=subjects)


@app.route('/conspectus/<int:conspectus_id>')
@login_required
def view_conspectus(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    # Check access permissions
    can_view = False
    
    if conspectus.visibility == 'public' and not conspectus.is_draft:
        can_view = True
    elif conspectus.author_id == current_user.id:
        can_view = True
    elif conspectus.visibility == 'link':
        # Check if user has the share link (from query params)
        share_token = request.args.get('token')
        if share_token == conspectus.share_link or conspectus.author_id == current_user.id:
            can_view = True
    elif current_user.role == 'teacher':
        can_view = True
    
    # Check if user is coauthor
    coauthor = CoAuthor.query.filter_by(
        conspectus_id=conspectus_id,
        user_id=current_user.id
    ).first()
    if coauthor:
        can_view = True
    
    if not can_view:
        flash('У вас нет доступа к этому конспекту.', 'danger')
        return redirect(url_for('feed'))
    
    # Increment views count (only once per session)
    view_key = f'viewed_conspectus_{conspectus_id}'
    if view_key not in session:
        conspectus.views_count += 1
        db.session.commit()
        session[view_key] = True
    
    # Render markdown
    rendered_content = render_markdown(conspectus.content)
    
    # Get comments
    comments = Comment.query.filter_by(
        conspectus_id=conspectus_id,
        parent_comment_id=None
    ).order_by(Comment.created_at.desc()).all()
    
    # Check if user has favorited
    is_favorited = Favorite.query.filter_by(
        user_id=current_user.id,
        conspectus_id=conspectus_id
    ).first() is not None
    
    # Get user's rating
    user_rating = conspectus.user_rating(current_user.id)
    
    return render_template('view_conspectus.html',
                         conspectus=conspectus,
                         rendered_content=rendered_content,
                         comments=comments,
                         is_favorited=is_favorited,
                         user_rating=user_rating,
                         coauthor=coauthor)


@app.route('/conspectus/<int:conspectus_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_conspectus(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    # Check permissions
    can_edit = conspectus.author_id == current_user.id
    if not can_edit:
        coauthor = CoAuthor.query.filter_by(
            conspectus_id=conspectus_id,
            user_id=current_user.id
        ).first()
        if coauthor and coauthor.permission_level in ['edit', 'admin']:
            can_edit = True
    
    if not can_edit:
        flash('У вас нет прав на редактирование этого конспекта.', 'danger')
        return redirect(url_for('view_conspectus', conspectus_id=conspectus_id))
    
    if request.method == 'POST':
        old_title = conspectus.title
        old_content = conspectus.content
        
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        subject_id = request.form.get('subject_id', type=int)
        tag_names = request.form.get('tags', '').strip()
        visibility = request.form.get('visibility', conspectus.visibility)
        is_draft = request.form.get('is_draft', 'false') == 'true'
        
        if not title or not content:
            flash('Название и содержание обязательны.', 'danger')
            return render_template('edit_conspectus.html',
                                 conspectus=conspectus,
                                 subjects=Subject.query.all())
        
        # Save version if content changed
        if title != old_title or content != old_content:
            version = ConspectusVersion(
                conspectus_id=conspectus.id,
                title=old_title,
                content=old_content
            )
            db.session.add(version)
        
        # Update conspectus
        conspectus.title = title
        conspectus.content = content
        conspectus.subject_id = subject_id if subject_id else None
        conspectus.visibility = visibility
        conspectus.is_draft = is_draft
        conspectus.updated_at = datetime.utcnow()
        
        # Generate share link if needed
        if visibility == 'link' and not conspectus.share_link:
            conspectus.generate_share_link()
        
        # Update tags
        conspectus.tags.clear()
        if tag_names:
            for tag_name in tag_names.split(','):
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    conspectus.tags.append(tag)
        
        db.session.commit()
        flash('Конспект успешно обновлен!', 'success')
        return redirect(url_for('view_conspectus', conspectus_id=conspectus_id))
    
    subjects = Subject.query.order_by(Subject.name).all()
    tag_names = ', '.join([tag.name for tag in conspectus.tags])
    
    return render_template('edit_conspectus.html',
                         conspectus=conspectus,
                         subjects=subjects,
                         tag_names=tag_names)


@app.route('/conspectus/<int:conspectus_id>/delete', methods=['POST'])
@login_required
def delete_conspectus(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    if conspectus.author_id != current_user.id and current_user.role != 'teacher':
        flash('У вас нет прав на удаление этого конспекта.', 'danger')
        return redirect(url_for('view_conspectus', conspectus_id=conspectus_id))
    
    db.session.delete(conspectus)
    db.session.commit()
    
    flash('Конспект успешно удален.', 'success')
    return redirect(url_for('feed'))


@app.route('/conspectus/<int:conspectus_id>/versions')
@login_required
def conspectus_versions(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    # Check permissions
    if conspectus.author_id != current_user.id and current_user.role != 'teacher':
        flash('У вас нет доступа к истории версий.', 'danger')
        return redirect(url_for('view_conspectus', conspectus_id=conspectus_id))
    
    versions = conspectus.versions
    
    return render_template('conspectus_versions.html',
                         conspectus=conspectus,
                         versions=versions)


# Rating API
@app.route('/api/conspectus/<int:conspectus_id>/rate', methods=['POST'])
@login_required
def rate_conspectus(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    vote = request.json.get('vote', 0)
    
    if vote not in [-1, 1]:
        return jsonify({'error': 'Invalid vote value'}), 400
    
    # Check existing rating
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id,
        conspectus_id=conspectus_id
    ).first()
    
    if existing_rating:
        if existing_rating.vote == vote:
            # Remove rating (toggle off)
            db.session.delete(existing_rating)
            db.session.commit()
            return jsonify({
                'success': True,
                'action': 'removed',
                'rating': conspectus.get_rating(),
                'likes': conspectus.get_likes_count(),
                'dislikes': conspectus.get_dislikes_count()
            })
        else:
            # Update rating
            existing_rating.vote = vote
            db.session.commit()
            return jsonify({
                'success': True,
                'action': 'updated',
                'rating': conspectus.get_rating(),
                'likes': conspectus.get_likes_count(),
                'dislikes': conspectus.get_dislikes_count()
            })
    else:
        # Create new rating
        rating = Rating(
            user_id=current_user.id,
            conspectus_id=conspectus_id,
            vote=vote
        )
        db.session.add(rating)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'created',
            'rating': conspectus.get_rating(),
            'likes': conspectus.get_likes_count(),
            'dislikes': conspectus.get_dislikes_count()
        })


# Comments API
@app.route('/api/conspectus/<int:conspectus_id>/comment', methods=['POST'])
@login_required
def add_comment(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    text = request.json.get('text', '').strip()
    parent_id = request.json.get('parent_id', type=int)
    
    if not text:
        return jsonify({'error': 'Comment text is required'}), 400
    
    is_author_reply = conspectus.author_id == current_user.id
    
    comment = Comment(
        user_id=current_user.id,
        conspectus_id=conspectus_id,
        parent_comment_id=parent_id,
        text=text,
        is_author_reply=is_author_reply
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'avatar': current_user.avatar
            },
            'text': comment.text,
            'is_author_reply': comment.is_author_reply,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
        }
    })


@app.route('/api/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check permissions
    can_delete = comment.user_id == current_user.id or current_user.role == 'teacher'
    if not can_delete:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True})


# Favorites
@app.route('/favorites')
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    conspectuses = [f.conspectus for f in favorites]
    
    return render_template('favorites.html', conspectuses=conspectuses)


@app.route('/api/conspectus/<int:conspectus_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    existing = Favorite.query.filter_by(
        user_id=current_user.id,
        conspectus_id=conspectus_id
    ).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        favorite = Favorite(
            user_id=current_user.id,
            conspectus_id=conspectus_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})


# Export functions
@app.route('/conspectus/<int:conspectus_id>/export/markdown')
@login_required
def export_markdown(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    # Check access
    can_access = (conspectus.visibility == 'public' and not conspectus.is_draft) or \
                 conspectus.author_id == current_user.id or \
                 current_user.role == 'teacher'
    
    if not can_access:
        flash('У вас нет доступа к этому конспекту.', 'danger')
        return redirect(url_for('feed'))
    
    # Increment download count
    conspectus.downloads_count += 1
    db.session.commit()
    
    # Create markdown file
    content = f"# {conspectus.title}\n\n"
    content += f"**Автор:** {conspectus.author.username}\n"
    content += f"**Дата создания:** {conspectus.created_at.strftime('%d.%m.%Y')}\n\n"
    content += "---\n\n"
    content += conspectus.content
    
    # Send file
    return send_file(
        BytesIO(content.encode('utf-8')),
        as_attachment=True,
        download_name=f"{conspectus.title}.md",
        mimetype='text/markdown'
    )


@app.route('/conspectus/<int:conspectus_id>/export/docx')
@login_required
def export_docx(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    
    # Check access
    can_access = (conspectus.visibility == 'public' and not conspectus.is_draft) or \
                 conspectus.author_id == current_user.id or \
                 current_user.role == 'teacher'
    
    if not can_access:
        flash('У вас нет доступа к этому конспекту.', 'danger')
        return redirect(url_for('feed'))
    
    # Increment download count
    conspectus.downloads_count += 1
    db.session.commit()
    
    # Create DOCX file
    document = Document()
    document.add_heading(conspectus.title, 0)
    document.add_paragraph(f"Автор: {conspectus.author.username}")
    document.add_paragraph(f"Дата создания: {conspectus.created_at.strftime('%d.%m.%Y')}")
    document.add_paragraph()
    document.add_paragraph(conspectus.content)
    
    # Save to BytesIO
    file_stream = BytesIO()
    document.save(file_stream)
    file_stream.seek(0)
    
    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f"{conspectus.title}.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# Moderation (teachers only)
@app.route('/moderation')
@teacher_required
def moderation():
    reports = Report.query.filter_by(status='pending').order_by(Report.created_at.desc()).all()
    return render_template('moderation.html', reports=reports)


@app.route('/api/report/<int:report_id>/resolve', methods=['POST'])
@teacher_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    action = request.json.get('action', 'resolve')
    
    if action == 'delete':
        # Delete the conspectus
        conspectus = report.conspectus
        db.session.delete(conspectus)
        report.status = 'resolved'
    else:
        report.status = 'reviewed'
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/conspectus/<int:conspectus_id>/report', methods=['POST'])
@login_required
def report_conspectus(conspectus_id):
    conspectus = Conspectus.query.get_or_404(conspectus_id)
    reason = request.json.get('reason', '').strip()
    
    if not reason:
        return jsonify({'error': 'Reason is required'}), 400
    
    # Check if already reported
    existing = Report.query.filter_by(
        user_id=current_user.id,
        conspectus_id=conspectus_id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'error': 'You already reported this conspectus'}), 400
    
    report = Report(
        user_id=current_user.id,
        conspectus_id=conspectus_id,
        reason=reason
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'success': True})


# Initialize database
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')
    
    # Create some default subjects
    default_subjects = [
        'Математика', 'Физика', 'Химия', 'Биология', 'История',
        'Литература', 'Информатика', 'Английский язык', 'Философия',
        'Экономика', 'Психология', 'Социология'
    ]
    
    for subject_name in default_subjects:
        if not Subject.query.filter_by(name=subject_name).first():
            subject = Subject(name=subject_name)
            db.session.add(subject)
    
    db.session.commit()
    print('Default subjects created!')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

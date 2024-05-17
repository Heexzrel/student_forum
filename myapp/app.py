#main codes to run the application

from flask import Flask, flash, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES, configure_uploads
from models import User

#Flask application instance
app = Flask(__name__)

# Configuration settings
app.config.update(
    SECRET_KEY='opeYEMIisy1',  
    SQLALCHEMY_DATABASE_URI='sqlite:///student_forum.db',
    TEMPLATES_AUTO_RELOAD=True
    UPLOADED_PHOTOS_DEST='uploads/photos'
    )

#database
db = SQLAlchemy(app)

# Login Manager configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirects to login view on unauthorized access

#Flask-Login (how to load users)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Flask uploads config
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)


#displays content for the root path
@app.route('/templates')
def index():
        return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))  # Redirect to profile if already logged in
    
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.verify_password(request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password.', 'error')  # Flash error message           
    return render_template('login.html')


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
    
        # Check for existing user
        existing_user = User.query.filter_any(email=email, username=username).first()
        if existing_user:
            if existing_user.email == email:
                flash('Email address already in use.', 'error')
            elif existing_user.username == username:
                flash('Username already in use.', 'error')
        else:
            #hash password and create user
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))
    return render_template('register.html')


# Profile (require the user to login)
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# route for password reset
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            token = user.get_reset_token()
            flash(f"An email has been sent to {user.email} with instructions to reset your password.", 'info')
        else:
            flash('Email address not found.', 'error')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html')


# route for password reset token
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user.set_password(request.form['password'])
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')


# route for uploading profile picture
@app.route('/upload_picture', methods=['GET', 'POST'])
def upload_picture():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        user = user.query.filter_by(id=current_user.id).first()
        current_user.profile_picture = filename
        db.session.commit()
        flash('Profile picture uploaded.', 'success')
        return redirect(url_for('profile'))
    return render_template('upload_picture.html')

# Logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#development server for running the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables (if it's not available)
        app.run(debug=True)

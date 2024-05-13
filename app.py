#main codes to run the application

from flask import Flask, flash, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

#Flask application instance
app = Flask(__name__)

# Configuration settings
# app.config.update(
#     SECRET_KEY='your_strong_secret_key',  
#     SQLALCHEMY_DATABASE_URI='sqlite:///student_forum.db'  
# )

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


# Login 
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


# Registration
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
        return render_template('register.html')

# Hash password and create user
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

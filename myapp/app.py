#main codes to run the application

from flask import Flask, flash, jsonify, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_mail import Mail, Message
from flask_cors import CORS
from models import User, Note

#Flask application instance
app = Flask(__name__)
CORS(app)

# Configuration settings
app.config.update(
    SECRET_KEY='opeYEMIisy1',  
    SQLALCHEMY_DATABASE_URI='sqlite:///student_forum.db',
    TEMPLATES_AUTO_RELOAD=True,
    UPLOADED_PHOTOS_DEST='uploads/photos',
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='georgeisrael18@gmail.com',
    MAIL_PASSWORD='opeYEMIisy1'
)

#database
db = SQLAlchemy(app)

# mail config
mail = Mail(app)

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



# Password reset email fuction
def send_password_reset_email(user, token):
    subject = 'Request Your Password'
    sender = 'noreply@demo.com'
    recipient = user.email
    mail_body = f'''To reset your password, click on the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request, ignore this email.
'''
    message = Message(subject, sender=sender, recipients=[recipient])
    message.body = mail_body
    mail.send(message)


# displays content for the root path
@app.route('/', methods=['GET'])
def index():
    data = {
        "message": "Welcome to the Smart Student!"
    } 
    return jsonify(data)


# Login route
@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({
            "message": "You are already logged in.",
            "redirect": url_for('profile')
        })
           
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"message": "Email and password are required."})
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(User.password_hash, password):
        login_user(User, remember=True)
        return jsonify({
            "message": "Login successful.",
            "redirect": url_for('profile')})
    else:
        return jsonify({"message": "Invalid username or password."})
    

# Registration route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    if not email or not username or not password:
        return jsonify({"message": "All fields are required."})
    
    # Check for existing user
    existing_user = User.query.filter((User.email == email) | (User.username == username))
    if existing_user:
        return jsonify({"message": "User already exists."})
    
    # Hash password and create user
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Registration successful! Please login.",
        "redirect": url_for('login')
        })



# Profile (require the user to login)
@app.route('/profile')
@login_required
def profile():
    return jsonify({
        "message": "Welcome to your profile.",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "profile_picture": current_user.profile_picture
        }
    })


# route for password reset
@app.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"message": "Email is required."})
    
    user = User.query.filter_by(email=email).first()
    if user:
        token = user.get_reset_token()
        send_password_reset_email(user, token)
        return jsonify({"message": f"An email has been sent to {user.email} with instructions to reset your password."})
    else:
        return jsonify({"message": "Email address not found."})


# route for password reset token
@app.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return jsonify({"message": "You are already logged in."})

    user = User.verify_reset_token(token)
    if not user:
        return jsonify({"message": "Invalid or expired token."})

    data = request.get_json()
    password = data.get('password')
    if not password:
        return jsonify({"message": "Invalid password."})    

    user.set_password(password)
    db.session.commit()
    return jsonify({"message": "Your password has been reset successfully."})


# route for uploading profile picture
@app.route('/upload_picture', methods=['POST'])
def upload_picture():
    if 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        user = User.query.filter_by(id=current_user.id).first()
        current_user.profile_picture = filename
        db.session.commit()
        return jsonify({"message": "Profile picture uploaded successfully."})
    else:
        return jsonify({"message": "No file selected."})
 

# Logout 
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully."})


@app.route('/note/create', methods=['POST'])
@login_required
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    if not title or not content:
        return jsonify({"message": "Title and content are required."})
    
    new_note = Note(title=title, content=content, user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()
    return jsonify({"message": "Note created successfully."})


@app.route('/note/<int:note_id>', methods=['GET'])
@login_required
def view_note(note_id):
    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        return jsonify({
            "id": note.id,
            "title": note.title,
            "content": note.content,
        })
    else:
        return jsonify({"message": "Note not found."})
    

@app.route('/note/<int:note_id>/edit', methods=['PUT'])
@login_required
def edit_note(note_id):
    note = Note.query.get(note_id)
    if note and note.user_id != current_user.id:
        return jsonify({"message": "You are not authorized to edit this note."})
    
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({"message": "Content is required."})
    
    note.content = content
    db.session.commit()
    return jsonify({"message": "Note updated successfully."})


@app.route('/note/<int:note_id>/delete', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note and note.user_id != current_user.id:
        return jsonify({"message": "You are not authorized to delete this note."})

    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted successfully."})

#development server for running the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables (if it's not available)
        app.run(debug=True)


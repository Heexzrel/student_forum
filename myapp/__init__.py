# __init__.py
from flask import Flask, request, redirect, url_for
from flask_security import Security, SQLAlchemyUserDatastore
from .models import db, User, Role


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

    db.init_app(app)

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            user = User(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('security.login'))
        return render_template('register.html')

    return app

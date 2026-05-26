from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from argon2 import PasswordHasher, exceptions
import pyotp
import qrcode
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-with-a-strong-secret'

# Database (SQLite)
engine = create_engine('sqlite:///instance/secure_login.db', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

ph = PasswordHasher()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    two_factor_secret = Column(String(64), nullable=True)
    two_factor_enabled = Column(Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    return db.query(User).get(int(user_id))


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db = SessionLocal()
        existing = db.query(User).filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing:
            flash('Username or email already exists', 'danger')
            return render_template('register.html', form=form)
        hash = ph.hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hash)
        db.add(user)
        db.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = SessionLocal()
        user = db.query(User).filter(User.username == form.username.data).first()
        if not user:
            flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form)
        try:
            ph.verify(user.password_hash, form.password.data)
        except exceptions.VerifyMismatchError:
            flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form)
        # If 2FA enabled, keep user id in session and ask for token
        if user.two_factor_enabled:
            session['pre_2fa_user_id'] = user.id
            return redirect(url_for('two_factor'))
        login_user(user, remember=form.remember.data)
        flash('Logged in successfully', 'success')
        return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route('/two-factor', methods=['GET', 'POST'])
def two_factor():
    # Verify TOTP token
    if request.method == 'POST':
        token = request.form.get('token')
        user_id = session.get('pre_2fa_user_id')
        if not user_id:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        db = SessionLocal()
        user = db.query(User).get(user_id)
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(token):
            login_user(user)
            session.pop('pre_2fa_user_id', None)
            flash('2FA verified, logged in', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid 2FA token', 'danger')
    return render_template('two_factor.html')


@app.route('/enable-2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    db = SessionLocal()
    user = db.query(User).get(current_user.id)
    if not user.two_factor_secret:
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        db.add(user)
        db.commit()
    else:
        secret = user.two_factor_secret
    # Generate provisioning URI
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="SecureLoginApp")
    # Generate QR code PNG as data URI
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    img_b64 = 'data:image/png;base64,' + (buf.getvalue()).hex()
    # Note: hex used for portability; template can render via separate endpoint
    return render_template('enable_2fa.html', secret=secret)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Create tables if missing
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)

from flask import render_template, url_for, flash, redirect, request
from auth import auth
from models.user import User
from models.setting import Setting
from extensions import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta, timezone
from utils.email_service import generate_otp, send_verification_email

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash('Email or username already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        otp = generate_otp()
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        user = User(
            full_name=full_name, 
            username=username, 
            email=email, 
            password_hash=hashed_password,
            otp_code=otp,
            otp_expiry=expiry
        )
        db.session.add(user)
        db.session.commit()
        
        # Create default settings
        setting = Setting(user_id=user.id)
        db.session.add(setting)
        db.session.commit()
        
        # Send email
        send_verification_email(user.email, otp)
        
        flash('Account created! Please check your email for the verification code.', 'info')
        return redirect(url_for('auth.verify', user_id=user.id))
        
    return render_template('auth/register.html', title='Register')

@auth.route("/verify/<int:user_id>", methods=['GET', 'POST'])
def verify(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_verified:
        flash('Account is already verified. You can log in.', 'info')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        if not user.otp_expiry or datetime.now(timezone.utc) > user.otp_expiry:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.verify', user_id=user.id))
            
        if otp_input == user.otp_code:
            user.is_verified = True
            user.otp_code = None
            user.otp_expiry = None
            db.session.commit()
            flash('Your account has been verified! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP code. Please try again.', 'danger')
            
    return render_template('auth/verify.html', title='Verify Account', user=user)

@auth.route("/resend-otp/<int:user_id>")
def resend_otp(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_verified:
        return redirect(url_for('auth.login'))
        
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.session.commit()
    
    send_verification_email(user.email, otp)
    flash('A new verification code has been sent to your email.', 'info')
    return redirect(url_for('auth.verify', user_id=user.id))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.verify', user_id=user.id))
                
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login')

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db, login_manager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Check if any user exists. If not, redirect to setup
    if not User.query.first():
        return redirect(url_for('auth.setup_admin'))
        
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_expired:
                flash('Your account has expired.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            # Log login action (todo)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    if User.query.first():
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        username = request.form.get('username') # Email
        password = request.form.get('password')
        
        if username and password:
            admin = User(username=username, role='super_admin')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            flash('Super Admin created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/setup_admin.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

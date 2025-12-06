from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = UserService.get_user_by_email(email)
        
        if user and UserService.verify_password(user, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password')
            
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        existing_user = UserService.get_user_by_email(email)
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('auth.signup'))
            
        UserService.create_user(email, password, first_name, last_name)
        flash('Account created successfully. Please log in.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

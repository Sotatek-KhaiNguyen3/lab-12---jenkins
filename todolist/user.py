from math import e
from string import Template
from flask import Blueprint, render_template, request, flash, session
from flask.helpers import url_for
from sqlalchemy.sql.expression import false
from werkzeug.utils import redirect
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from todolist import views
from .models import User, Note

from . import db

user = Blueprint("user", __name__)


@user.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                session.permanent = True
                login_user(user, remember=True)
                flash("Logged in success!", category="success")
                return redirect(url_for("views.home"))
            else:
                flash("Wrong password, please check again!", category="error")
        else:
            flash("User doesn't exist!", category="error")
    return render_template("login.html", user=current_user)


@user.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        user = User.query.filter_by(email=email).first()
        # validate user
        if user:
            flash("User existed!", category="error")
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category="error")
        elif len(password) < 7:
            flash("Email must be greater than 7 characters.", category="error")
        elif password != confirm_password:
            flash("Password doesn not match!", category="error")
        else:
            password = generate_password_hash(password)  # Sử dụng phương thức mặc định (pbkdf2:sha256)
            new_user = User(email, password, user_name)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash("User created!", category="success")
                # Log in the newly created user (was previously logging in the old `user` variable)
                login_user(new_user, remember=True)
                return redirect(url_for("views.home"))
            except Exception as e:
                # keep minimal error handling and surface the message for debugging
                flash(f"Error when create user: {e}", category="error")
    return render_template("signup.html", user=current_user)


@user.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("user.login"))


@user.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', category='error')
            return render_template('change_password.html', user=current_user)

        # Validate new password
        if len(new_password) < 7:
            flash('New password must be at least 7 characters long.', category='error')
            return render_template('change_password.html', user=current_user)

        if new_password != confirm_password:
            flash('New password and confirmation do not match.', category='error')
            return render_template('change_password.html', user=current_user)

        # Update password
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully.', category='success')
        return redirect(url_for('views.home'))

    return render_template('change_password.html', user=current_user)

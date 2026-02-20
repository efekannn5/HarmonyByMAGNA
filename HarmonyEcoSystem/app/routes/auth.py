from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from ..extensions import db
from ..models import UserAccount
from ..services.audit_service import AuditService
from ..utils.security import hash_password

auth_bp = Blueprint("auth", __name__)
audit_service = AuditService()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_home"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = UserAccount.query.filter_by(Username=username, IsActive=True).first()
        if not user or not check_password_hash(user.PasswordHash, password):
            error = "Kullanıcı adı veya şifre hatalı."
        else:
            login_user(user)
            user.LastLoginAt = db.func.now()
            db.session.commit()
            audit_service.log(
                action="auth.login",
                resource="user",
                resource_id=str(user.Id),
                actor_user=user,
            )
            return redirect(url_for("dashboard.dashboard_home"))
    return render_template("auth/login.html", error=error, title="Giriş")


@auth_bp.route("/logout")
@login_required
def logout():
    audit_service.log(
        action="auth.logout",
        resource="user",
        resource_id=str(current_user.Id),
        actor_user=current_user,
    )
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    message = None
    error = None
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not check_password_hash(current_user.PasswordHash, current_pw):
            error = "Mevcut şifre yanlış."
        elif len(new_pw) < 8:
            error = "Yeni şifre en az 8 karakter olmalı."
        elif new_pw != confirm:
            error = "Şifre doğrulaması eşleşmiyor."
        else:
            current_user.PasswordHash = hash_password(new_pw)
            db.session.commit()
            audit_service.log(
                action="auth.password_change",
                resource="user",
                resource_id=str(current_user.Id),
                actor_user=current_user,
            )
            message = "Şifre güncellendi."
    return render_template(
        "auth/password.html",
        error=error,
        message=message,
        title="Şifre Değiştir",
    )

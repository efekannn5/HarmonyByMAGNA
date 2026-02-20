"""
Analytics Dashboard Routes
===========================
Web interface for analytics dashboard.
Provides views for executives and managers.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app.models.user import UserAccount


analytics_dashboard_bp = Blueprint(
    "analytics_dashboard",
    __name__,
    url_prefix="/analytics"
)


@analytics_dashboard_bp.route("/")
@login_required
def index():
    """Main analytics dashboard page."""
    return render_template(
        "dashboard.html",
        title="Analytics Dashboard",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page for analytics dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("analytics_dashboard.index"))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please provide both username and password", "error")
            return render_template("login.html")
        
        user = UserAccount.query.filter_by(Username=username, IsActive=True).first()
        
        if user and check_password_hash(user.PasswordHash, password):
            # Check if user has admin or manager role
            if user.role and user.role.Name.lower() in ["admin", "administrator", "manager"]:
                login_user(user)
                next_page = request.args.get("next")
                return redirect(next_page or url_for("analytics_dashboard.index"))
            else:
                flash("Access denied. Analytics dashboard is for managers only.", "error")
        else:
            flash("Invalid username or password", "error")
    
    return render_template("login.html")


@analytics_dashboard_bp.route("/logout")
@login_required
def logout():
    """Logout from analytics dashboard."""
    logout_user()
    return redirect(url_for("analytics_dashboard.login"))


@analytics_dashboard_bp.route("/timeline")
@login_required
def timeline():
    """Timeline and trend analysis page."""
    return render_template(
        "timeline.html",
        title="Timeline Analysis",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/lines")
@login_required
def lines():
    """Production line performance page."""
    return render_template(
        "lines.html",
        title="Line Performance",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/process")
@login_required
def process():
    """Line process analytics page."""
    return render_template(
        "process.html",
        title="Process Analysis",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/operators")
@login_required
def operators():
    """Operator performance page."""
    return render_template(
        "operators.html",
        title="Operator Performance",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/bottlenecks")
@login_required
def bottlenecks():
    """Bottleneck detection and alerts page."""
    return render_template(
        "bottlenecks.html",
        title="Bottlenecks & Alerts",
        current_user=current_user
    )


@analytics_dashboard_bp.route("/reports")
@login_required
def reports():
    """Historical reports page."""
    return render_template(
        "reports.html",
        title="Reports",
        current_user=current_user
    )

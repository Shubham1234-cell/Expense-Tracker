from flask import render_template, redirect, url_for, flash, request
from admin import admin
from models.user import User
from models.transaction import Transaction
from extensions import db
from flask_login import login_required, current_user

def admin_required(f):
    def wrap(*args, **kwargs):
        if not current_user.is_admin:
            flash("You need to be an admin to view this page.", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@admin.route("/")
@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    total_users = len(users)
    total_transactions = Transaction.query.count()
    return render_template('admin/dashboard.html', title='Admin Dashboard', users=users, total_users=total_users, total_transactions=total_transactions)

@admin.route("/user/<int:user_id>/delete", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for('admin.dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

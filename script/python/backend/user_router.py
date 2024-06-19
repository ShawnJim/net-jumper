from datetime import date

from flask import Blueprint, current_app, jsonify, request, render_template, redirect, url_for
from db.db_manager import NodeDBManager, VnstatInfoDBManager, UserManager
from utils import login_required, get_refresh_day

# 创建一个Blueprint实例
user_router = Blueprint('user_router', __name__)


@user_router.route('/user_index')
@login_required
def index():
    with current_app.app_context():
        db_file = current_app.config['db_file']
    users = UserManager.select_all(db_file)
    return render_template('user_index.html', users=users)


@user_router.route('/user/<ip>', methods=['GET'])
@login_required
def get_user(ip):
    with current_app.app_context():
        db_file = current_app.config['db_file']
        user = UserManager.select_by_ip(db_file, ip)
        return render_template('user.html', user=user)


@user_router.route('/update_user', methods=['POST'])
@login_required
def update_user():
    with current_app.app_context():
        db_file = current_app.config['db_file']
    ip = request.form['ip']
    remark = request.form['remark']
    client_type = request.form['type']
    UserManager.save_or_update(db_file, ip, remark, client_type)
    return redirect(url_for('user_router.index'))

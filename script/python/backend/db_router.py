from flask import Blueprint, current_app, jsonify, request, render_template, redirect, url_for
from db.db_manager import NodeDBManager, VnstatInfoDBManager
from utils import login_required

# 创建一个Blueprint实例
db_router = Blueprint('db_router', __name__)


@db_router.route('/insert', methods=['POST'])  # 指定方法为POST，以接收JSON数据
@login_required
def insert():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        # 获取JSON数据
        record = request.json  # 假设客户端发送的是JSON格式的数据
        if not record:
            return jsonify({"error": "No JSON data provided"}), 400  # 如果没有数据或不是JSON格式，返回错误
    # 使用提取的数据调用DBManager的insert方法
    NodeDBManager.insert(db_file, record)
    return jsonify({"message": "Record inserted successfully"}), 200  # 返回成功消息和状态码


@db_router.route('/delete', methods=['GET'])  # 使用GET方法
@login_required
def delete():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        # 从URL查询参数中获取name
        name = request.args.get('name')
        if not name:
            return jsonify({"error": "Error: No name provided"}), 400  # 如果没有数据或不是JSON格式，返回错误

        NodeDBManager.delete(db_file, name)
        resp = redirect(url_for("db_index"))
        return resp


@db_router.route('/add', methods=['GET', 'POST'])
@login_required
def add_record():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        if request.method == 'POST':
            record = {
                'name': request.form['name'],
                'server': request.form['server'],
                'port': request.form['port'],
                'uuid': request.form['uuid'],
                'endpoint': request.form['endpoint'],
                'threshold': request.form['threshold']
            }
            NodeDBManager.insert(db_file, record)
            resp = redirect(url_for("db_index"))
            return resp
        return render_template('add_record.html')


@db_router.route('/update/<string:name>', methods=['GET', 'POST'])
@login_required
def update_record(name):
    with current_app.app_context():
        db_file = current_app.config['db_file']
        if request.method == 'POST':
            updated_record = {
                'name': request.form['name'],
                'server': request.form['server'],
                'port': request.form['port'],
                'uuid': request.form['uuid'],
                'endpoint': request.form['endpoint'],
                'threshold': request.form['threshold']
            }
            NodeDBManager.update(db_file, name, updated_record)
            resp = redirect(url_for("db_index"))
            return resp
        record = NodeDBManager.select_by_name(db_file, name)
        return render_template('update_record.html', record=record)


@db_router.route('/vnstat/report', methods=['POST'])
def vnstat_report():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        updated_record = {
            'name': request.json['name'],
            'day': request.json['day'],
            'rx': request.json['rx'],
            'tx': request.json['tx'],
            'total': request.json['total']
        }
        VnstatInfoDBManager.refresh_record(db_file, updated_record)
        VnstatInfoDBManager.delete_old_records(db_file)
        return jsonify({"success": "data reported"}), 200

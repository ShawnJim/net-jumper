from datetime import date

from flask import Blueprint, current_app, jsonify, request, render_template, redirect, url_for
from db.db_manager import NodeDBManager, VnstatInfoDBManager
from utils import login_required, get_refresh_day

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
                'threshold': request.form['threshold'],
                'total_amount_flow': request.form['total_amount_flow'],
                'net_refresh_date': request.form['net_refresh_date']
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
                'threshold': request.form['threshold'],
                'net_refresh_date': request.form['net_refresh_date'],
                'total_amount_flow': request.form['total_amount_flow']
            }
            NodeDBManager.update(db_file, name, updated_record)
            resp = redirect(url_for("db_index"))
            return resp
        record = NodeDBManager.select_by_name(db_file, name)
        return render_template('update_record.html', record=record)

@db_router.route('/vnstat/threshold/<string:name>/get', methods=['get'])
def vnstat_get_threshold(name):
    with current_app.app_context():
        db_file = current_app.config['db_file']
        node = NodeDBManager.select_by_name(db_file, name)
        return str(node['threshold']), 200


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

        # 刷新每日阈值
        # 获取节点刷新日志
        node = NodeDBManager.select_by_name(db_file, updated_record['name'])
        node = calculate_threshold(node, db_file, date.today())
        NodeDBManager.update(db_file, updated_record['name'], node)

        return jsonify({"success": "data reported"}), 200


def calculate_threshold(node, db_file, today):
    """
    计算节点剩余天数每天的阈值
    计算：(总流量 - 今日之前的流量)
    :param node:
    :param db_file:
    :param today:
    :return:
    """
    node_name = node['name']
    net_refresh_date = node['net_refresh_date']
    total_amount_flow = node['total_amount_flow']
    start_refresh_day = get_refresh_day(net_refresh_date, today)
    if net_refresh_date == today:
        node['threshold'] = int(total_amount_flow - VnstatInfoDBManager.select_by_today(db_file, node_name, today))
    else:
        node['threshold'] = int(total_amount_flow -
                                VnstatInfoDBManager.select_by_day_between(
                                    db_file, node_name, f'{start_refresh_day}', today))
    return node



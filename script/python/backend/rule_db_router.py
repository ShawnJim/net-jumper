from flask import Blueprint, current_app, jsonify, request, render_template, redirect, url_for
from db.db_manager import V2rayRuleDBManager
from utils import login_required

# 创建一个Blueprint实例
rule_db_router = Blueprint('rule_db_router', __name__)


@rule_db_router.route('/rule/add', methods=['GET', 'POST'])  # 指定方法为POST，以接收JSON数据
@login_required
def add():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        if request.method == 'POST':
            rule = request.form['rule']
            rule = rule.replace(" ", "").replace("\t", "")
            V2rayRuleDBManager.insert(db_file, rule)
            resp = redirect(url_for("db_index"))
            return resp
    return render_template('add_rule.html')


@rule_db_router.route('/rule/delete', methods=['GET'])  # 使用GET方法
@login_required
def delete():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        # 从URL查询参数中获取name
        rule = request.args.get('rule')
        if not rule:
            return jsonify({"error": "Error: No rule provided"}), 400  # 如果没有数据或不是JSON格式，返回错误

        V2rayRuleDBManager.delete(db_file, rule)
        resp = redirect(url_for("db_index"))
        return resp


@rule_db_router.route('/rule/update/<string:rule>', methods=['GET', 'POST'])
@login_required
def update_record(rule):
    with current_app.app_context():
        db_file = current_app.config['db_file']
        if request.method == 'POST':
            V2rayRuleDBManager.update(db_file, rule, request.form['rule'])
            resp = redirect(url_for("db_index"))
            return resp
        return render_template('update_rule.html', rule=rule)


@rule_db_router.route('/rule/delete_all', methods=['GET'])
@login_required
def delete_all():
    with current_app.app_context():
        db_file = current_app.config['db_file']
        V2rayRuleDBManager.delete_all(db_file)
        return jsonify({"success": "delete is done"}), 200

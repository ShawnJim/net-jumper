#!/bin/env python
# _*_coding:utf-8_*_
import base64
import os
import sys
from io import BytesIO

import requests
import yaml
from flask import *

from db.db_manager import IpRecorderManager, VnstatInfoDBManager, V2rayRuleDBManager, NodeDBManager
from db_router import db_router
from rule_db_router import rule_db_router
from user_router import user_router
from template import CFW
from utils import validate_user, login_required

app = Flask(__name__)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if validate_user(username, password):
            # 登录成功，设置 cookie
            resp = redirect(url_for("index"))
            resp.set_cookie("username", username)
            resp.set_cookie("password", password)
            return resp
        else:
            return "登录失败，用户名或密码错误"

    return render_template("login.html")


@app.route("/logout")
def logout():
    # 清除 cookie 并重定向到登录页面
    resp = redirect(url_for("login"))
    resp.delete_cookie("username")
    resp.delete_cookie("password")
    return resp


@app.route('/refresh', methods=['POST'])
@login_required
def refresh():
    name = request.form.get('name')
    node = node_db_manager.select_by_name(db_file, name)
    curl_address = f"https://{node['server']}/refresh_exec"
    res = requests.get(curl_address)
    if res.status_code == 200:
        if res.text == "success":
            return 'success'
        else:
            return 'error, 调用远程刷新接口成功，接口返回失败'
    else:
        return 'error, 调用远程刷新接口失败'


@app.route('/refresh_exec')
def refresh_exec():
    output = os.popen(refresh_script).read()
    print(output)
    return_code = os.popen('echo $?').read().strip()
    # 判断命令是否执行成功
    if return_code == '0':
        return 'success'
    else:
        return 'error'


@app.route('/vmess2cfw')
def vmess2cfw():
    # 记录请求ip
    record_req_ip("cfw")
    # 创建一个响应对象
    response = make_response(transform_yaml_to_dict())
    # 添加自定义头部
    try:
        use_net_info = vnstat_db_manager.select_total_for_day(db_file)
        rx = gib_to_bits(use_net_info['rx'])
        tx = gib_to_bits(use_net_info['tx'])
        threshold = gib_to_bits(node_db_manager.select_total_threshold(db_file)[0])
        response.headers['Subscription-Userinfo'] = f'upload={rx}; download={tx}; total={threshold}; expire=0'
    except Exception as e:
        print(e)
    return response


def record_req_ip(client_type):
    # 获取客户端 IP 地址
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    ip_recorder_manager.save_or_update(db_file, ip, client_type)


def gib_to_bits(gib):
    return gib * 2**30

def to_v2ray_txt():
    proxy_list = node_db_manager.select(db_file)
    vmess_group = []
    # 添加自定义头部
    use_net_info = vnstat_db_manager.select_total_for_day(db_file)
    use_total = use_net_info['total']
    threshold = node_db_manager.select_total_threshold(db_file)[0]
    vmess_group.append(f"STATUS=当月流量: {use_total}Gib / {threshold}Gib")
    for proxy in proxy_list:
        vmess_dict = {
            "ps": proxy['name'],
            "add": proxy['server'],
            "port": proxy['port'],
            "id": proxy['uuid'],
            "aid": "0",
            "scy": "none",
            "net": "ws",
            "type": "",
            "host": "",
            "path": proxy['endpoint'],
            "tls": "tls",
            "allowInsecure": False,
            "v": "2",
            "protocol": "vmess"
        }
        vmess_str = f'vmess://{base64.b64encode(json.dumps(vmess_dict).encode()).decode()}'
        vmess_group.append(vmess_str)
    final_vmess = base64.b64encode("\n".join(vmess_group).encode()).decode()  # 编码为字符串
    return final_vmess


@app.route('/vmess2general')
def download_file():
    record_req_ip("v2ray")
    vmess2general = to_v2ray_txt()
    file_object = BytesIO()
    file_object.write(vmess2general.encode('utf-8'))
    file_object.seek(0)
    return send_file(file_object, as_attachment=True, download_name='vmess2general.txt', mimetype='text/txt')


def transform_yaml_to_dict():
    # 将 YAML 格式的字符串转换为字典
    config = yaml.safe_load(CFW)
    # 检查 'proxies' 是否存在并且是一个列表
    if 'proxies' not in config or not isinstance(config['proxies'], list):
        config['proxies'] = []

    proxy_list = node_db_manager.select(db_file)
    for proxy in proxy_list:
        # 添加一个新的代理
        new_proxy = {
            'name': proxy['name'],
            'type': 'vmess',
            'server': proxy['server'],
            'port': int(proxy['port']),
            'uuid': proxy['uuid'],
            'alterId': '0',
            'cipher': 'auto',
            'tls': True,
            'network': 'ws',
            'ws-opts': {
                'path': proxy['endpoint']
            }
        }
        config['proxies'].append(new_proxy)
        # 找到名称为 'Proxy' 的 proxy-group 并向其 proxies 列表中添加数据
        for proxy_group in config.get('proxy-groups', []):
            if proxy_group.get('name') == 'Proxy':
                if 'proxies' not in proxy_group or not isinstance(proxy_group['proxies'], list):
                    proxy_group['proxies'] = []
                proxy_group['proxies'].append(proxy['name'])
                break  # 假设只有一个名为 'Proxy' 的 proxy-group，找到后即可停止循环

    # rule
    rule_list = rule_db_manager.select_all(db_file)
    for rule in rule_list:
        config['rules'].append(rule)

    # 将修改后的字典转换回 YAML 格式的字符串
    updated_CFW = yaml.dump(config, sort_keys=False)

    # 创建一个 BytesIO 对象，并写入 YAML 内容
    file_object = BytesIO()
    file_object.write(updated_CFW.encode('utf-8'))
    file_object.seek(0)  # 移动到文件的开头，以便于读取

    # 使用 send_file 函数发送文件
    return send_file(file_object, as_attachment=True, download_name='vmess2cfw.yaml', mimetype='text/yaml')


@app.route('/refresh_port', methods=['POST'])
def refresh_port():
    node_db_manager.refresh_port(db_file, request.form['name'], request.form['port'])
    return jsonify({"success": "Success: port is refresh done."}), 200


@app.route('/', methods=['GET'])
@login_required
def index():
    proxy_list = node_db_manager.select(db_file)
    for proxy in proxy_list:
        vnstat_list = vnstat_db_manager.select_by_name(db_file, proxy['name'])
        summer = vnstat_db_manager.select_summer_by_name(db_file, proxy['name'])
        if vnstat_list:
            proxy['vnstat'] = vnstat_list
        if summer:
            proxy['vnstat_summer'] = [summer]
    return render_template('index.html', proxy_nodes=proxy_list)


@app.route('/db_index')
@login_required
def db_index():
    records = NodeDBManager.select(db_file)
    rules = rule_db_manager.select_all(db_file)
    return render_template('db_index.html', records=records, rules=rules)


@app.route('/ip_index')
@login_required
def ip_index():
    today_records = ip_recorder_manager.select(db_file)
    month_records_by_type = ip_recorder_manager.select_month(db_file)
    return render_template('ip_recorder.html', today_records=today_records, month_records_by_type=month_records_by_type)


# *使用命令行启动*
if __name__ == '__main__':
    db_file = sys.argv[1]
    refresh_script = sys.argv[2]
    # refresh_script = "dir"
    # db_file = "../../../resource/sqlite/vmess.sqlite"
    app.config['db_file'] = db_file

    # 数据库初始化
    node_db_manager = NodeDBManager()
    node_db_manager.init(db_file)
    vnstat_db_manager = VnstatInfoDBManager()
    vnstat_db_manager.init(db_file)
    rule_db_manager = V2rayRuleDBManager()
    rule_db_manager.init(db_file)
    ip_recorder_manager = IpRecorderManager()
    ip_recorder_manager.init(db_file)

    app.register_blueprint(db_router)
    app.register_blueprint(rule_db_router)
    app.register_blueprint(user_router)
    app.run(host='0.0.0.0', port=5000, threaded=True)

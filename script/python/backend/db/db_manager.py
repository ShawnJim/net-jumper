import sqlite3
from datetime import datetime, timedelta, date
from utils import get_refresh_day


class IpRecorderManager:

    def __init__(self):
        pass

    @staticmethod
    def init(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 查询sqlite_master表，检查是否存在表名为'node'的表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ip_record'")
        # 获取查询结果
        result = c.fetchone()
        # 检查结果
        if result:
            print("Table 'ip_record' exists.")
        else:
            # 创建表
            c.execute('''
                create table ip_record
                (
                    day    TEXT not null,
                    ip     TEXT not null,
                    type   TEXT,
                    update_time TEXT,
                    constraint ip_record_pk
                        primary key (day, ip)
                )
            ''')
        # 保存（提交）更改
        conn.commit()
        # 关闭连接
        conn.close()

    @staticmethod
    def save_or_update(db_file, ip, client_type):
        record_tuple = (date.today().strftime('%Y-%m-%d'), ip, client_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO ip_record VALUES (?, ?, ?, ?)", record_tuple)
        conn.commit()
        conn.close()
        if not UserManager.select_by_ip(db_file, ip):
            UserManager.save_or_update(db_file, ip, "", "")

    @staticmethod
    def select(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            SELECT ir.ip, ir.`type` as vpn_type, u.remark, u.type as device_type , update_time 
            FROM ip_record ir
            left join user u on ir.ip = u.ip
            WHERE day = ?
        """, (date.today().strftime('%Y-%m-%d'),))
        rows = c.fetchall()
        conn.close()
        if rows:
            column_names = ['ip', 'vpn_type', 'remark', 'device_type', 'update_time']
            result = [dict(zip(column_names, row)) for row in rows]
        else:
            result = []
        return result

    @staticmethod
    def select_month(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        query_month = """
            SELECT ir.ip, ir.`type` as vpn_type, u.remark, u.type as device_type 
            FROM ip_record ir
            left join user u on ir.ip = u.ip
            WHERE day >= ? AND day <= ?
            group by ir.ip, ir.type
        """
        c.execute(query_month, (date.today().strftime('%Y-%m-01'), date.today().strftime('%Y-%m-%d')))
        rows = c.fetchall()
        conn.close()
        month_records_by_type = {}
        if rows:
            for row in rows:
                ip, client_type, remark, device_type = row
                if client_type not in month_records_by_type:
                    month_records_by_type[client_type] = []
                month_records_by_type[client_type].append({
                    'ip': ip,
                    'remark': remark,
                    'device_type': device_type
                })
        return month_records_by_type



class NodeDBManager:

    def __init__(self):
        pass

    @staticmethod
    def init(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 查询sqlite_master表，检查是否存在表名为'node'的表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node'")
        # 获取查询结果
        result = c.fetchone()
        # 检查结果
        if result:
            print("Table 'node' exists.")
        else:
            # 创建表
            c.execute('''
                create table main.node
                (
                    name     TEXT,
                    server   TEXT,
                    port     TEXT,
                    uuid     TEXT,
                    endpoint TEXT,
                    threshold integer
                )
            ''')
        # 保存（提交）更改
        conn.commit()
        # 检查是否存在 threshold 字段
        c.execute("PRAGMA table_info(node)")
        result = c.fetchall()
        if len(result) >= 6:
            print("Column 'threshold' exists.")
        else:
            # 添加 threshold 字段
            c.execute("alter table node add threshold integer")
            conn.commit()

        if len(result) >= 8:
            print("Column 'refresh' exists.")
        else:
            # 添加 refresh 字段
            c.execute("alter table node add net_refresh_date integer")
            c.execute("alter table node add total_amount_flow integer")
            conn.commit()

        # 关闭连接
        conn.close()

    @staticmethod
    def insert(db_file, record):
        record_tuple = (record['name'], record['server'], record['port'], record['uuid'], record['endpoint'],
                        record['threshold'], record['net_refresh_date'], record['total_amount_flow'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("INSERT INTO node VALUES (?, ?, ?, ?, ? ,?, ?, ?)", record_tuple)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(db_file, name: str):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("DELETE FROM node WHERE name=?", (name,))
        conn.commit()
        conn.close()

    @staticmethod
    def select(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM node")
        rows = c.fetchall()
        conn.close()
        column_names = ['name', 'server', 'port', 'uuid', 'endpoint', 'threshold', 'net_refresh_date',
                        'total_amount_flow']
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    @staticmethod
    def update(db_file, name, updated_record):
        record_tuple = (
            updated_record['server'], updated_record['port'], updated_record['uuid'],
            updated_record['endpoint'], updated_record['name'], updated_record['threshold'],
            updated_record['net_refresh_date'], updated_record['total_amount_flow'], name
        )
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute(
            "UPDATE node Set server = ? , port = ?, uuid = ? , endpoint = ? , name = ?, threshold = ?, "
            "net_refresh_date = ?, total_amount_flow = ? where name = ?",
            record_tuple
        )
        conn.commit()
        conn.close()

    @staticmethod
    def select_by_name(db_file, name):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM node where name = ?", (name,))
        row = c.fetchone()
        conn.close()
        column_names = ['name', 'server', 'port', 'uuid', 'endpoint', 'threshold', 'net_refresh_date',
                        'total_amount_flow']
        result = dict(zip(column_names, row))
        return result

    @staticmethod
    def refresh_port(db_file, name, port):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("UPDATE node Set port = ? where name = ?", (port, name))
        conn.commit()
        conn.close()

    @staticmethod
    def select_total_threshold(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("select round(sum(node.threshold), 2) from node")
        result = c.fetchone()
        conn.close()
        return result


class VnstatInfoDBManager:

    def __init__(self):
        pass

    @staticmethod
    def init(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 查询sqlite_master表，检查是否存在表名为'node'的表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vnstat_info'")
        # 获取查询结果
        result = c.fetchone()
        # 检查结果
        if result:
            print("Table 'node' exists.")
        else:
            # 创建表
            c.execute('''
                create table main.vnstat_info
                (
                    name  TEXT not null,
                    day   TEXT not null,
                    rx    TEXT,
                    tx    TEXT,
                    total TEXT,
                    constraint vnstat_info_pk
                        primary key (name, day)
                )
            ''')
        # 保存（提交）更改
        conn.commit()
        # 关闭连接
        conn.close()


    @staticmethod
    def delete(db_file, name: str, day: str):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("DELETE FROM vnstat_info WHERE day=? and name = ?", (day, name))
        conn.commit()
        conn.close()

    @staticmethod
    def select_by_name(db_file, name):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        node = NodeDBManager.select_by_name(db_file, name)
        today = date.today()
        refresh_day = get_refresh_day(node['net_refresh_date'], today)
        c.execute("SELECT day, rx, tx, total FROM vnstat_info where name = ?"
                  " and day >= ? and day <= ? order by day desc", (name, refresh_day, today))
        rows = c.fetchall()
        conn.close()
        column_names = ['day', 'rx', 'tx', 'total']
        return [dict(zip(column_names, row)) for row in rows]

    @staticmethod
    def select_total_for_day(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("select "
                  "ROUND(sum(rx), 2) as rx, "
                  "ROUND(sum(tx), 2) as tx, "
                  "ROUND(sum(total), 2) as total "
                  "from vnstat_info where day = ?", (date.today().strftime('%Y-%m-%d'),))
        row = c.fetchone()
        conn.close()
        column_names = ['rx', 'tx', 'total']
        return dict(zip(column_names, row))

    @staticmethod
    def select_by_day_between(db_file, name, start_day, end_day):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT sum(total) FROM vnstat_info where name = ? and day >= ? and day <= ?",
                  (name, start_day, end_day))
        row = c.fetchone()
        conn.close()
        return int(row[0])

    @staticmethod
    def select_by_today(db_file, name, today):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT sum(total) FROM vnstat_info where name = ? and day = ? ",
                  (name, today))
        row = c.fetchone()
        conn.close()
        return int(row[0])

    @staticmethod
    def refresh_record(db_file, record):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 检查是否存在具有指定 name 和 day 的记录
        c.execute("SELECT * FROM vnstat_info WHERE name = ? AND day = ?", (record['name'], record['day']))
        result = c.fetchone()
        if result:
            # 如果存在，更新记录
            record_tuple = (record['rx'], record['tx'], record['total'], record['name'], record['day'])
            c.execute("UPDATE vnstat_info Set rx = ? , tx = ?, total = ? where name = ? and day = ?", record_tuple)
        else:
            # 如果不存在，插入新的记录
            record_tuple = (record['name'], record['day'], record['rx'], record['tx'], record['total'])
            c.execute("INSERT INTO vnstat_info VALUES (?, ?, ?, ?, ?)", record_tuple)
        conn.commit()
        conn.close()

    @staticmethod
    def delete_old_records(db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("DELETE FROM vnstat_info WHERE date(day) < date(?)", (date_30_days_ago,))
        conn.commit()
        conn.close()

    @staticmethod
    def select_summer_by_name(db_file, name):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        node = NodeDBManager.select_by_name(db_file, name)
        today = date.today()
        refresh_day = get_refresh_day(node['net_refresh_date'], today)
        c.execute("SELECT  "
                  "ROUND(sum(rx), 2) as rx, "
                  "ROUND(sum(tx), 2) as tx, "
                  "ROUND(sum(total), 2) as total "
                  " FROM vnstat_info where name = ? and day >= ? and day <= ?", (name, refresh_day, today))
        row = c.fetchone()
        conn.close()
        column_names = ['rx', 'tx', 'total']
        return dict(zip(column_names, row))


class V2rayRuleDBManager:

    def __init__(self):
        pass

    @staticmethod
    def init(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 查询sqlite_master表，检查是否存在表名为'v2ray_rule'的表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='v2ray_rule'")
        # 获取查询结果
        result = c.fetchone()
        # 检查结果
        if result:
            print("Table 'node' exists.")
        else:
            # 创建表
            c.execute('''
                create table main.v2ray_rule
                (
                    rule text not null
                        constraint v2ray_rule_pk
                            primary key
                );
            ''')
        # 保存（提交）更改
        conn.commit()
        # 关闭连接
        conn.close()

    @staticmethod
    def select_all(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT rule FROM v2ray_rule")
        rows = c.fetchall()
        conn.close()
        result = [str(row[0]) for row in rows]
        return result

    @staticmethod
    def insert(db_file, rule):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("INSERT INTO v2ray_rule VALUES (?)", (rule,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(db_file, rule: str):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("DELETE FROM v2ray_rule WHERE rule=?", (rule,))
        conn.commit()
        conn.close()

    @staticmethod
    def update(db_file, old_rule: str, rule: str):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("UPDATE v2ray_rule Set rule = ? where rule = ?", (rule, old_rule))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_all(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("delete from v2ray_rule")
        conn.commit()
        conn.close()


class UserManager:

    def __init__(self):
        pass

    @staticmethod
    def init(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        # 查询sqlite_master表，检查是否存在表名为'node'的表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        # 获取查询结果
        result = c.fetchone()
        # 检查结果
        if result:
            print("Table 'user' exists.")
        else:
            # 创建表
            c.execute('''
                -- auto-generated definition
                create table user
                (
                    ip     TEXT
                        constraint user_pk
                            primary key,
                    remark TEXT,
                    type   TEXT
                )
            ''')
        # 保存（提交）更改
        conn.commit()
        # 关闭连接
        conn.close()

    @staticmethod
    def save_or_update(db_file, ip, remark, device_type):
        record_tuple = (ip, remark, device_type)
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user (ip, remark, type) VALUES (?, ?, ?)", record_tuple)
        conn.commit()
        conn.close()

    @staticmethod
    def select_by_ip(db_file, ip):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            SELECT ip, remark, type
            FROM user
            WHERE ip = ?
        """, (ip,))
        row = c.fetchone()
        conn.close()
        if row:
            column_names = ['ip', 'remark', 'type']
            result = dict(zip(column_names, row))
        else:
            result = None
        return result

    @staticmethod
    def select_all(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            SELECT ip, remark, type
            FROM user
        """)
        rows = c.fetchall()
        conn.close()
        column_names = ['ip', 'remark', 'type']
        result = [dict(zip(column_names, row)) for row in rows]
        return result

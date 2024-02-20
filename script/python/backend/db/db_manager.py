import sqlite3


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
                  CREATE TABLE node
                  (name TEXT, server TEXT, port TEXT, uuid TEXT, endpoint TEXT)
            ''')
        # 保存（提交）更改
        conn.commit()
        # 关闭连接
        conn.close()

    @staticmethod
    def insert(db_file, record):
        record_tuple = (record['name'], record['server'], record['port'], record['uuid'], record['endpoint'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("INSERT INTO node VALUES (?, ?, ?, ?, ?)", record_tuple)
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
        column_names = ['name', 'server', 'port', 'uuid', 'endpoint']
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    @staticmethod
    def update(db_file, name, updated_record):
        record_tuple = (
            updated_record['server'], updated_record['port'], updated_record['uuid'],
            updated_record['endpoint'], updated_record['name'], name
        )
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("UPDATE node Set server = ? , port = ?, uuid = ? , endpoint = ? , name = ? where name = ?",
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
        column_names = ['name', 'server', 'port', 'uuid', 'endpoint']
        result = dict(zip(column_names, row))
        return result

    @staticmethod
    def refresh_port(db_file, name, port):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("UPDATE node Set port = ? where name = ?", (port, name))
        conn.commit()
        conn.close()


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
                    strict;
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
        c.execute("SELECT day, rx, tx, total FROM vnstat_info where name = ?", (name,))
        rows = c.fetchall()
        conn.close()
        column_names = ['day', 'rx', 'tx', 'total']
        return [dict(zip(column_names, row)) for row in rows]

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

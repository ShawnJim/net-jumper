from flask import request, redirect, url_for

users = {
    "v2rayadmin": "v2ray@123456",
}

def login_required(view_func):
    """
    登录验证装饰器
    :param view_func:
    :return:
    """
    def wrapper(*args, **kwargs):
        if "username" not in request.cookies or "password" not in request.cookies:
            return redirect(url_for("login"))

        username = request.cookies.get("username")
        password = request.cookies.get("password")

        if not validate_user(username, password):
            return redirect(url_for("login"))

        return view_func(*args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


def validate_user(username, password):
    """
    用户验证函数
    :param username: 用户名
    :param password: 密码
    :return:
    """
    return username in users and users[username] == password


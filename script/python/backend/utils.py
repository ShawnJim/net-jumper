from datetime import date

from dateutil.relativedelta import relativedelta
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


def get_refresh_day(net_refresh_date, today) -> date:
    current_year = today.year
    current_month = today.month
    current_day = today.day
    # 如果今天是刷新日, 则流量刷新日期返回当天
    if net_refresh_date == today:
        return today
    # 如果流量刷新日期小于今天, 则流量刷新日则为下月当天
    elif current_day > net_refresh_date:
        return date(current_year, current_month, net_refresh_date)
    # 如果流量刷新日期大于今天, 则流量刷新日为当月刷新日
    else:
        return (today + relativedelta(months=-1)).replace(day=net_refresh_date)


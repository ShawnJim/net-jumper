import requests

subscribe_coll = [
    "https://example.com/subscribe1",
]



# 启动一个本地服务，提供一个接口，返回subscribe_assembler
from flask import Flask, make_response

app = Flask(__name__)

@app.route('/subscribe')
def subscribe():
    subscribe_assembler = ""
    upload = 0
    download=0
    for subscribe in subscribe_coll:
        response = requests.get(subscribe)
        subscribe_assembler += response.text + "\n"
        userinfo = response.headers['Subscription-Userinfo']
        upload += int(userinfo.split(';')[0].split('=')[1])
        download += int(userinfo.split(';')[1].split('=')[1])

    response = make_response(subscribe_assembler)
    response.headers['Subscription-Userinfo'] = f'upload={upload};download={download};total=3221225472000;expire=2588803200'
    return response



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9679)

from flask import Flask, render_template, jsonify
from NeteaseCloudMusicApi import login_qr_key, login_qr_create, login_qr_check
import time

app = Flask(__name__)

# 存储二维码 key
qr_key_cache = {}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/get_qr', methods=['GET'])
def get_qr():
    key = login_qr_key()["data"]["unikey"]
    qr = login_qr_create(key, qrimg=True)["data"]["qrimg"]
    qr_key_cache["key"] = key
    return jsonify({"qrimg": qr})

@app.route('/check_qr', methods=['GET'])
def check_qr():
    key = qr_key_cache.get("key")
    if not key:
        return jsonify({"code": 400, "msg": "No QR key"})
    
    res = login_qr_check(key)
    code = res["code"]
    if code == 803:
        return jsonify({"code": 200, "msg": "Login successful", "cookie": res["cookie"]})
    elif code == 800:
        return jsonify({"code": 400, "msg": "QR expired"})
    elif code == 801:
        return jsonify({"code": 202, "msg": "Waiting for scan"})
    elif code == 802:
        return jsonify({"code": 203, "msg": "Waiting for confirm"})
    else:
        return jsonify({"code": code, "msg": "Unknown status"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

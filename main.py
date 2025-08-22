from flask import Flask, render_template, jsonify
from NeteaseCloudMusicApi import login_qr_key, login_qr_create, login_qr_check
import time

app = Flask(__name__)

# 保存全局二维码 key
qr_key = None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_qr")
def get_qr():
    global qr_key
    # 获取二维码 key
    res = login_qr_key()
    qr_key = res["data"]["unikey"]

    # 获取二维码 base64 图片
    qr_res = login_qr_create({"key": qr_key, "qrimg": "true"})
    return jsonify(qr_res)

@app.route("/check_qr")
def check_qr():
    global qr_key
    if not qr_key:
        return jsonify({"code": 400, "msg": "No QR key"})

    # 查询扫码状态
    res = login_qr_check({"key": qr_key})
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

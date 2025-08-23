from flask import Flask, request, jsonify, render_template
from NeteaseCloudMusic import NeteaseCloudMusicApi
import os

app = Flask(__name__)
netease = NeteaseCloudMusicApi()  # 初始化API

# 前端页面
@app.route("/")
def index():
    return render_template("index.html")

# 发送验证码
@app.route("/captcha", methods=["POST"])
def send_captcha():
    phone = request.form.get("phone")
    if not phone:
        return jsonify({"error": "缺少手机号"}), 400
    result = netease.request("/captcha/sent", {"phone": str(phone)})
    return jsonify(result)

# 手机号 + 验证码登录
@app.route("/login", methods=["POST"])
def login():
    phone = request.form.get("phone")
    captcha = request.form.get("captcha")
    if not phone or not captcha:
        return jsonify({"error": "缺少手机号或验证码"}), 400
    result = netease.request("/login/cellphone", {"phone": str(phone), "captcha": str(captcha)})
    return jsonify(result)

# 查询登录状态
@app.route("/status", methods=["GET"])
def status():
    result = netease.request("/login/status")
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request, jsonify
from NeteaseCloudMusic import NeteaseCloudMusicApi
import requests

app = Flask(__name__)

# 初始化 API
netease = NeteaseCloudMusicApi()


@app.route("/")
def index():
    return {"message": "NeteaseCloudMusic API 服务运行中"}


# 发送验证码
@app.route("/captcha", methods=["POST"])
def send_captcha():
    data = request.json
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "缺少手机号"}), 400

    result = netease.request("/captcha/sent", {"phone": str(phone)})
    return jsonify(result)


# 手机号 + 验证码登录
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    phone = data.get("phone")
    captcha = data.get("captcha")
    if not phone or not captcha:
        return jsonify({"error": "缺少手机号或验证码"}), 400

    result = netease.request("/login/cellphone", {"phone": str(phone), "captcha": str(captcha)})
    return jsonify(result)


# 查询登录状态
@app.route("/status", methods=["GET"])
def status():
    result = netease.request("/login/status")
    return jsonify(result)


# 获取歌曲详情
@app.route("/song/<song_id>", methods=["GET"])
def song_detail(song_id):
    result = netease.request("song_detail", {"ids": str(song_id)})
    return jsonify(result)


# 获取歌曲下载地址
@app.route("/song/<song_id>/url", methods=["GET"])
def song_url(song_id):
    result = netease.request("song_url_v1", {"id": str(song_id), "level": "exhigh"})
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

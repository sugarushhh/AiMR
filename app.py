import sys
import os
from flask import Flask, render_template, jsonify

# 将 NeteaseCloudMusicApi 添加到 sys.path，确保 Linux/Render 可以找到
sys.path.append(os.path.join(os.path.dirname(__file__), "NeteaseCloudMusicApi"))

# 导入 SDK 登录方法
from login import login_qr_key, login_qr_create, login_qr_check

app = Flask(__name__)

# 全局存储二维码 key
qr_key_cache = {}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/get_qr', methods=['GET'])
def get_qr():
    try:
        # 获取二维码 key
        key_data = login_qr_key()
        key = key_data["data"]["unikey"]
        qr_data = login_qr_create(key, qrimg=True)
        qr_img = qr_data["data"]["qrimg"]

        # 缓存 key
        qr_key_cache["key"] = key
        return jsonify({"qrimg": qr_img})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_qr', methods=['GET'])
def check_qr():
    key = qr_key_cache.get("key")
    if not key:
        return jsonify({"code": 400, "msg": "No QR key"})

    try:
        status = login_qr_check(key)
        code = status["code"]
        if code == 803:
            return jsonify({"code": 200, "msg": "Login successful", "cookie": status.get("cookie")})
        elif code == 800:
            return jsonify({"code": 400, "msg": "QR expired"})
        elif code == 801:
            return jsonify({"code": 202, "msg": "Waiting for scan"})
        elif code == 802:
            return jsonify({"code": 203, "msg": "Waiting for confirm"})
        else:
            return jsonify({"code": code, "msg": "Unknown status"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render 默认会使用 0.0.0.0
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

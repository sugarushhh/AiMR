import sys
import os
from flask import Flask, render_template, jsonify

# 将 SDK 文件夹加入 sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "NeteaseCloudMusicApi"))

# 自动尝试导入 login_qr_* 函数
try:
    # 优先从 api.py 导入
    from api import login_qr_key, login_qr_create, login_qr_check
except ModuleNotFoundError:
    try:
        # 如果 api.py 里没定义，尝试从 __init__.py 导入
        from NeteaseCloudMusicApi import login_qr_key, login_qr_create, login_qr_check
    except ModuleNotFoundError:
        raise RuntimeError(
            "请确认 NeteaseCloudMusicApi 里包含 login_qr_key, login_qr_create, login_qr_check 函数"
        )

app = Flask(__name__)
qr_key_cache = {}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/get_qr', methods=['GET'])
def get_qr():
    try:
        key_data = login_qr_key()
        key = key_data["data"]["unikey"]
        qr_data = login_qr_create(key, qrimg=True)
        qr_img = qr_data["data"]["qrimg"]
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
    # Render 默认使用 0.0.0.0
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

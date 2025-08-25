# app.py
import os
import threading
import time
import requests
from flask import Flask, request, jsonify, render_template

# NeteaseCloudMusic SDK
from NeteaseCloudMusic import NeteaseCloudMusicApi

# Supabase
from supabase import create_client, Client

# ---------- Config ----------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
RENDER_URL = os.environ.get("RENDER_URL", "").strip()  # 可选，用于 keep-alive

app = Flask(__name__, template_folder="templates")
netease = NeteaseCloudMusicApi()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---------- 可选：自唤醒，防止 Render 休眠 ----------
def keep_alive():
    url = RENDER_URL or ""
    if not url:
        return
    while True:
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(300)  # 5 分钟

threading.Thread(target=keep_alive, daemon=True).start()

# ------------------- 前端页面 -------------------
@app.route("/")
def index():
    return render_template("login.html")

# ------------------- Helper: safe extract functions -------------------
def extract_list(resp):
    if not resp:
        return []
    if isinstance(resp, list):
        return resp
    for key in ("data", "result", "list", "followeds", "artists", "songs", "weekData", "allData"):
        v = resp.get(key) if isinstance(resp, dict) else None
        if isinstance(v, list):
            return v
    return []

def safe_get_profile_from_status(status_resp):
    try:
        if not status_resp:
            return None
        if isinstance(status_resp, dict):
            for path in [("data","data","profile"), ("data","profile"), ("profile",)]:
                cur = status_resp
                ok = True
                for p in path:
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        ok = False
                        break
                if ok and isinstance(cur, dict):
                    userId = cur.get("userId") or cur.get("user_id") or cur.get("id")
                    return cur, userId
        return None
    except Exception:
        return None

def pick(v, *keys):
    for k in keys:
        if isinstance(v, dict) and k in v:
            return v[k]
    return None

# ------------------- 网易云绑定与数据接口 -------------------

@app.route("/api/netease/send_captcha", methods=["POST"])
def ne_send_captcha():
    phone = request.form.get("phone") or request.json.get("phone") if request.is_json else None
    if not phone:
        return jsonify({"error": "缺少手机号"}), 400
    res = netease.request("/captcha/sent", {"phone": str(phone)})
    return jsonify(res)


@app.route("/api/netease/login", methods=["POST"])
def ne_login():
    if request.is_json:
        body = request.json
        phone = body.get("phone")
        captcha = body.get("captcha")
    else:
        phone = request.form.get("phone")
        captcha = request.form.get("captcha")

    if not phone or not captcha:
        return jsonify({"error": "缺少手机号或验证码"}), 400

    # 1) 网易云登录
    try:
        result = netease.request("/login/cellphone", {"phone": str(phone), "captcha": str(captcha)})
    except Exception as e:
        return jsonify({"error": "调用网易云登录接口失败", "detail": str(e)}), 500

    cookie = getattr(netease, "cookie", None)
    if result.get("code") != 200 or not cookie:
        return jsonify({"error": "网易云登录失败", "raw": result}), 400

    # 2) 读取 profile
    nickname = None
    account_user_id = None
    try:
        status = netease.request("/login/status")
        profile_res = safe_get_profile_from_status(status)
        if profile_res:
            profile, account_user_id = profile_res[0], profile_res[1]
            nickname = profile.get("nickname") or profile.get("name")
        else:
            nickname = pick(status, "data", "data", "profile", "nickname") or pick(status, "data", "profile", "nickname")
            account_user_id = pick(status, "data", "data", "profile", "userId") or pick(status, "data", "profile", "userId")
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "nickname": nickname
    })


@app.route("/api/netease/status", methods=["GET"])
def ne_status():
    try:
        status = netease.request("/login/status")
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 健康检查
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

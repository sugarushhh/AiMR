import os
import threading
import time
import requests
from functools import wraps
from flask import Flask, request, jsonify, render_template

# NeteaseCloudMusic SDK
from NeteaseCloudMusic import NeteaseCloudMusicApi

# Supabase
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

app = Flask(__name__, template_folder="templates")
netease = NeteaseCloudMusicApi()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)  # 后端用 service_role 便于写入

# ---------- 可选：自唤醒，防止 Render 休眠 ----------
def keep_alive():
    url = os.environ.get("RENDER_URL") or ""  # 你可在 env 里加 RENDER_URL = https://your.onrender.com
    if not url:
        return
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(300)  # 5 分钟

threading.Thread(target=keep_alive, daemon=True).start()


# ---------- 工具：校验 Supabase 前端传来的 JWT ----------
import httpx

def get_supabase_user_from_jwt(token: str):
    """
    通过 GoTrue /auth/v1/user 验证前端 Supabase JWT 并取回 user 对象
    """
    if not token:
        return None, "missing token"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_ANON_KEY,  # 前端同款 anon key
    }
    url = f"{SUPABASE_URL}/auth/v1/user"
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"auth error: {resp.text}"
    except Exception as e:
        return None, str(e)

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        user, err = get_supabase_user_from_jwt(token)
        if err or not user:
            return jsonify({"error": "unauthorized", "detail": err}), 401
        # user 对象里有 id
        request.supabase_user = user
        return f(*args, **kwargs)
    return wrapper


# ------------------- 前端页面 -------------------
@app.route("/")
def index():
    # 你的 templates/login.html
    return render_template("login.html")


# ------------------- 网易云绑定与数据接口 -------------------

@app.route("/api/netease/send_captcha", methods=["POST"])
@require_auth
def ne_send_captcha():
    phone = request.form.get("phone")
    if not phone:
        return jsonify({"error": "缺少手机号"}), 400
    res = netease.request("/captcha/sent", {"phone": str(phone)})
    return jsonify(res)

@app.route("/api/netease/login", methods=["POST"])
@require_auth
def ne_login():
    """
    前端传来 phone + captcha，调用网易云登陆
    成功后将返回的 cookie 写入 netease_accounts 表
    """
    phone = request.form.get("phone")
    captcha = request.form.get("captcha")
    if not phone or not captcha:
        return jsonify({"error": "缺少手机号或验证码"}), 400

    # 1) 网易云登录
    result = netease.request("/login/cellphone", {"phone": str(phone), "captcha": str(captcha)})

    # 2) 检查结果并拿 cookie（SDK 会把 cookie 存在 netease.cookie 字段；也会在工作目录生成 cookie_storage）
    cookie = getattr(netease, "cookie", None)

    if result.get("code") != 200 or not cookie:
        return jsonify({"error": "网易云登录失败", "raw": result}), 400

    # 3) 取 Supabase user_id
    user_id = request.supabase_user["id"]
    nickname = None
    try:
        # 查一下登录状态拿 profile（可选）
        status = netease.request("/login/status")
        nickname = status.get("data", {}).get("data", {}).get("profile", {}).get("nickname")
    except:
        pass

    # 4) 写入/更新 netease_accounts（同一用户只保留一条的话可以先 upsert）
    # 这里用 service_role，RLS 不生效
    supabase.table("netease_accounts").insert({
        "user_id": user_id,
        "phone": str(phone),
        "cookie": cookie,   # 生产环境建议加密
        "nickname": nickname
    }).execute()

    return jsonify({"ok": True, "nickname": nickname})

@app.route("/api/netease/status", methods=["GET"])
@require_auth
def ne_status():
    try:
        status = netease.request("/login/status")
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history/sync", methods=["POST"])
@require_auth
def sync_history():
    """
    示例：从网易云拉取最近播放并落库
    实际接口你可以用 /user/record 或 /record/recent/song 等（按 SDK 文档选择）
    这里示例用一个假的结果结构说明如何写库
    """
    user_id = request.supabase_user["id"]

    # 保底：确保 DB 有 cookie（如果你想每次都用 SDK 的内存 cookie，也可以）
    acc = supabase.table("netease_accounts").select("*").eq("user_id", user_id).limit(1).execute()
    if not acc.data:
        return jsonify({"error": "未绑定网易云账号"}), 400

    # TODO 这里根据 SDK 文档去请求实际历史接口，你可以替换为真实调用
    # 例如：recent = netease.request("/record/recent/song", {"limit": "50"})
    # 这里给个示例列表：
    recent_list = [
        {"song_id": "33894312", "song_name": "Lemon", "artist": "米津玄師", "played_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
    ]

    # 批量落库
    rows = [{"user_id": user_id, **item} for item in recent_list]
    if rows:
        supabase.table("listening_history").insert(rows).execute()

    return jsonify({"ok": True, "count": len(rows)})


# 健康检查
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os
from flask import Flask, request, jsonify
from supabase import create_client, Client
from NeteaseCloudMusic import cloudmusic as cm

# ============ 配置 =============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask app
app = Flask(__name__)

# ============ 网易云登录 ============
@app.route("/login", methods=["POST"])
def login():
    """
    登录网易云账号
    Body 参数:
        phone: 手机号
        password: 密码
    """
    data = request.json
    phone = data.get("phone")
    password = data.get("password")

    try:
        user = cm.login(phone, password)
        return jsonify({"message": "登录成功", "userId": user["account"]["id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============ 拉取关注歌手 ============
@app.route("/fetch/artists", methods=["POST"])
def fetch_artists():
    """
    拉取用户关注的歌手并写入 user_artists 表
    Body 参数:
        userId: 网易云用户 ID
    """
    data = request.json
    user_id = data.get("userId")

    try:
        artists = cm.getUserFollows(user_id)  # 获取关注歌手
        for artist in artists:
            supabase.table("user_artists").insert({
                "user_id": user_id,
                "artist_id": artist["userId"],
                "artist_name": artist["nickname"]
            }).execute()

        return jsonify({"message": f"成功写入 {len(artists)} 个关注歌手"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============ 拉取历史记录 ============
@app.route("/fetch/history", methods=["POST"])
def fetch_history():
    """
    拉取用户听歌历史并写入 user_history 表
    Body 参数:
        userId: 网易云用户 ID
    """
    data = request.json
    user_id = data.get("userId")

    try:
        history = cm.getUserRecord(user_id, type=1)  # type=1 最近一周
        for h in history:
            supabase.table("user_history").insert({
                "user_id": user_id,
                "song_id": h["song"]["id"],
                "song_name": h["song"]["name"],
                "play_count": h["playCount"]
            }).execute()

        return jsonify({"message": f"成功写入 {len(history)} 条历史记录"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============ 拉取喜欢的音乐 ============
@app.route("/fetch/likes", methods=["POST"])
def fetch_likes():
    """
    拉取用户喜欢的音乐并写入 user_likes 表
    Body 参数:
        userId: 网易云用户 ID
    """
    data = request.json
    user_id = data.get("userId")

    try:
        likes = cm.getUserPlaylist(user_id)[0]  # 取第一个歌单（喜欢的音乐）
        tracks = cm.getPlaylist(likes["id"])["tracks"]

        for track in tracks:
            supabase.table("user_likes").insert({
                "user_id": user_id,
                "song_id": track["id"],
                "song_name": track["name"],
                "artist_name": track["ar"][0]["name"]
            }).execute()

        return jsonify({"message": f"成功写入 {len(tracks)} 首喜欢的音乐"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============ 首页 ============
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Netease → Supabase API 运行中"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

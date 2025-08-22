import sys, os
# 添加 SDK 源码路径
sys.path.append(os.path.join(os.path.dirname(__file__), "NeteaseCloudMusic_PythonSDK"))

from NeteaseCloudMusicApi import api

def fetch_user_recent_play(uid: str, limit: int = 20):
    """
    uid: 网易云用户 id
    返回最近播放的歌曲列表
    """
    result = api.user_record(uid=uid, type=1)  # type=1 为最近一周
    songs = result.get("allData", [])[:limit]
    data = []
    for s in songs:
        data.append({
            "song_id": s["song"]["id"],
            "name": s["song"]["name"],
            "artist": s["song"]["ar"][0]["name"],
            "played_at": s.get("playTime")  # 时间戳
        })
    return data

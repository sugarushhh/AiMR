import os
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def insert_listen_record(user_id: str, song_id: str, played_at: str):
    supabase.table("listen_logs").insert({
        "user_id": user_id,
        "song_id": song_id,
        "played_at": played_at
    }).execute()

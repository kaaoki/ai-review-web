"""
db.py
Supabase（無料枠のPostgreSQL）にレビュー結果を保存・取得する。
テーブル定義は supabase_schema.sql を参照。
"""

from datetime import datetime, timezone

from supabase import create_client


def get_client(url: str, key: str):
    return create_client(url, key)


def save_review(client, file_name: str, file_type: str, summary: str, result: dict):
    """レビュー結果を1件保存する"""
    payload = {
        "file_name": file_name,
        "file_type": file_type,
        "summary": summary,
        "result_json": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    response = client.table("reviews").insert(payload).execute()
    return response.data[0] if response.data else None


def list_reviews(client, limit: int = 100):
    """保存済みレビューの一覧を新しい順で取得する"""
    response = (
        client.table("reviews")
        .select("id, file_name, file_type, summary, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_review(client, review_id: str):
    """1件分の詳細（result_json含む）を取得する"""
    response = client.table("reviews").select("*").eq("id", review_id).single().execute()
    return response.data


def delete_review(client, review_id: str):
    client.table("reviews").delete().eq("id", review_id).execute()

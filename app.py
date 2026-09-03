"""
app.py
文書自動レビューツール（Webアプリ版）

- Gemini APIで文書をレビュー
- Supabaseに結果を永続保存
- 過去のレビュー結果を一覧から選んで閲覧

必要なsecrets（.streamlit/secrets.toml、またはStreamlit CloudのSecrets管理画面）:
  APP_PASSWORD    = "任意のパスワード"
  GEMINI_API_KEY  = "Gemini APIキー"
  SUPABASE_URL    = "SupabaseプロジェクトのURL"
  SUPABASE_KEY    = "Supabaseのanon key"
"""

import pandas as pd
import streamlit as st

import db
from review_engine import SUPPORTED_EXTENSIONS, extract_text, review_document, summarize_result

st.set_page_config(page_title="文書自動レビューツール", page_icon="📝", layout="wide")


# ---------------------------------------------------------------------------
# 簡易パスワード認証
# ---------------------------------------------------------------------------
def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("📝 文書自動レビューツール")
    st.caption("ポートフォリオデモ：Gemini APIによる自動文書レビュー")

    pw = st.text_input("パスワードを入力してください", type="password")
    if st.button("入室する"):
        correct = st.secrets.get("APP_PASSWORD", "")
        if correct and pw == correct:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("パスワードが違います。")
    return False


if not check_password():
    st.stop()


# ---------------------------------------------------------------------------
# 各種クライアント初期化
# ---------------------------------------------------------------------------
@st.cache_resource
def get_supabase_client():
    return db.get_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


try:
    supabase = get_supabase_client()
except Exception as e:
    st.error("Supabaseへの接続に失敗しました。secretsの設定を確認してください。")
    st.exception(e)
    st.stop()

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# 画面
# ---------------------------------------------------------------------------
st.title("📝 文書自動レビューツール")
st.caption("Gemini APIで複数フォーマットの文書を自動レビューし、結果を保存・一覧参照できます。")

tab_upload, tab_history = st.tabs(["📤 アップロード＆レビュー", "📚 過去のレビュー一覧"])

# --- タブ1: アップロード＆レビュー ---------------------------------------
with tab_upload:
    st.subheader("ファイルをアップロード")
    st.write(f"対応形式: {', '.join(SUPPORTED_EXTENSIONS)}")

    uploaded_file = st.file_uploader(
        "レビューしたいファイルを選択",
        type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
    )

    if uploaded_file is not None:
        st.info(f"選択中のファイル: **{uploaded_file.name}**（{uploaded_file.size:,} bytes）")

        if st.button("🔍 レビューを実行", type="primary"):
            if not GEMINI_API_KEY:
                st.error("GEMINI_API_KEYがsecretsに設定されていません。")
            else:
                with st.spinner("文書を読み込んでいます..."):
                    file_bytes = uploaded_file.getvalue()
                    try:
                        text = extract_text(uploaded_file.name, file_bytes)
                    except Exception as e:
                        st.error("ファイルの読み込みに失敗しました。")
                        st.exception(e)
                        st.stop()

                if not text.strip():
                    st.warning("ファイルからテキストを抽出できませんでした。")
                else:
                    with st.spinner("Gemini APIでレビュー中です...（数十秒かかる場合があります）"):
                        try:
                            result = review_document(text, GEMINI_API_KEY)
                        except Exception as e:
                            st.error("レビュー実行中にエラーが発生しました。")
                            st.exception(e)
                            st.stop()

                    summary = summarize_result(result)
                    file_type = uploaded_file.name.split(".")[-1]

                    with st.spinner("結果を保存しています..."):
                        saved = db.save_review(
                            supabase, uploaded_file.name, file_type, summary, result
                        )

                    st.success(f"レビュー完了：{summary}")

                    issues = result.get("issues", [])
                    if issues:
                        df = pd.DataFrame(issues)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.write("指摘事項はありませんでした。")

                    st.caption("この結果は自動保存され、「過去のレビュー一覧」タブからいつでも見返せます。")

# --- タブ2: 過去のレビュー一覧 ---------------------------------------------
with tab_history:
    st.subheader("これまでのレビュー結果")

    if st.button("🔄 一覧を更新"):
        st.rerun()

    reviews = db.list_reviews(supabase)

    if not reviews:
        st.write("まだレビュー結果がありません。")
    else:
        list_df = pd.DataFrame(reviews)[["file_name", "file_type", "summary", "created_at"]]
        list_df.columns = ["ファイル名", "種別", "サマリー", "実行日時"]
        st.dataframe(list_df, use_container_width=True, hide_index=True)

        options = {
            f"{r['file_name']}（{r['created_at'][:19].replace('T', ' ')}）": r["id"]
            for r in reviews
        }
        selected_label = st.selectbox("詳細を見るレビューを選択", options.keys())

        if selected_label:
            selected_id = options[selected_label]
            detail = db.get_review(supabase, selected_id)

            if detail:
                st.markdown(f"### {detail['file_name']}")
                st.caption(f"実行日時: {detail['created_at']}　|　{detail['summary']}")

                issues = detail["result_json"].get("issues", [])
                if issues:
                    df = pd.DataFrame(issues)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.write("指摘事項はありませんでした。")

                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🗑️ この結果を削除", key=f"del_{selected_id}"):
                        db.delete_review(supabase, selected_id)
                        st.rerun()

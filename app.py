"""
app.py
文書自動レビューツール（Webアプリ版）

- Gemini APIで文書をレビュー（複数ファイル一括対応）
- Supabaseに結果を永続保存
- レビュー結果を一覧から選んで閲覧

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
# 画面切り替え（st.tabsはコードから切り替えられないため、
# セグメントコントロール＋session_stateで自前実装する）
# ---------------------------------------------------------------------------
VIEW_UPLOAD = "アップロード"
VIEW_HISTORY = "レビュー一覧"

# segmented_controlのkey("active_view")は、ウィジェット生成後の同一実行内では
# 直接書き換えられない(StreamlitWidgetAlreadyInstantiatedError)。
# そのため、切り替えたいときは "_pending_view" に希望の値を入れてrerunし、
# ウィジェット生成より前のこの位置で "active_view" に反映させる。
if "_pending_view" in st.session_state:
    st.session_state["active_view"] = st.session_state.pop("_pending_view")

if "active_view" not in st.session_state:
    st.session_state["active_view"] = VIEW_UPLOAD

st.title("📝 文書自動レビューツール")
st.caption("Gemini APIで複数フォーマットの文書を自動レビューし、結果を保存・一覧参照できます。")

view = st.segmented_control(
    "表示切り替え",
    options=[VIEW_UPLOAD, VIEW_HISTORY],
    key="active_view",
    label_visibility="collapsed",
)

# --- アップロード＆レビュー -------------------------------------------------
if view == VIEW_UPLOAD:
    st.subheader("ファイルをアップロード")
    st.write(f"対応形式: {', '.join(SUPPORTED_EXTENSIONS)}（複数選択可）")

    uploaded_files = st.file_uploader(
        "レビューしたいファイルを選択",
        type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.info(f"選択中のファイル: {len(uploaded_files)}件")

        if st.button("🔍 レビューを実行", type="primary"):
            if not GEMINI_API_KEY:
                st.error("GEMINI_API_KEYがsecretsに設定されていません。")
            else:
                progress = st.progress(0.0)
                status_area = st.container()
                error_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    status_area.write(f"⏳ {uploaded_file.name} を処理中...")

                    try:
                        file_bytes = uploaded_file.getvalue()
                        text = extract_text(uploaded_file.name, file_bytes)

                        if not text.strip():
                            status_area.warning(
                                f"⚠️ {uploaded_file.name}: テキストを抽出できませんでした（スキップ）"
                            )
                        else:
                            result = review_document(text, GEMINI_API_KEY)
                            summary = summarize_result(result)
                            file_type = uploaded_file.name.split(".")[-1]
                            db.save_review(supabase, uploaded_file.name, file_type, summary, result)
                            status_area.write(f"✅ {uploaded_file.name}: {summary}")
                    except Exception as e:
                        error_count += 1
                        status_area.error(f"❌ {uploaded_file.name}: エラーが発生しました（{e}）")

                    progress.progress((i + 1) / len(uploaded_files))

                if error_count == 0:
                    st.success("すべてのファイルのレビューが完了しました。一覧に移動します...")
                else:
                    st.warning(
                        f"{len(uploaded_files) - error_count}件成功、{error_count}件エラーが発生しました。一覧に移動します..."
                    )

                st.session_state["_pending_view"] = VIEW_HISTORY
                st.rerun()

# --- レビュー一覧 -----------------------------------------------------------
else:
    st.subheader("これまでのレビュー結果")

    if st.button("🔄 一覧を更新"):
        st.rerun()

    reviews = db.list_reviews(supabase)

    if not reviews:
        st.write("まだレビュー結果がありません。")
    else:
        list_df = pd.DataFrame(reviews)[["file_name", "file_type", "summary", "created_at"]]
        list_df.columns = ["ファイル名", "種別", "サマリー", "実行日時"]

        st.caption("表の行をクリックすると詳細が表示されます。")
        event = st.dataframe(
            list_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        selected_rows = event.selection.rows if event and event.selection else []

        if not selected_rows:
            st.info("上の表から行を選択してください。")
        else:
            selected_id = reviews[selected_rows[0]]["id"]
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
                    if st.button("🗑️ 削除", key=f"del_{selected_id}"):
                        db.delete_review(supabase, selected_id)
                        st.rerun()

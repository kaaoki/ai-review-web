# 文書自動レビューツール（Webアプリ版）

Gemini APIを使って複数フォーマットの文書を自動レビューし、結果を永続保存・一覧参照できるWebアプリです。
CLI版（[AI-Auto-Review-System](https://github.com/kaaoki/AI-Auto-Review-System)）で培った自動レビューのロジックを、Streamlitベースの実用的なWebアプリとして発展させたものです。

## 概要

- 複数ファイルをまとめてアップロードし、一括でAIレビューを実行
- レビュー観点は「誤字脱字」「事実関係の誤り」「文章内の矛盾」「フォーマット・表記ゆれ」の4つ
- レビュー結果はSupabase（PostgreSQL）に永続保存され、ブラウザや端末を変えても参照可能
- 一覧表から行をクリックするだけで、その場でレビュー詳細を表示
- 簡易パスワード認証付きで、ポートフォリオとして安全にURL公開できる

## デモの流れ

1. パスワードを入力して入室
2. 「アップロード」画面でファイルを選択し、レビューを実行
3. 完了すると自動的に「レビュー一覧」画面に切り替わる
4. 一覧表の行をクリックすると、指摘事項の詳細（該当箇所・指摘内容・修正提案・重要度）が表示される

## 使用技術

| 分類 | 技術 |
|---|---|
| フロントエンド／バックエンド | Streamlit |
| AIレビュー | Gemini API（`google-genai` SDK、構造化JSON出力） |
| データ永続化 | Supabase（PostgreSQL、無料枠） |
| ファイル抽出 | python-docx／openpyxl／pdfplumber（.docx／.xlsx／.pdf／.txt／.md に対応） |
| データ加工・表示 | pandas |
| デプロイ | Streamlit Community Cloud |

## 対応ファイル形式

`.txt` `.md` `.docx` `.xlsx` `.xlsm` `.pdf`

## 使い方（デプロイ）

セットアップからStreamlit Community Cloudへの公開までの手順は [README_DEPLOY.md](./README_DEPLOY.md) にまとめています。Supabaseプロジェクトの作成、テーブル定義（`supabase_schema.sql`）の実行、Secretsの設定までを一通り記載しています。

ローカルで動かす場合：

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml を編集して APP_PASSWORD / GEMINI_API_KEY / SUPABASE_URL / SUPABASE_KEY を設定
streamlit run app.py
```

## 設計上の工夫

**複数フォーマットの統一的な扱い**
`.docx`・`.xlsx`・`.pdf`など形式の異なるファイルを、共通のテキスト抽出インターフェース（`review_engine.extract_text`）で一本化。レビューロジック側はフォーマットの違いを意識せずに済む構成にしている。

**構造化出力によるレビュー結果の一貫性**
Gemini APIに`response_mime_type: application/json`を指定し、指摘事項を`{location, content, suggestion, severity}`の固定スキーマで出力させることで、一覧表示・DB保存・重要度別の集計を安定して行えるようにしている。

**一時的なAPI混雑への耐性**
Gemini API側の一時的な混雑（503）やレート制限（429）に対し、指数バックオフ（5秒→10秒→20秒）による自動リトライを実装。ユーザー操作を必要とせずに大半の一時エラーを吸収する。

**速度とコストのバランスを考慮したモデル選定**
標準モデルと軽量モデル（Flash-Lite）を比較検証した上で、体感速度と安定性を優先しFlash-Lite系をデフォルトに採用。環境変数`GEMINI_MODEL`で切り替え可能にしており、モデル更新にも追従しやすい設計にしている。

**Streamlitの制約を踏まえた画面遷移設計**
Streamlitの`st.tabs`はコードから能動的に切り替えられない制約があるため、`st.segmented_control`とセッション状態を組み合わせて自前のナビゲーションを実装。レビュー完了後に一覧画面へ自動遷移する体験を実現している。また、ウィジェットに紐づくセッション状態を実行中に直接書き換えられない制約に対しては、「切り替え予約用の別キー」を経由させることで回避している。

**クリック操作による直感的な詳細表示**
一覧表を`st.dataframe`の行選択機能（`on_select="rerun"`）で受け、プルダウン選択を挟まずに行クリックだけで詳細を表示できるようにしている。

**最小限の公開制御**
Gemini APIキーを利用する都合上、URLを知っていれば誰でも実行できてしまうことを踏まえ、簡易パスワード認証を設けてAPIクォータの無制限な消費を防いでいる。

## 今後の拡張案

- レビュー結果のExcel／PDFエクスポート
- ファイルごとのレビュー履歴比較（差分表示）
- 重要度でのフィルタリング・検索機能

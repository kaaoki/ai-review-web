# デプロイ手順（Streamlit Community Cloud + Supabase）

サーバーを自分で用意しなくても、無料の範囲でWeb公開できます。全体の流れは次の3ステップです。

1. Supabase（無料DB）を用意する
2. コードをGitHubにpushする
3. Streamlit Community Cloudでデプロイする

---

## 1. Supabaseのセットアップ

1. https://supabase.com にアクセスし、GitHubアカウント等でサインアップ
2. 「New Project」から新規プロジェクトを作成
   - Project name: 任意（例: `ai-review-webapp`）
   - Database Password: 任意の強いパスワードを設定（控えておく）
   - Region: `Northeast Asia (Tokyo)` を推奨
3. プロジェクト作成後、左メニューの **SQL Editor** を開き、同梱の `supabase_schema.sql` の内容を貼り付けて実行
   - `reviews` テーブルが作成されます
4. 左メニューの **Project Settings > API** を開き、以下をメモする
   - `Project URL` → `SUPABASE_URL`
   - `anon public` キー → `SUPABASE_KEY`

## 2. GitHubへのpush

このフォルダ一式（`app.py`, `db.py`, `review_engine.py`, `requirements.txt`, `supabase_schema.sql`, `.gitignore` など）を、既存のポートフォリオと同じ要領で新規リポジトリとしてGitHubにpushしてください。

**重要:** `.streamlit/secrets.toml`（実際のキーが入ったファイル）は絶対にpushしないでください。`.gitignore` に含めてあるので、誤って `git add -f` などしない限り大丈夫です。GitHubにpushされるのは `secrets.toml.example`（テンプレート）だけにしてください。

## 3. Streamlit Community Cloudでデプロイ

1. https://share.streamlit.io にアクセスし、GitHubアカウントでログイン
2. 「New app」から、pushしたリポジトリ・ブランチ・`app.py` を指定してデプロイ
3. デプロイ後、アプリ管理画面の **Settings > Secrets** を開き、次の内容を貼り付けて保存
   ```toml
   APP_PASSWORD = "任意のパスワード"
   GEMINI_API_KEY = "Gemini APIキー"
   SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
   SUPABASE_KEY = "Supabaseのanon key"
   ```
4. 保存すると自動的に再起動し、発行されたURL（例: `https://your-app.streamlit.app`）でアクセスできるようになります

## ローカルで動作確認する場合

```bash
cd webapp
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml を編集して実際の値を入れる
streamlit run app.py
```

## 運用上の注意（ポートフォリオとして見せる際）

- パスワードは簡易的なものです。本格的な認証（メール認証等）が必要な業務利用には向きません。あくまでポートフォリオ閲覧者向けの軽い保護として使ってください。
- Gemini APIは無料枠にもレート制限があります。閲覧者に何度も試されるとその日の枠を使い切る可能性があるため、README等に「デモ利用は1〜2回程度でお願いします」と一言添えておくと安心です。
- Streamlit Community Cloudの無料プランは、しばらくアクセスがないとアプリがスリープします。面接や応募の直前に一度アクセスして起動確認しておくと親切です。
- Supabaseの無料プランはプロジェクトが一定期間完全に非アクティブだと一時停止されることがあります。応募前に一度動作確認をおすすめします。

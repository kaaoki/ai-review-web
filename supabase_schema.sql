-- Supabaseの「SQL Editor」でこのまま実行してください。
-- reviews テーブル: 文書レビュー結果を1件ずつ保存する

create table if not exists reviews (
    id uuid primary key default gen_random_uuid(),
    file_name text not null,
    file_type text,
    summary text,
    result_json jsonb not null,
    created_at timestamptz not null default now()
);

-- 一覧取得を新しい順で行うためのインデックス
create index if not exists reviews_created_at_idx on reviews (created_at desc);

-- 【任意】Row Level Security（RLS）について
-- このアプリはアプリ側の簡易パスワードのみで保護しており、
-- Supabaseへの接続には anon key を使います。
-- anon keyはクライアント（このアプリ）から見える前提のキーのため、
-- 本番運用や機密データを扱う場合は、Supabase側でもRLSを有効にし、
-- 適切なポリシーを設定することを推奨します（ポートフォリオデモ用途では必須ではありません）。
--
-- 例）RLSを有効化し、anonロールに全操作を許可する場合：
-- alter table reviews enable row level security;
-- create policy "allow all for anon" on reviews
--   for all
--   to anon
--   using (true)
--   with check (true);

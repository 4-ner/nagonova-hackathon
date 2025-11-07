# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

RFP Radarは、FastAPI（バックエンド）とNext.js + shadcn/ui（フロントエンド）を組み合わせたモノレポ構成のアプリケーションです。データベースにはSupabaseを使用しています。

## アーキテクチャ構成

```
apps/
  api/          # FastAPI バックエンド
  web/          # Next.js フロントエンド（App Router使用）
supabase/
  sql/          # データベーススキーマとRLSポリシー
infra/          # インフラ・デプロイ設定（現在は空）
```

### フロントエンド（apps/web）

- **フレームワーク**: Next.js 16 (App Router)
- **スタイリング**: Tailwind CSS v4 + shadcn/ui (new-york style)
- **ランタイム**: React 19
- **UIコンポーネント**: shadcn/ui を使用（`components.json`で設定）
- **パスエイリアス**:
  - `@/components` → src/components/
  - `@/lib` → src/lib/
  - `@/hooks` → src/hooks/

### Directory Structure

The frontend follows a **Feature-based directory structure** pattern:

```
apps/web/src/
├── app/                      # Next.js App Router pages
│   ├── (dashboard)/          # Authenticated route group
│   └── login/                # Public login page
├── features/                 # Feature modules
│   ├── auth/                 # Authentication feature
│   └── users/                # User management feature
│       ├── components/       # Feature-specific components
│       ├── hooks/            # Feature-specific hooks
│       ├── types/            # Feature-specific types
│       ├── schemas/          # Validation schemas (Zod)
│       └── utils/            # Feature utilities
├── components/               # Shared components
│   ├── layout/               # Layout components
│   └── ui/                   # shadcn/ui components
├── hooks/                    # Global custom hooks
├── lib/                      # Utilities and helpers
└── providers/                # React Context providers
```
#### Component Design

- Use **shadcn/ui** as the base UI component library
- All components are **Client Components** by default (use `'use client'` directive)
- Use **TypeScript strict mode** for type safety
- Import paths use `@/` alias for absolute imports

#### State Management

- **SWR** - Server state caching and synchronization
  - Use `useApi` hook for GET requests
  - Use `useApiMutation` hook for POST/PUT/DELETE requests
- **React Context** - Global state (authentication, theme)
- **React Hook Form + Zod** - Form state and validation

### バックエンド（apps/api）

- **フレームワーク**: FastAPI
- **Python**: 3.13（`.python-version`で指定）
- **主要依存**: uvicorn, supabase, python-dotenv, pandas
- **起動方法**: uvxを使用

### データベース

- **Supabase**: PostgreSQL + Row Level Security (RLS)
- **スキーマ定義**: `supabase/sql/init.sql`（現在は空テンプレート）

## 必須コマンド

### 環境セットアップ

```bash
# Node.js バージョン確認（v22.21.1を使用）
node --version

# 環境変数設定
cp .env.example .env
# .envを編集してSupabaseの認証情報を設定
```

### 開発サーバー起動

```bash
# Webフロントエンド（apps/web）
cd apps/web
pnpm install
pnpm dev
# → http://localhost:3000

# APIバックエンド（apps/api）
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload  # または uvx を使用
# → http://localhost:8000
```

### ビルドとリント

```bash
# Webアプリのビルド
cd apps/web
pnpm build

# Webアプリのリント
cd apps/web
pnpm lint
```

## タスク管理

このプロジェクトでは、**Notion Nagonova**を使用してタスク管理を行います。

### Nagonovaデータベース構成

- **データベースID**: `2a4e9670-1260-80b2-bc26-d3c24be611ea`
- **URL**: https://www.notion.so/2a4e9670126080b2bc26d3c24be611ea

### タスクプロパティ

- **タスク名**: タスクの概要
- **ステータス**: 未着手 / 進行中 / 完了
- **優先度**: 高 / 中 / 低
- **工数レベル**: 小 / 中 / 大
- **タスクの種類**: 🐞 バグ / 💬 機能リクエスト / 💅 仕上げ
- **期日**: タスクの期限
- **担当者**: タスクの担当者
- **説明**: タスクの詳細説明

### タスク管理フロー

1. **仕様検討**: 新機能や変更の仕様をNagonovaに記載
2. **開発タスク登録**: 仕様に基づいて具体的な開発タスクを作成
3. **タスク実施**: ステータスを「進行中」に更新して開発を進める
4. **完了報告**: 実装完了後、ステータスを「完了」に更新

### タスク着手時のワークフロー（GitHub Flow）

1. タスクの状態を「着手中」に変更
2. タスクの開始日時を設定 (時間まで記載すること)
3. Git で main からブランチを作成 (ブランチ名は`feature/<タスクID>`とする)
4. 空コミットを作成 (コミットメッセージは`chore: start feature/<タスクID>`とする)
5. PR を作成 (`gh pr create --assignee @me --base main --draft`)
  - タイトルはタスクのタイトルを参照する (`【<タスクID>】<タイトル>`)
  - ボディはタスクの内容から生成する (Notion タスクへのリンクを含める)
6. 実装計画を考えて、ユーザーに伝える
7. ユーザーにプロンプトを返す

### タスク完了時のワークフロー（GitHub Flow）

1. PR のステータスを ready にする
2. PR をマージ (`gh pr merge --merge --auto --delete-branch`)
3. タスクの完了日時を設定 (時間まで記載すること)
4. タスクに「サマリー」を追加
  - コマンドライン履歴とコンテキストを参照して、振り返りを効率化するための文章を作成
  - Notion の見出しは「振り返り」とする
5. タスクの状態を「完了」に変更
6. ユーザーにプロンプトを返す

### Claude Codeからのアクセス

Claude CodeはNotion APIを通じてNagonovaのタスク一覧を取得・更新できます。タスクの確認や更新を行う際は、Claude Codeに依頼してください。

## 開発時の注意点

### 環境変数

以下の環境変数が必須：
- `SUPABASE_URL`: SupabaseプロジェクトURL
- `SUPABASE_ANON_KEY`: Supabase匿名キー
- `SUPABASE_SERVICE_KEY`: Supabaseサービスキー
- `NEXT_PUBLIC_API_BASE_URL`: APIエンドポイント（デフォルト: http://localhost:8000）

### shadcn/uiコンポーネント追加

```bash
cd apps/web
pnpx shadcn@latest add <component-name>
```

設定は`components.json`で管理されており、new-yorkスタイルを使用しています。

### API開発

- FastAPIアプリのメインファイル: `apps/api/main.py`（存在する場合）
- Supabaseクライアントを使用してデータベースと連携
- 環境変数は`.env`から`python-dotenv`で読み込み

### データベーススキーマ変更

1. `supabase/sql/init.sql`にSQL文を追加
2. Supabase DashboardのSQL Editorで実行、またはSupabase CLIを使用してマイグレーション
3. RLSポリシーの設定も忘れずに行う

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

RFP Radarは、FastAPI（バックエンド）とNext.js + shadcn/ui（フロントエンド）を組み合わせたモノレポ構成のアプリケーションです。データベースにはSupabaseを使用し、包括的なテストスイートを備えています。

### プロジェクトステータス

**✅ 全7フェーズ完了** - フル機能実装済み、テストカバレッジ充実、プロダクションレディ

## アーキテクチャ構成

```
apps/
  api/                      # FastAPI バックエンド
  │ ├── routers/           # APIエンドポイント
  │ ├── services/          # ビジネスロジック
  │ ├── schemas/           # Pydanticスキーマ
  │ ├── middleware/        # 認証・エラーハンドリング
  │ ├── templates/         # Jinja2テンプレート
  │ ├── tests/             # テストスイート (pytest)
  │ │   ├── fixtures/      # RLSテスト用フィクスチャ
  │ │   └── *.py          # 各種テストファイル
  │ ├── pyproject.toml    # uv依存関係管理
  │ └── pytest.ini        # pytest設定
  │
  web/                      # Next.js フロントエンド
    ├── src/
    │   ├── app/           # App Router
    │   ├── features/      # 機能別モジュール
    │   ├── components/    # 共有コンポーネント
    │   ├── hooks/         # カスタムフック
    │   └── lib/           # ユーティリティ
    ├── e2e/               # Playwright E2Eテスト
    │   ├── fixtures/      # 認証ヘルパー
    │   └── *.spec.ts      # テストスイート
    ├── playwright.config.ts # Playwright設定
    └── jest.config.ts     # Jest設定

supabase/
  sql/                     # データベーススキーマとRLSポリシー

infra/                     # インフラ・デプロイ設定（未実装）
```

## 技術スタック

### フロントエンド（apps/web）

- **フレームワーク**: Next.js 16.0.1 (App Router)
- **ランタイム**: React 19
- **スタイリング**: Tailwind CSS v4 + shadcn/ui (new-york style)
- **状態管理**: SWR + React Context
- **フォーム**: React Hook Form + Zod
- **テスト**:
  - Playwright v1.56.1 - E2Eテスト
  - Jest + React Testing Library - ユニットテスト
- **パスエイリアス**:
  - `@/components` → src/components/
  - `@/lib` → src/lib/
  - `@/hooks` → src/hooks/
  - `@/features` → src/features/

### バックエンド（apps/api）

- **フレームワーク**: FastAPI v0.115.0+
- **Python**: 3.13（`.python-version`で指定）
- **パッケージ管理**: **uv** (pyproject.toml使用)
- **主要依存**:
  - uvicorn[standard] - ASGIサーバー
  - supabase - データベースクライアント
  - python-dotenv - 環境変数
  - pydantic-settings - 設定管理
- **テスト**: pytest v8.3.0+ (asyncio対応)
- **認証**: Supabase Auth (JWT)

### データベース

- **Supabase**: PostgreSQL + Row Level Security (RLS)
- **pgvector**: セマンティック検索用ベクトル埋め込み
- **RLSポリシー**: 6テーブル（companies, company_documents, rfps, bookmarks, match_snapshots, company_skill_embeddings）

## 環境変数設定

### 必須環境変数（`.env`）

```env
# Supabase設定（必須）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Next.js環境変数（必須）
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here

# API設定（オプション - デフォルト値あり）
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### E2Eテスト用環境変数（`apps/web/.env.test`）

```env
# E2Eテストユーザー認証情報（必須）
E2E_TEST_USER_EMAIL=test@example.com
E2E_TEST_USER_PASSWORD=test-password-123!Aa

# Playwright設定（オプション）
PLAYWRIGHT_BASE_URL=http://localhost:3000
```

## 開発ガイド

### 環境セットアップ

```bash
# Node.js バージョン確認（v22.21.1を使用）
node --version

# 環境変数設定
cp .env.example .env
# .envを編集してSupabaseの認証情報を設定

# E2Eテスト用環境変数設定（必要に応じて）
cd apps/web
cp .env.test.example .env.test
# E2Eテストユーザー情報を設定
```

### 開発サーバー起動

```bash
# Webフロントエンド（apps/web）
cd apps/web
pnpm install
pnpm dev
# → http://localhost:3000

# APIバックエンド（apps/api）- uvを使用
cd apps/api
uv pip sync                          # 依存関係インストール
uvx uvicorn main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs (API仕様書)
```

### テスト実行

#### フロントエンド（apps/web）

```bash
cd apps/web

# ユニットテスト
pnpm test                   # Jest実行
pnpm test:coverage         # カバレッジ付き

# E2Eテスト（Playwright）
pnpm test:e2e              # ヘッドレス実行（CI向け）
pnpm test:e2e:ui           # UIモード（対話的デバッグ）
pnpm test:e2e:debug        # デバッグモード
pnpm test:e2e:headed       # ブラウザ表示モード
pnpm test:e2e:chromium     # Chromiumのみ実行

# Playwrightブラウザインストール（初回のみ）
pnpx playwright install
```

#### バックエンド（apps/api）- uvを使用

```bash
cd apps/api

# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov

# RLSポリシーテスト（要Service Key）
uv run pytest tests/test_rls_policies.py -v -m rls

# 特定のマーカーでフィルタ
uv run pytest -m unit        # ユニットテストのみ
uv run pytest -m integration # 統合テストのみ

# 並列実行（高速化）
uv run pytest -n auto
```

### ビルドとリント

```bash
# Webアプリのビルド
cd apps/web
pnpm build
pnpm lint

# Pythonコードのフォーマット（バックエンド）
cd apps/api
ruff check .
ruff format .
```

## テストインフラストラクチャ

### E2Eテストスイート（Playwright）

| テストファイル | テスト数 | カバレッジ |
|--------------|---------|-----------|
| auth.spec.ts | 7 | 認証フロー全体 |
| rfps.spec.ts | 10 | RFP一覧・詳細・フィルタ |
| bookmarks.spec.ts | 8 | ブックマーク機能 |
| proposal.spec.ts | 10 | 提案ドラフト生成 |
| **合計** | **34** | **主要機能全て** |

### RLSポリシーテスト（pytest）

| テーブル | テスト数 | ポリシー |
|---------|---------|----------|
| companies | 6 | ユーザーは自分の会社のみCRU可能 |
| company_documents | 5 | 同一会社のユーザーのみCRUD可能 |
| rfps | 6 | 全認証ユーザーがR可能 |
| bookmarks | 5 | ユーザーは自分のブックマークのみCRD可能 |
| match_snapshots | 5 | ユーザーはR可能、CDはservice_roleのみ |
| company_skill_embeddings | 5 | ユーザーはR可能、CUDはservice_roleのみ |
| **合計** | **32** | **完全なアクセス制御** |

## 実装済み主要機能

### 認証・ユーザー管理
- ✅ Supabase Auth（メールOTP認証）
- ✅ ユーザー登録・ログイン
- ✅ セッション管理

### 会社プロフィール
- ✅ 会社情報登録・更新
- ✅ スキル・対応地域・予算範囲設定
- ✅ NG条件設定

### ドキュメント管理
- ✅ ファイルアップロード（Supabase Storage）
- ✅ ドキュメント一覧・削除
- ✅ タグ付けと分類

### RFP案件管理
- ✅ 案件一覧表示（ページネーション対応）
- ✅ 詳細表示
- ✅ 地域・予算・キーワードフィルタリング

### マッチング機能
- ✅ ハイブリッドマッチング（pgvector + キーワード）
- ✅ マッチングスコア計算
- ✅ スコア要因の可視化
- ✅ Must/NG条件チェック

### ブックマーク
- ✅ 案件のブックマーク保存
- ✅ ブックマーク一覧
- ✅ ブックマーク解除

### 提案ドラフト生成
- ✅ Jinja2テンプレートベース
- ✅ Markdownプレビュー
- ✅ コピー・ダウンロード機能

## タスク管理（Notion Nagonova）

### Nagonovaデータベース構成

- **データベースID**: `2a4e9670-1260-80b2-bc26-d3c24be611ea`
- **URL**: https://www.notion.so/2a4e9670126080b2bc26d3c24be611ea

### 完了フェーズ

| フェーズ | タスク名 | ステータス |
|---------|---------|-----------|
| 0 | 環境構築・基盤整備 | ✅ 完了 |
| 1 | 認証・プロフィール管理 | ✅ 完了 |
| 2 | 会社ドキュメント管理 | ✅ 完了 |
| 3 | RFPデータ取得（KKJ API） | ✅ 完了 |
| 4 | スコアリング・マッチング | ✅ 完了 |
| 5 | 案件一覧・詳細画面 | ✅ 完了 |
| 6 | 提案ドラフト生成 | ✅ 完了 |
| 7 | 統合テスト・仕上げ | ✅ 完了 |

### タスク着手時のワークフロー（GitHub Flow）

1. タスクの状態を「進行中」に変更
2. タスクの開始日時を設定
3. Git で main からブランチを作成 (`feature/<タスクID>`)
4. 空コミットを作成 (`chore: start feature/<タスクID>`)
5. PR を作成 (`gh pr create --assignee @me --base main --draft`)
6. 実装計画を立案
7. ユーザーにプロンプトを返す

### タスク完了時のワークフロー

1. PR のステータスを ready にする
2. コードレビュー実施（プラグイン利用推奨）
3. PR をマージ (`gh pr merge --merge --delete-branch`)
4. タスクの完了日時を設定
5. タスクに「振り返り」セクション追加
6. タスクの状態を「完了」に変更

## 開発時の注意点

### Python依存関係管理 - uvを使用

```bash
# 依存関係インストール
uv pip sync                   # pyproject.tomlから
uv pip install -r requirements.txt  # requirements.txtから

# 新しいパッケージ追加
uv pip install <package>
uv pip freeze > requirements.txt    # 更新

# 開発用依存関係
uv pip install --dev pytest httpx
```

### shadcn/uiコンポーネント追加

```bash
cd apps/web
pnpx shadcn@latest add <component-name>
```

設定は`components.json`で管理（new-yorkスタイル使用）

### API開発

- FastAPIアプリのメインファイル: `apps/api/main.py`
- Supabaseクライアントを使用してデータベースと連携
- 環境変数は`python-dotenv`で`.env`から読み込み
- API仕様書: http://localhost:8000/docs (開発環境のみ)

### データベーススキーマ変更

1. `supabase/sql/`にSQL文を追加
2. Supabase DashboardのSQL Editorで実行
3. RLSポリシーの設定を忘れずに行う
4. RLSテストを更新・実行（`uv run pytest tests/test_rls_policies.py`）

### E2Eテストデータの準備

1. Supabaseでテストユーザーを作成
2. `apps/web/.env.test`に認証情報を設定
3. テスト実行前にdev serverを起動
4. `pnpm test:e2e`でテスト実行

## トラブルシューティング

### E2Eテストが失敗する場合

```bash
# Playwrightブラウザを再インストール
pnpx playwright install

# 環境変数確認
cd apps/web
cat .env.test  # E2E_TEST_USER_EMAIL/PASSWORDが設定されているか

# デバッグモードで実行
pnpm test:e2e:debug
```

### RLSテストが失敗する場合

```bash
# Service Keyが設定されているか確認
echo $SUPABASE_SERVICE_KEY

# verboseモードで実行
uv run pytest tests/test_rls_policies.py -vvs

# 特定のテストのみ実行
uv run pytest tests/test_rls_policies.py::TestCompaniesRLS -v
```

### Python依存関係の問題

```bash
# uvのキャッシュクリア
uv cache clean

# 仮想環境を再作成
rm -rf .venv
uv venv
uv pip sync
```

## 今後の展望

- CI/CDパイプライン統合（GitHub Actions）
- 本番環境デプロイ（Vercel + Fly.io）
- パフォーマンスモニタリング（Sentry）
- 負荷テスト実装（Locust）
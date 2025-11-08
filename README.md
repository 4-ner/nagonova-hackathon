# RFP Radar

会社情報とスキルに基づいて官公需の入札案件（RFP: Request for Proposal）をマッチングするシステム

## 技術スタック

### バックエンド
- **FastAPI** (Python 3.13) - 高速なWeb APIフレームワーク
- **Supabase** - PostgreSQL + Row Level Security (RLS)
- **pgvector** - セマンティック検索のためのベクトル埋め込み
- **Jinja2** - 提案書テンプレートエンジン

### フロントエンド
- **Next.js 16** (App Router) - React フレームワーク
- **React 19** - UI ライブラリ
- **shadcn/ui** (new-york style) - UI コンポーネントライブラリ
- **Tailwind CSS v4** - ユーティリティファーストCSS
- **SWR** - データフェッチング・キャッシング

### テスト
- **Playwright** - E2Eテスト
- **Jest** + React Testing Library - フロントエンドユニットテスト
- **pytest** - バックエンドユニットテスト

## 必要な環境

- **Node.js**: v22.21.1
- **Python**: 3.13
- **pnpm**: 9.x
- **uv**: Python パッケージマネージャー
- **Supabase アカウント**

## セットアップ手順

### 1. リポジトリクローン

```bash
git clone https://github.com/4-ner/nagonova-hackathon.git
cd nagonova-hackathon
```

### 2. 環境変数設定

```bash
cp .env.example .env
```

`.env`ファイルを編集してSupabase認証情報を設定：

```env
# Supabase設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Next.js環境変数
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

### 3. データベーススキーマ適用

Supabase Dashboard → SQL Editor で `supabase/sql/init.sql` を実行

### 4. バックエンド起動

```bash
cd apps/api

# 依存関係インストール（uv使用）
uv pip install -r requirements.txt

# 開発サーバー起動
uvx uvicorn main:app --reload --port 8000
```

APIドキュメント: http://localhost:8000/docs

### 5. フロントエンド起動

```bash
cd apps/web

# 依存関係インストール
pnpm install

# 開発サーバー起動
pnpm dev
```

アプリケーション: http://localhost:3000

## 開発ガイド

### テスト実行

#### フロントエンド

```bash
cd apps/web

# ユニットテスト
pnpm test

# カバレッジ付きテスト
pnpm test:coverage

# E2Eテスト
pnpx playwright test

# E2Eテスト（UIモード）
pnpm test:e2e:ui
```

#### バックエンド

```bash
cd apps/api

# ユニットテスト（uv使用）
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov

# RLSポリシーテスト
uv run pytest tests/test_rls_policies.py -v
```

### コードフォーマット・リント

```bash
# フロントエンド
cd apps/web
pnpm lint

# バックエンド
cd apps/api
ruff check .
ruff format .
```

### shadcn/uiコンポーネント追加

```bash
cd apps/web
pnpx shadcn@latest add <component-name>
```

## プロジェクト構成

```
.
├── apps/
│   ├── api/              # FastAPI バックエンド
│   │   ├── routers/      # APIエンドポイント
│   │   ├── services/     # ビジネスロジック
│   │   ├── schemas/      # Pydanticスキーマ
│   │   ├── middleware/   # 認証・エラーハンドリング
│   │   ├── templates/    # Jinja2テンプレート
│   │   └── tests/        # テストコード
│   │
│   └── web/              # Next.js フロントエンド
│       ├── src/
│       │   ├── app/      # App Router ページ
│       │   ├── components/ # 共有コンポーネント
│       │   ├── features/ # 機能別モジュール
│       │   ├── hooks/    # カスタムフック
│       │   └── lib/      # ユーティリティ
│       └── e2e/          # E2Eテスト
│
├── supabase/
│   └── sql/              # データベーススキーマ
│
└── infra/                # インフラ設定（未使用）
```

## 主要機能

### 1. 会社プロフィール管理
- 会社情報、スキル、対応地域、予算範囲の登録・更新
- `/profile/setup` - プロフィール初期設定
- `/profile/edit` - プロフィール編集

### 2. ドキュメント管理
- 会社の実績書類や提案書のアップロード・管理
- Supabase Storageを使用したファイル保存
- `/documents` - ドキュメント一覧・管理

### 3. RFP案件閲覧
- 官公需入札案件の一覧表示、詳細確認
- 地域・予算・キーワードによるフィルタリング
- `/rfps` - RFP一覧
- `/rfps/[id]` - RFP詳細

### 4. マッチング機能
- セマンティック検索による案件とスキルのマッチングスコア計算
- pgvectorを使用したベクトル類似度検索
- マッチングスコアの可視化

### 5. ブックマーク
- 気になる案件のブックマーク保存
- ブックマーク一覧の確認

### 6. 提案ドラフト生成
- RFP案件に対する提案書のドラフト自動生成
- Jinja2テンプレートを使用
- Markdownプレビュー、コピー・ダウンロード機能
- `/rfps/[id]/proposal` - 提案ドラフト生成

## API エンドポイント

詳細は http://localhost:8000/docs を参照

### 会社プロフィール
- `GET /api/companies/me` - 自分の会社情報取得
- `POST /api/companies` - 会社情報作成
- `PUT /api/companies/me` - 会社情報更新

### ドキュメント
- `GET /api/documents` - ドキュメント一覧
- `POST /api/documents` - ドキュメントアップロード
- `DELETE /api/documents/{id}` - ドキュメント削除

### RFP案件
- `GET /api/rfps` - RFP一覧（フィルタリング対応）
- `GET /api/rfps/{id}` - RFP詳細
- `GET /api/rfps/with-matching` - マッチングスコア付きRFP一覧
- `GET /api/rfps/{id}/proposal/draft` - 提案ドラフト生成

### ブックマーク
- `GET /api/bookmarks` - ブックマーク一覧
- `POST /api/bookmarks` - ブックマーク追加
- `DELETE /api/bookmarks/rfp/{rfp_id}` - ブックマーク削除
- `GET /api/bookmarks/check/{rfp_id}` - ブックマーク状態確認

### マッチング
- `POST /api/matching/calculate` - マッチングスコア計算
- `GET /api/matching/snapshots` - マッチングスナップショット一覧

## セキュリティ

### Row Level Security (RLS)
Supabaseデータベースレベルでのアクセス制御を実装：

- **companies**: ユーザーは自分の会社のみCRU可能
- **company_documents**: 同一会社のユーザーのみCRUD可能
- **rfps**: 全認証ユーザーがR可能、CUDはservice_roleのみ
- **bookmarks**: ユーザーは自分のブックマークのみCRD可能
- **match_snapshots**: ユーザーはR可能、CDはservice_roleのみ

### 認証
- Supabase Authを使用したJWT認証
- すべての保護されたエンドポイントでトークン検証

## トラブルシューティング

### バックエンドが起動しない

1. Python バージョン確認: `python --version` (3.13が必要)
2. uv インストール確認: `uv --version`
3. 環境変数確認: `.env`ファイルが存在し、正しい値が設定されているか
4. Supabase接続確認: http://localhost:8000/health

### フロントエンドが起動しない

1. Node.js バージョン確認: `node --version` (v22.21.1が必要)
2. pnpm インストール確認: `pnpm --version`
3. 依存関係再インストール: `rm -rf node_modules && pnpm install`
4. キャッシュクリア: `rm -rf .next`

### E2Eテストが失敗する

1. 開発サーバーが起動しているか確認
2. 環境変数が正しく設定されているか確認
3. Playwrightブラウザインストール: `pnpx playwright install`

## ライセンス

MIT

## コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずIssueで議論してください。

## リンク

- [GitHub Repository](https://github.com/4-ner/nagonova-hackathon)
- [API Documentation](http://localhost:8000/docs)

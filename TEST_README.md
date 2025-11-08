# RFP Radar テストガイド

このドキュメントでは、RFP Radarアプリケーションのテスト構成と実行方法について説明します。

## テスト構成概要

### バックエンド (FastAPI)
- **テストフレームワーク**: pytest
- **テスト場所**: `apps/api/tests/`
- **カバレッジ**: ブックマークAPI、RFPフィルターAPI

### フロントエンド (Next.js + React)
- **テストフレームワーク**: Jest + React Testing Library
- **テスト場所**: `apps/web/src/**/__tests__/`
- **カバレッジ**: ブックマーク機能（カスタムフック、コンポーネント）

## バックエンドテストの実行

### 環境準備

```bash
cd apps/api

# テスト用の依存関係をインストール
uv pip install -r requirements-dev.txt
```

### テスト実行コマンド

```bash
# すべてのテストを実行
uv run pytest tests/ -v

# カバレッジレポート付きで実行
uv run pytest tests/ -v --cov=. --cov-report=html

# 特定のテストファイルのみ実行
uv run pytest tests/test_bookmarks.py -v

# 特定のテストケースのみ実行
uv run pytest tests/test_bookmarks.py::TestCreateBookmark::test_ブックマーク作成_正常系 -v

# カバレッジなしで実行（高速）
uv run pytest tests/ -v --no-cov
```

### バックエンドテストの内容

#### ブックマークAPI (`tests/test_bookmarks.py`)
- ✅ ブックマーク作成（正常系）
- ✅ RFPが存在しない場合のエラー処理
- ✅ 既存ブックマークの冪等性確認
- ✅ ブックマーク削除（正常系）
- ✅ 存在しないブックマークの削除エラー
- ✅ 他ユーザーのブックマーク削除拒否
- ✅ ブックマーク一覧取得
- ✅ 空リスト取得
- ✅ ページネーション機能

#### RFPフィルターAPI (`tests/test_rfps.py`)
- ✅ マッチングスコア付きRFP取得（正常系）
- ✅ 会社情報が存在しない場合のエラー処理
- ✅ 最小スコアフィルタ
- ✅ 必須要件フィルタ
- ✅ 締切日フィルタ（指定日数以内）
- ✅ 予算フィルタ（最小値・最大値）
- ✅ 複数フィルタの組み合わせ
- ✅ 空リスト取得

## フロントエンドテストの実行

### 環境準備

```bash
cd apps/web

# テスト用の依存関係は既にインストール済み
# 必要に応じて再インストール
# pnpm install
```

### テスト実行コマンド

```bash
# すべてのテストを実行
pnpm test

# ウォッチモードで実行（開発時推奨）
pnpm test:watch

# カバレッジレポート付きで実行
pnpm test:coverage

# 特定のテストファイルのみ実行
pnpm test src/features/bookmarks/hooks/__tests__/useBookmarks.test.ts

# 特定のテストスイートのみ実行
pnpm test -- --testNamePattern="useBookmarks"
```

### フロントエンドテストの内容

#### ブックマークカスタムフック (`src/features/bookmarks/hooks/__tests__/useBookmarks.test.ts`)
- ✅ ブックマーク一覧の取得
- ✅ エラーハンドリング
- ✅ クエリパラメータのURL反映
- ✅ RFPのブックマーク済み判定（正常系）
- ✅ RFPの未ブックマーク判定
- ✅ null RFP IDのハンドリング

#### ブックマークボタンコンポーネント (`src/features/bookmarks/components/__tests__/BookmarkButton.test.tsx`)
- ✅ 未ブックマーク状態のレンダリング
- ✅ ブックマーク済み状態のレンダリング
- ✅ アイコンのみモードの表示
- ✅ ローディング中のボタン無効化
- ✅ ブックマーク追加機能
- ✅ ブックマーク追加失敗時のエラー表示
- ✅ ブックマーク削除機能
- ✅ クリックイベントの伝播停止

## テスト設計の原則

### モック戦略
- **バックエンド**: Supabaseクライアント、認証ミドルウェアをモック
- **フロントエンド**: SWRキャッシュ、API呼び出し、ルーター、トースト通知をモック

### テストの重点
1. **正常系**: 主要な機能が正しく動作すること
2. **異常系**: エラーハンドリングが適切に行われること
3. **境界条件**: 空リスト、null値、存在しないデータなど
4. **ユーザーインタラクション**: クリック、フォーム送信など

### カバレッジ目標
- 重要な機能の動作確認を優先
- 100%カバレッジよりも、重要なユースケースのテストを重視

## トラブルシューティング

### バックエンド

**問題**: `ModuleNotFoundError: No module named 'main'`
**解決**: `tests/conftest.py`でPYTHONPATHが正しく設定されているか確認

**問題**: `No module named pytest`
**解決**: `uv pip install pytest` または `uv pip install -r requirements-dev.txt`

### フロントエンド

**問題**: `Cannot find module 'next/jest'`
**解決**: `jest.config.ts`で`next/jest`を使用せず、直接設定を記述

**問題**: `transformIgnorePatterns`エラー
**解決**: `@swc/jest`と`@swc/core`がインストールされているか確認

## CI/CDへの統合

### GitHub Actions 例

```yaml
# バックエンドテスト
- name: Run backend tests
  working-directory: apps/api
  run: |
    uv pip install -r requirements-dev.txt
    uv run pytest tests/ -v --cov=. --cov-report=xml

# フロントエンドテスト
- name: Run frontend tests
  working-directory: apps/web
  run: |
    pnpm install
    pnpm test:coverage
```

## 今後の改善点

- [ ] E2Eテストの追加（Playwright）
- [ ] ビジュアルリグレッションテスト
- [ ] パフォーマンステスト
- [ ] セキュリティテスト（認証・認可）
- [ ] バックエンドの統合テスト（実際のDBを使用）
- [ ] フロントエンドのアクセシビリティテスト

## 参考資料

- [pytest ドキュメント](https://docs.pytest.org/)
- [React Testing Library ドキュメント](https://testing-library.com/react)
- [Jest ドキュメント](https://jestjs.io/)
- [FastAPI テストガイド](https://fastapi.tiangolo.com/tutorial/testing/)

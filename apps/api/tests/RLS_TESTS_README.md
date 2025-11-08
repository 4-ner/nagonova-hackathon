# Row Level Security (RLS) ポリシー動作確認テスト

このディレクトリには、SupabaseデータベースのRow Level Security (RLS) ポリシーが正しく機能していることを確認するテストが含まれています。

## 概要

RLSポリシーテストは、実際のSupabaseデータベースに接続し、以下の6つのテーブルのアクセス制御が適切に動作していることを確認します：

1. **companies** - ユーザーは自分の会社のみCRU可能
2. **company_documents** - 同一会社のユーザーのみCRUD可能
3. **rfps** - 全認証ユーザーがR可能、CUDはservice_roleのみ
4. **bookmarks** - ユーザーは自分のブックマークのみCRD可能
5. **match_snapshots** - ユーザーはR可能、CDはservice_roleのみ
6. **company_skill_embeddings** - ユーザーはR可能、CUDはservice_roleのみ

## 前提条件

### 環境変数の設定

`.env`ファイルに以下の環境変数が設定されている必要があります：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

### Supabaseプロジェクトの設定

RLSテストを実行する前に、Supabaseプロジェクトでデータベーススキーマが正しくセットアップされている必要があります：

```bash
# スキーマの適用
psql -h db.your-project.supabase.co -U postgres -d postgres -f ../../supabase/sql/init.sql
```

または、Supabase DashboardのSQL Editorで`supabase/sql/init.sql`を実行してください。

## テストの実行

### 全RLSテストの実行

```bash
cd apps/api
uv run pytest tests/test_rls_policies.py -v -m rls
```

### 特定のテーブルのテストのみ実行

```bash
# companiesテーブルのみ
uv run pytest tests/test_rls_policies.py::TestCompaniesRLS -v

# company_documentsテーブルのみ
uv run pytest tests/test_rls_policies.py::TestCompanyDocumentsRLS -v

# rfpsテーブルのみ
uv run pytest tests/test_rls_policies.py::TestRfpsRLS -v

# bookmarksテーブルのみ
uv run pytest tests/test_rls_policies.py::TestBookmarksRLS -v

# match_snapshotsテーブルのみ
uv run pytest tests/test_rls_policies.py::TestMatchSnapshotsRLS -v

# company_skill_embeddingsテーブルのみ
uv run pytest tests/test_rls_policies.py::TestCompanySkillEmbeddingsRLS -v
```

### 特定のテストケースのみ実行

```bash
# ユーザーが自分の会社を参照できることを確認
uv run pytest tests/test_rls_policies.py::TestCompaniesRLS::test_user_can_read_own_company -v

# ユーザーが他人の会社を参照できないことを確認
uv run pytest tests/test_rls_policies.py::TestCompaniesRLS::test_user_cannot_read_other_company -v
```

### 詳細なログ出力で実行

```bash
# 標準出力とログを表示
uv run pytest tests/test_rls_policies.py -v -s -m rls

# トレースバックを短く表示
uv run pytest tests/test_rls_policies.py -v --tb=short -m rls
```

## テストの仕組み

### フィクスチャ構成

テストは以下のフィクスチャを使用しています（`tests/fixtures/rls_fixtures.py`）：

#### 基本フィクスチャ

- **`supabase_anon_client`**: 匿名キーで接続したSupabaseクライアント（RLS適用）
- **`supabase_service_client`**: サービスロールキーで接続したSupabaseクライアント（RLS無視）

#### テストユーザーフィクスチャ

- **`test_user_1`**: 主要なテストユーザー（Service Roleで作成、メール確認済み）
- **`test_user_2`**: 「他のユーザー」として使用するテストユーザー

#### 認証済みクライアントフィクスチャ

- **`authenticated_client_1`**: test_user_1でログイン済みのSupabaseクライアント
- **`authenticated_client_2`**: test_user_2でログイン済みのSupabaseクライアント

#### テストデータフィクスチャ

- **`company_user_1`**: test_user_1の会社データ
- **`company_user_2`**: test_user_2の会社データ
- **`rfp_data`**: テスト用RFP案件データ（Service Roleで作成）
- **`company_document_user_1`**: test_user_1の会社ドキュメント
- **`bookmark_user_1`**: test_user_1のブックマーク
- **`match_snapshot_user_1`**: test_user_1のマッチングスナップショット
- **`company_skill_embedding_user_1`**: test_user_1の会社スキル埋め込み

### テストの流れ

1. **セットアップ**: Service Roleクライアントでテストユーザーとデータを作成
2. **テスト実行**: 認証済みクライアントでRLSポリシーを確認
3. **検証**: 期待通りのアクセス制御が動作していることを確認
4. **クリーンアップ**: テストユーザーと関連データを削除（自動）

## テストケース詳細

### 1. companiesテーブル (6テスト)

- ✅ ユーザーは自分の会社を参照できる
- ✅ ユーザーは他人の会社を参照できない
- ✅ ユーザーは自分の会社を更新できる
- ✅ ユーザーは他人の会社を更新できない
- ✅ ユーザーは自分の会社を作成できる
- ✅ 未認証ユーザーは会社を参照できない

### 2. company_documentsテーブル (5テスト)

- ✅ 同一会社のユーザーはドキュメントを参照できる
- ✅ 他社のユーザーはドキュメントを参照できない
- ✅ 同一会社のユーザーはドキュメントを作成できる
- ✅ 同一会社のユーザーはドキュメントを削除できる
- ✅ 他社のユーザーはドキュメントを削除できない

### 3. rfpsテーブル (6テスト)

- ✅ 認証済みユーザーはRFPを参照できる
- ✅ 未認証ユーザーはRFPを参照できない
- ✅ 一般ユーザーはRFPを作成できない
- ✅ 一般ユーザーはRFPを更新できない
- ✅ 一般ユーザーはRFPを削除できない
- ✅ Service RoleはRFPを管理できる（作成・更新・削除）

### 4. bookmarksテーブル (5テスト)

- ✅ ユーザーは自分のブックマークを参照できる
- ✅ ユーザーは他人のブックマークを参照できない
- ✅ ユーザーはブックマークを作成できる
- ✅ ユーザーは自分のブックマークを削除できる
- ✅ ユーザーは他人のブックマークを削除できない

### 5. match_snapshotsテーブル (5テスト)

- ✅ ユーザーは自分のマッチングスナップショットを参照できる
- ✅ ユーザーは他人のマッチングスナップショットを参照できない
- ✅ 一般ユーザーはマッチングスナップショットを作成できない
- ✅ 一般ユーザーはマッチングスナップショットを削除できない
- ✅ Service Roleはマッチングスナップショットを管理できる

### 6. company_skill_embeddingsテーブル (5テスト)

- ✅ ユーザーは自分の会社のスキル埋め込みを参照できる
- ✅ ユーザーは他の会社のスキル埋め込みを参照できない
- ✅ 一般ユーザーはスキル埋め込みを作成できない
- ✅ 一般ユーザーはスキル埋め込みを更新できない
- ✅ Service Roleはスキル埋め込みを管理できる

## トラブルシューティング

### テストが失敗する場合

1. **環境変数の確認**
   ```bash
   # .envファイルが存在することを確認
   ls -la apps/api/.env

   # 環境変数が正しく読み込まれているか確認
   cd apps/api && uv run python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))"
   ```

2. **データベーススキーマの確認**
   - Supabase DashboardでRLSポリシーが有効になっているか確認
   - `supabase/sql/init.sql`が最新の状態で適用されているか確認

3. **テストデータのクリーンアップ**
   ```bash
   # 既存のテストデータを削除（Service Roleで実行）
   # Supabase DashboardのSQL Editorで以下を実行
   DELETE FROM companies WHERE name LIKE 'テスト株式会社%';
   DELETE FROM auth.users WHERE email LIKE '%@gmail.com%';
   ```

### よくある問題

**問題**: `Email not confirmed`エラーが発生する

**解決策**: テストフィクスチャは自動的にService Roleでメール確認済みユーザーを作成します。もしエラーが発生する場合は、Supabaseプロジェクトの「Authentication」設定で「Confirm email」が無効になっていることを確認してください。

**問題**: `403 Forbidden`エラーが発生する

**解決策**: RLSポリシーが正しく設定されていることを確認してください。特に、以下を確認：
- テーブルでRLSが有効になっているか (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)
- 適切なポリシーが作成されているか (`CREATE POLICY ...`)

**問題**: テストが遅い

**解決策**:
- テストは実際のデータベースに接続するため、通常よりも時間がかかります
- 特定のテーブルやテストケースのみを実行して時間を短縮できます
- ネットワーク接続が安定していることを確認してください

## カバレッジレポート

テストカバレッジを確認：

```bash
cd apps/api
uv run pytest tests/test_rls_policies.py -v --cov=. --cov-report=html
open htmlcov/index.html
```

## 参考資料

- [Supabase Row Level Security Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [pytest Documentation](https://docs.pytest.org/)

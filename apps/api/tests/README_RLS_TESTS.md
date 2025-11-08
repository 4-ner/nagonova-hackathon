# RLS (Row Level Security) ポリシーテスト

このディレクトリには、SupabaseのRow Level Security (RLS) ポリシーが正しく機能していることを確認するためのテストが含まれています。

## 概要

RLSポリシーテストは、実際のSupabaseデータベースに接続して以下を検証します:

- **認証済みユーザー**が自分のデータにアクセスできる
- **認証済みユーザー**が他人のデータにアクセスできない
- **未認証ユーザー**がデータにアクセスできない
- **Service Role**がすべてのデータにアクセスできる

## テスト対象テーブル

### 1. companies
- ✅ ユーザーは自分の会社を参照できる
- ✅ ユーザーは他人の会社を参照できない
- ✅ ユーザーは自分の会社を更新できる
- ✅ ユーザーは他人の会社を更新できない
- ✅ ユーザーは会社を作成できる

### 2. company_documents
- ✅ 同一会社のユーザーはドキュメントを参照できる
- ✅ 他社のユーザーはドキュメントを参照できない
- ✅ 同一会社のユーザーはドキュメントを作成できる
- ✅ 同一会社のユーザーはドキュメントを削除できる
- ✅ 他社のユーザーはドキュメントを削除できない

### 3. rfps
- ✅ 認証済みユーザーはRFPを参照できる
- ✅ 未認証ユーザーはRFPを参照できない
- ✅ 一般ユーザーはRFPを作成できない
- ✅ 一般ユーザーはRFPを更新できない
- ✅ 一般ユーザーはRFPを削除できない
- ✅ Service RoleはRFPを管理できる

### 4. bookmarks
- ✅ ユーザーは自分のブックマークを参照できる
- ✅ ユーザーは他人のブックマークを参照できない
- ✅ ユーザーはブックマークを作成できる
- ✅ ユーザーは自分のブックマークを削除できる
- ✅ ユーザーは他人のブックマークを削除できない

### 5. match_snapshots
- ✅ ユーザーは自分のマッチングスナップショットを参照できる
- ✅ ユーザーは他人のマッチングスナップショットを参照できない
- ✅ 一般ユーザーはマッチングスナップショットを作成できない
- ✅ 一般ユーザーはマッチングスナップショットを削除できない
- ✅ Service Roleはマッチングスナップショットを管理できる

### 6. company_skill_embeddings
- ✅ ユーザーは自分の会社のスキル埋め込みを参照できる
- ✅ ユーザーは他の会社のスキル埋め込みを参照できない
- ✅ 一般ユーザーはスキル埋め込みを作成できない
- ✅ 一般ユーザーはスキル埋め込みを更新できない
- ✅ Service Roleはスキル埋め込みを管理できる

## 環境変数の設定

RLSテストを実行するには、以下の環境変数が必要です:

```bash
# .envファイルに設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

## テストの実行方法

### すべてのRLSテストを実行

```bash
cd apps/api
pytest tests/test_rls_policies.py -v -m rls
```

### 特定のテーブルのRLSテストのみ実行

```bash
# companiesテーブルのみ
pytest tests/test_rls_policies.py::TestCompaniesRLS -v

# rfpsテーブルのみ
pytest tests/test_rls_policies.py::TestRfpsRLS -v

# bookmarksテーブルのみ
pytest tests/test_rls_policies.py::TestBookmarksRLS -v
```

### 特定のテストケースのみ実行

```bash
# ユーザーが自分の会社を参照できるテスト
pytest tests/test_rls_policies.py::TestCompaniesRLS::test_user_can_read_own_company -v

# 一般ユーザーがRFPを作成できないテスト
pytest tests/test_rls_policies.py::TestRfpsRLS::test_user_cannot_create_rfp -v
```

### RLSテスト以外のテストを実行

```bash
# RLSマーカーがついていないテストのみ実行
pytest -v -m "not rls"
```

### カバレッジなしで実行（高速実行）

```bash
pytest tests/test_rls_policies.py -v -m rls --no-cov
```

## テストの仕組み

### 1. フィクスチャ構成

RLSテストは `tests/fixtures/rls_fixtures.py` で定義されたフィクスチャを使用します:

- **supabase_anon_client**: 匿名クライアント（RLS適用）
- **supabase_service_client**: Service Roleクライアント（RLS無視）
- **test_user_1, test_user_2**: テスト用ユーザー（自動作成・削除）
- **authenticated_client_1, authenticated_client_2**: 認証済みクライアント
- **company_user_1, company_user_2**: テスト用会社データ
- **rfp_data**: テスト用RFPデータ
- その他、各テーブルのテストデータフィクスチャ

### 2. テストユーザーの管理

テストユーザーは各テスト実行時に自動的に作成され、テスト終了後に自動的に削除されます:

```python
@pytest.fixture(scope="function")
def test_user_1(supabase_anon_client, supabase_service_client):
    # ユーザー作成
    user = create_test_user(...)
    yield user
    # 自動クリーンアップ（ユーザーと関連データを削除）
    cleanup_user(user)
```

### 3. テストデータのクリーンアップ

- テストユーザーに紐づくデータは、ユーザー削除時にCASCADE削除される
- Service Roleで作成したデータ（RFP、マッチングスナップショットなど）は明示的に削除

## トラブルシューティング

### テストが失敗する場合

#### 環境変数が設定されていない

```
SKIPPED [1] tests/fixtures/rls_fixtures.py:XX: SUPABASE_URL環境変数が設定されていません
```

**解決策**: `.env`ファイルに必要な環境変数を設定してください。

#### 認証エラー

```
AuthApiError: Invalid API key
```

**解決策**: `SUPABASE_ANON_KEY`と`SUPABASE_SERVICE_KEY`が正しいか確認してください。

#### RLSポリシーが設定されていない

```
AssertionError: assert len(response.data) == 0
```

**解決策**:
1. `supabase/sql/init.sql`が実行されているか確認
2. Supabase DashboardでRLSポリシーが有効化されているか確認

#### テストユーザーが削除されない

テストが途中で失敗した場合、テストユーザーが残る可能性があります。

**解決策**: Supabase Dashboardの認証画面から手動で削除するか、以下のSQLを実行:

```sql
-- テストユーザーを削除（Service Roleで実行）
DELETE FROM auth.users WHERE email LIKE 'test-user-%@example.com';
```

### テスト実行が遅い

RLSテストは実際のデータベースに接続するため、モックベースのテストより実行時間が長くなります。

**高速化のヒント**:
- カバレッジ計測を無効化: `--no-cov`
- 並列実行: `pytest-xdist`を使用（ただしデータベース競合に注意）
- 特定のテストクラスのみ実行

## CI/CDでの実行

GitHub ActionsなどのCI/CD環境で実行する場合:

1. Supabaseプロジェクトのシークレットを環境変数に設定
2. テスト用のSupabaseプロジェクトを別途用意（本番環境と分離）
3. RLSテストを別ジョブとして分離

```yaml
# .github/workflows/test.yml
jobs:
  rls-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: RLSテスト実行
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_TEST_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_TEST_ANON_KEY }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_TEST_SERVICE_KEY }}
        run: |
          cd apps/api
          pytest tests/test_rls_policies.py -v -m rls
```

## ベストプラクティス

1. **テスト環境を本番環境と分離する**: 本番データベースでRLSテストを実行しない
2. **テストユーザーは自動削除される**: 手動クリーンアップは不要
3. **失敗時のデバッグ**: `-vv`オプションで詳細ログを表示
4. **定期実行**: RLSポリシーの変更後は必ずテストを実行

## 参考リンク

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [pytest Documentation](https://docs.pytest.org/)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)

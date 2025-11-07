# Services

外部API連携やビジネスロジックを提供するサービスレイヤーです。

## KKJ API クライアント

官公需情報ポータルサイトからRFP（Request for Proposal）データを取得するAPIクライアントです。

### 基本的な使い方

```python
from services.kkj_api import KKJAPIClient

# クライアントを初期化
client = KKJAPIClient()

# 東京都のRFPを取得
rfps = client.fetch_rfps(
    prefecture_code="13",  # 都道府県コード（JIS X0401準拠）
    count=100,             # 取得件数（最大1000）
    query="情報システム",   # 検索キーワード
)

# 結果を表示
for rfp in rfps:
    print(f"件名: {rfp['project_name']}")
    print(f"機関名: {rfp['organization_name']}")
    print(f"公告日: {rfp['cft_issue_date']}")
    print(f"URL: {rfp['external_document_uri']}")
```

### NGキーワードフィルタリング

特定のキーワードを含むRFPを除外できます。

```python
# 「保守」「運用」を含むRFPを除外
rfps = client.fetch_rfps(
    prefecture_code="13",
    count=100,
    query="システム",
    ng_keywords=["保守", "運用", "メンテナンス"],
)
```

### 都道府県コード

JIS X0401に準拠した都道府県コード（01-47）を使用します。

- `01`: 北海道
- `13`: 東京都
- `27`: 大阪府
- `40`: 福岡県
- など

詳細は`kkj_api.py`の`PREFECTURE_NAMES`定数を参照してください。

### レスポンス形式

各RFPは以下のフィールドを持つdictで返されます。

```python
{
    "project_name": "件名",
    "organization_name": "機関名",
    "cft_issue_date": "2024-01-01T00:00:00+09:00",  # ISO8601形式
    "external_document_uri": "https://...",
    "prefecture_name": "東京都",
    "lg_code": "13",
    "category": "物品",  # または "工事", "役務"
    "procedure_type": "一般競争入札",
    "attachments": [
        {"name": "仕様書", "uri": "https://..."}
    ],
    # その他のフィールド...
}
```

### エラーハンドリング

```python
import httpx

try:
    rfps = client.fetch_rfps(
        prefecture_code="13",
        count=100,
    )
except ValueError as e:
    # 無効なパラメータやXMLパースエラー
    print(f"パラメータエラー: {e}")
except httpx.HTTPError as e:
    # HTTP通信エラー（最大3回自動リトライ後）
    print(f"通信エラー: {e}")
```

### 機能

- ✅ 都道府県コード指定でのRFP取得
- ✅ 検索キーワード指定
- ✅ 取得件数制御（最大1000件）
- ✅ NGキーワードフィルタリング
- ✅ 自動リトライ（最大3回、指数バックオフ）
- ✅ レート制限遵守（1秒間隔）
- ✅ タイムアウト設定（30秒）
- ✅ 型ヒント完備
- ✅ ログ出力

### 制限事項

- APIのレート制限に配慮し、リクエスト間隔を1秒空けています
- 最大取得件数は1000件です（API仕様）
- タイムアウトは30秒に設定されています
- XMLパースに失敗した場合は`ValueError`が発生します

### 実装のポイント

1. **リトライロジック**: HTTP通信エラー時は最大3回まで自動リトライします（指数バックオフ）
2. **レート制限**: リクエスト後に1秒のスリープを入れてレート制限を遵守します
3. **NGキーワードフィルタ**: 件名と公告文の両方をチェックして除外します
4. **都道府県名自動補完**: 都道府県コードから都道府県名を自動的に補完します
5. **ログ出力**: `logging`モジュールを使用して詳細なログを出力します

### 参考資料

- [官公需情報ポータルサイト](http://www.kkj.go.jp/)
- [検索API仕様書](../../docs/api_guide.pdf)

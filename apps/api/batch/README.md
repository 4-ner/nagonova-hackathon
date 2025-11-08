# バッチスクリプト

RFP Radar APIのバッチ処理スクリプト集

## 概要

| スクリプト | 説明 | 対象テーブル |
|-----------|------|-------------|
| `fetch_rfps.py` | KKJ APIからRFP案件を取得 | `rfps` |
| `generate_embeddings.py` | RFPの埋め込みベクトル生成 | `rfps.embedding` |
| `generate_company_skill_embeddings.py` | 会社スキルの埋め込みベクトル生成 | `company_skill_embeddings.embedding` |
| `calculate_matching.py` | マッチングスコア計算・保存 | `match_snapshots` |

## 前提条件

### 環境変数設定

`.env`ファイルに以下を設定：

```env
# Supabase認証情報（必須）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OpenAI API設定（埋め込み生成バッチで必須）
OPENAI_API_KEY=your_openai_api_key_here
```

### Python環境

- Python 3.13+
- uvパッケージマネージャー

```bash
# 依存関係インストール
cd apps/api
uv pip sync
```

## 各スクリプトの使用方法

### 1. RFP案件取得 (`fetch_rfps.py`)

KKJ APIから公募情報を取得してSupabaseに保存します。

```bash
# 基本実行（全件取得）
PYTHONPATH=. uv run python batch/fetch_rfps.py

# 件数制限付き実行
PYTHONPATH=. uv run python batch/fetch_rfps.py --limit 100

# ヘルプ表示
PYTHONPATH=. uv run python batch/fetch_rfps.py --help
```

**オプション:**
- `--limit N`: 取得件数を上限N件に制限

### 2. RFP埋め込み生成 (`generate_embeddings.py`)

RFPのタイトル・説明文から埋め込みベクトルを生成します。

```bash
# 基本実行（全未処理RFP）
PYTHONPATH=. uv run python batch/generate_embeddings.py

# バッチサイズ指定
PYTHONPATH=. uv run python batch/generate_embeddings.py --batch-size 50

# 件数制限付き実行
PYTHONPATH=. uv run python batch/generate_embeddings.py --limit 100

# バッチサイズ + 件数制限
PYTHONPATH=. uv run python batch/generate_embeddings.py --batch-size 50 --limit 200
```

**オプション:**
- `--batch-size N`: バッチサイズ（デフォルト: 100）
- `--limit N`: 処理件数上限（デフォルト: なし）

**処理対象:**
- `rfps`テーブルの`embedding IS NULL`のレコード

### 3. 会社スキル埋め込み生成 (`generate_company_skill_embeddings.py`)

会社スキルテキストから埋め込みベクトルを生成します。

```bash
# 基本実行（全未処理スキル）
PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py

# バッチサイズ指定
PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py --batch-size 50

# 件数制限付き実行
PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py --limit 100

# バッチサイズ + 件数制限
PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py --batch-size 50 --limit 200
```

**オプション:**
- `--batch-size N`: バッチサイズ（デフォルト: 100）
- `--limit N`: 処理件数上限（デフォルト: なし）

**処理対象:**
- `company_skill_embeddings`テーブルの`embedding IS NULL`のレコード

### 4. マッチングスコア計算 (`calculate_matching.py`)

会社とRFPのマッチングスコアを計算してスナップショットを保存します。

```bash
# 基本実行（全会社）
PYTHONPATH=. uv run python batch/calculate_matching.py

# 特定会社のみ処理
PYTHONPATH=. uv run python batch/calculate_matching.py --company-id <company_uuid>

# バッチサイズ指定
PYTHONPATH=. uv run python batch/calculate_matching.py --batch-size 50
```

**オプション:**
- `--company-id UUID`: 特定会社のみ処理
- `--batch-size N`: バッチサイズ（デフォルト: 100）

## 実行順序（初期セットアップ時）

1. **RFP案件取得**
   ```bash
   PYTHONPATH=. uv run python batch/fetch_rfps.py
   ```

2. **RFP埋め込み生成**
   ```bash
   PYTHONPATH=. uv run python batch/generate_embeddings.py
   ```

3. **会社スキル埋め込み生成**
   ```bash
   PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py
   ```

4. **マッチングスコア計算**
   ```bash
   PYTHONPATH=. uv run python batch/calculate_matching.py
   ```

## エラーハンドリング

### リトライ処理

埋め込み生成スクリプトは以下のリトライ機能を持ちます：

- **OpenAI APIエラー**: 最大3回リトライ（指数バックオフ）
- **レート制限エラー**: 60秒待機後リトライ

### エラー時の動作

- 個別レコードの処理失敗時はスキップして継続
- 処理結果は統計情報として出力（成功数/失敗数/成功率）

### ログレベル

デフォルトは`INFO`レベル。詳細ログが必要な場合はスクリプト内の`logging.basicConfig`の`level`を`DEBUG`に変更してください。

## トラブルシューティング

### ModuleNotFoundError

```bash
# PYTHONPATHを設定して実行
PYTHONPATH=. uv run python batch/<script_name>.py
```

### Supabase接続エラー

```bash
# 環境変数確認
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# .envファイル確認
cat .env
```

### OpenAI APIエラー

```bash
# APIキー確認
echo $OPENAI_API_KEY

# レート制限の場合は--batch-sizeを減らす
PYTHONPATH=. uv run python batch/generate_embeddings.py --batch-size 10
```

## 定期実行（cron設定例）

```cron
# 毎日午前2時にRFP案件取得
0 2 * * * cd /path/to/apps/api && PYTHONPATH=. uv run python batch/fetch_rfps.py

# 毎日午前3時に埋め込み生成
0 3 * * * cd /path/to/apps/api && PYTHONPATH=. uv run python batch/generate_embeddings.py
0 3 * * * cd /path/to/apps/api && PYTHONPATH=. uv run python batch/generate_company_skill_embeddings.py

# 毎日午前4時にマッチング計算
0 4 * * * cd /path/to/apps/api && PYTHONPATH=. uv run python batch/calculate_matching.py
```

## 注意事項

- **Service Role Key使用**: 全バッチスクリプトはService Role KeyでRLSをバイパスします
- **OpenAI API費用**: 埋め込み生成はOpenAI APIを使用するため、処理件数に応じて費用が発生します
- **処理時間**: 大量データ処理時はレート制限により時間がかかる場合があります（`--batch-size`で調整）

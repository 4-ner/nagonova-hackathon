# RFP Radar 実装計画（フェーズ3→フェーズ4→フェーズ2）

## 概要

Notionタスクの以下のフェーズを順次実装します：
1. **フェーズ3**: RFPデータ取得（KKJ API連携）
2. **フェーズ4**: スコアリング・マッチング機能
3. **フェーズ2**: 会社ドキュメント管理機能

---

## フェーズ3: RFPデータ取得・埋め込み生成

**Notionタスク**: `2a4e9670-1260-81a3-88f3-f33966ee79dd`
**URL**: https://www.notion.so/3-RFP-KKJ-API-2a4e9670126081a388f3f33966ee79dd
**優先度**: 高 | **工数**: 大

**📚 API仕様書**: `docs/api_guide.pdf` にKKJ API連携の仕様書を配置済み

### 目的
KKJ APIから公共調達情報（RFP）を取得し、OpenAI Embeddings APIで埋め込みベクトルを生成してデータベースに格納する。

### 実装内容

#### 1. 環境設定
- [ ] `.env`に以下の環境変数を追加
  - `OPENAI_API_KEY` - OpenAI API認証キー
  - `KKJ_API_URL` - KKJ APIエンドポイント
- [ ] `requirements.txt`に依存関係を追加
  - `openai>=1.0.0`
  - `httpx>=0.25.0`

#### 2. バックエンド実装

**新規作成ファイル**:
- `apps/api/services/__init__.py`
- `apps/api/services/kkj_api.py`
  - KKJ API連携サービス
  - 10県×各100件のRFPデータ取得
  - NGキーワード除外機能
  - レート制限対応（インターバル設定、リトライロジック）

- `apps/api/services/embedding.py`
  - OpenAI text-embedding-3-small APIによる埋め込み生成
  - バッチ処理対応
  - エラーハンドリング

- `apps/api/batch/__init__.py`
- `apps/api/batch/fetch_rfps.py`
  - RFP取得バッチスクリプト
  - コマンドライン引数対応（県指定、件数指定など）

- `apps/api/batch/generate_embeddings.py`
  - embedding生成バッチスクリプト
  - 未生成RFPのみを対象に処理

- `apps/api/routers/rfps.py`
  - `GET /rfps` - RFP一覧取得
  - `GET /rfps/{id}` - RFP詳細取得
  - `POST /admin/ingest/kkj` - 管理者用RFP取得トリガー

- `apps/api/schemas/rfp.py`
  - RFPレスポンススキーマ
  - RFPリクエストスキーマ

**修正ファイル**:
- `apps/api/main.py` - RFPルーター登録
- `apps/api/config.py` - OpenAI/KKJ API設定追加

#### 3. テスト項目
- [ ] KKJ APIからのRFP取得が成功するか
- [ ] NGキーワード除外が正しく動作するか
- [ ] OpenAI APIによるembedding生成が成功するか
- [ ] データベースへの格納が正しく行われるか
- [ ] バッチスクリプトが正常に実行できるか

---

## フェーズ4: スコアリング・マッチング機能

**Notionタスク**: `2a4e9670-1260-81c9-a5fb-e346cd223f38`
**URL**: https://www.notion.so/4-2a4e9670126081c9a5fbe346cd223f38
**優先度**: 高 | **工数**: 大

### 目的
会社プロフィールとRFPをハイブリッドマッチング（ベクトル検索+キーワード検索）でスコアリングし、最適な案件を提案する。

### 実装内容

#### 1. バックエンド実装

**新規作成ファイル**:
- `apps/api/services/matching_engine.py`
  - ベクトル検索（pgvector）実装
  - キーワード検索実装
  - スキル一致度計算（辞書ベース、エイリアス展開）
  - 必須要件判定（「必須」「必ず」等のキーワード検出）
  - 地域係数（1.0/0.8）、予算ブースト（+5~10%）、締切ブースト
  - 総合スコア計算ロジック

- `apps/api/batch/calculate_matching.py`
  - マッチングスコア計算バッチ
  - `match_snapshots`テーブルへの結果保存

- `apps/api/routers/matching.py`
  - `GET /me/matching` - 自社のマッチング結果取得

- `apps/api/schemas/matching.py`
  - マッチング結果スキーマ
  - スコア詳細スキーマ

- `apps/api/data/skill_aliases.json`
  - スキルエイリアス辞書（例: "JS" → "JavaScript"）

**修正ファイル**:
- `apps/api/main.py` - マッチングルーター登録
- `apps/api/routers/rfps.py` - マッチングスコア統合

#### 2. フロントエンド実装

**新規作成ファイル**:
- `apps/web/src/app/(dashboard)/rfps/page.tsx`
  - RFP一覧ページ
  - マッチングスコア順でソート表示
  - フィルタリング機能（地域、予算、締切）

- `apps/web/src/app/(dashboard)/rfps/[id]/page.tsx`
  - RFP詳細ページ
  - マッチングスコア詳細表示
  - ブックマーク機能

- `apps/web/src/hooks/useRfps.ts`
  - RFP取得hook（SWR使用）
  - フィルタリング、ページネーション対応

- `apps/web/src/components/rfp/RfpCard.tsx`
  - RFPカードコンポーネント
  - スコアバッジ、締切表示、ブックマークボタン

- `apps/web/src/components/rfp/MatchScore.tsx`
  - マッチングスコア表示コンポーネント
  - プログレスバー、スコア詳細ツールチップ

- `apps/web/src/types/rfp.ts`
  - RFP型定義

- `apps/web/src/types/matching.ts`
  - マッチング結果型定義

#### 3. テスト項目
- [ ] ベクトル検索が正しく動作するか
- [ ] スキル一致度計算が正確か
- [ ] 必須要件判定が機能するか
- [ ] 各種係数が正しく適用されるか
- [ ] スコア順ソートが正しいか
- [ ] RFP一覧ページが表示されるか
- [ ] RFP詳細ページが表示されるか
- [ ] フィルタリング機能が動作するか

---

## フェーズ2: 会社ドキュメント管理機能

**Notionタスク**: `2a4e9670-1260-81f6-8bf8-e289b9c4fffd`
**URL**: https://www.notion.so/2-2a4e9670126081f68bf8e289b9c4fffd
**優先度**: 中 | **工数**: 中

### 目的
会社の技術資料、実績資料などをアップロード・管理し、提案書生成時に活用できるようにする。

### 実装内容

#### 1. Supabase Storage設定
- [ ] Supabase Dashboardで`company-documents`バケット作成
- [ ] RLSポリシー設定（自社ドキュメントのみアクセス可能）

#### 2. バックエンド実装

**新規作成ファイル**:
- `apps/api/services/storage.py`
  - Supabase Storage連携サービス
  - ファイルアップロード処理
  - 署名付きURL生成（有効期限1時間）
  - ファイル削除処理

- `apps/api/routers/documents.py`
  - `GET /me/company/documents` - ドキュメント一覧取得
  - `POST /me/company/documents` - ドキュメントアップロード
  - `PUT /me/company/documents/{id}` - ドキュメント更新
  - `DELETE /me/company/documents/{id}` - ドキュメント削除

- `apps/api/schemas/document.py`
  - ドキュメントレスポンススキーマ
  - ドキュメントアップロードスキーマ

**修正ファイル**:
- `apps/api/main.py` - ドキュメントルーター登録

#### 3. フロントエンド実装

**新規作成ファイル**:
- `apps/web/src/app/(dashboard)/documents/page.tsx`
  - ドキュメント管理ページ
  - アップロード、一覧表示、削除機能

- `apps/web/src/hooks/useDocuments.ts`
  - ドキュメント管理hook（SWR使用）
  - アップロード、削除のmutation対応

- `apps/web/src/components/documents/DocumentUploader.tsx`
  - ファイルアップロードコンポーネント
  - ドラッグ&ドロップ対応
  - ファイルサイズ・形式バリデーション（20MB以下、対応形式チェック）

- `apps/web/src/components/documents/DocumentList.tsx`
  - ドキュメント一覧表示コンポーネント
  - プレビュー、ダウンロード、削除機能

- `apps/web/src/types/document.ts`
  - ドキュメント型定義

#### 4. テスト項目
- [ ] ファイルアップロードが成功するか
- [ ] 署名付きURLが生成されるか
- [ ] ファイルサイズ・形式バリデーションが動作するか
- [ ] ドキュメント一覧が表示されるか
- [ ] ドキュメント削除が成功するか
- [ ] RLSポリシーが正しく機能するか

---

## タスク着手時のワークフロー（GitHub Flow）

各フェーズ開始時に以下の手順を実施：

1. **Notionタスク更新**
   - ステータスを「進行中」に変更
   - 開始日時を設定（時間まで記載）

2. **Gitブランチ作成**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<タスクID>
   ```

3. **空コミット作成**
   ```bash
   git commit --allow-empty -m "chore: start feature/<タスクID>"
   git push -u origin feature/<タスクID>
   ```

4. **Draft PR作成**
   ```bash
   gh pr create --assignee @me --base main --draft \
     --title "【<タスクID>】<タイトル>" \
     --body "<タスクの説明> Notion: <NotionタスクURL>"
   ```

5. **実装計画をユーザーに提示**

---

## タスク完了時のワークフロー（GitHub Flow）

各フェーズ完了時に以下の手順を実施：

1. **PR ready化・マージ**
   ```bash
   gh pr ready
   gh pr merge --merge --auto --delete-branch
   ```

2. **Notionタスク更新**
   - 完了日時を設定（時間まで記載）
   - 「振り返り」セクションを追加
     - コマンドライン履歴を参照
     - 実装のポイント、学び、課題を記載
   - ステータスを「完了」に変更

3. **ユーザーにプロンプトを返す**

---

## 技術的な注意事項

### 1. KKJ API
- **API仕様書**: `docs/api_guide.pdf` を参照
- エンドポイント、認証方式、レート制限の詳細を確認
- XML/JSONレスポンス形式の確認

### 2. OpenAI API
- text-embedding-3-small使用（1536次元）
- レート制限、コスト管理に注意
- エラーハンドリング（リトライロジック）実装

### 3. データベース
- pgvector拡張有効化済み
- IVFFlat インデックス設定済み（100リスト）
- 大規模データ時はインデックスチューニングが必要

### 4. Supabase Storage
- バケット作成とRLSポリシー設定が必要
- ファイルサイズ上限: 20MB/件
- 対応形式: URL/PDF/Word/PPT/画像/テキスト

### 5. wshobson/agentsプラグイン活用
- `backend-architect` - API設計時
- `fastapi-pro` - FastAPI実装時
- `frontend-developer` - React/Next.js実装時
- `database-optimizer` - クエリ最適化時

---

## 実装スケジュール（目安）

- **フェーズ3**: 2-3日（KKJ API仕様書は `docs/api_guide.pdf` を参照）
- **フェーズ4**: 3-4日（フロントエンド実装含む）
- **フェーズ2**: 1-2日（Storage設定含む）

**合計**: 約6-9日

---

## 現在のプロジェクト状況

### 完了済み
- ✅ フェーズ0: 環境構築・基盤整備
- ✅ フェーズ1: 認証・会社プロフィール管理機能
- ✅ データベーススキーマ（pgvector対応、全テーブル定義済み）
- ✅ バックエンド基本構成（FastAPI、Supabase連携、認証ミドルウェア）
- ✅ フロントエンド基本構成（Next.js 16、shadcn/ui、認証機能）

### 未実装
- ❌ RFP取得・埋め込み生成機能（フェーズ3）
- ❌ スコアリング・マッチング機能（フェーズ4）
- ❌ ドキュメント管理機能（フェーズ2）
- ❌ ブックマーク機能（フェーズ5）
- ❌ 提案ドラフト生成機能（フェーズ6）

---

**最終更新**: 2025-11-08

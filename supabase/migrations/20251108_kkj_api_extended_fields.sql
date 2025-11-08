-- ============================================================================
-- KKJ API対応: rfpsテーブル拡張マイグレーション
-- ============================================================================
-- このマイグレーションは、KKJ API（官公需ポータル）からの充実したデータを
-- サポートするために、rfpsテーブルに9個の新規カラムとそれに対応する
-- 11個のインデックスを追加します。
--
-- 新規カラム:
--   - category: カテゴリ
--   - procedure_type: 入札方式
--   - cft_issue_date: 公告日
--   - tender_deadline: 入札書提出期限
--   - opening_event_date: 開札日時
--   - item_code: 品目分類コード
--   - lg_code: 都道府県コード（2桁）
--   - city_code: 市区町村コード
--   - certification: 資格要件
--
-- インデックス戦略:
--   - 部分インデックス: NOT NULL条件付きで検索頻度が高いカラムを最適化
--   - 複合インデックス: よく一緒に検索されるカラムの組み合わせ
--   - 全文検索: 資格要件のテキスト検索最適化
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. 新規カラム追加
-- ============================================================================

-- category カラムの追加
ALTER TABLE rfps
ADD COLUMN category TEXT;

COMMENT ON COLUMN rfps.category IS 'KKJ API: 案件のカテゴリ分類';

-- procedure_type カラムの追加
ALTER TABLE rfps
ADD COLUMN procedure_type TEXT;

COMMENT ON COLUMN rfps.procedure_type IS 'KKJ API: 入札方式（一般競争入札、プロポーザル形式など）';

-- cft_issue_date カラムの追加
ALTER TABLE rfps
ADD COLUMN cft_issue_date TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN rfps.cft_issue_date IS 'KKJ API: 公告日（案件の公開日時）';

-- tender_deadline カラムの追加
ALTER TABLE rfps
ADD COLUMN tender_deadline TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN rfps.tender_deadline IS 'KKJ API: 入札書提出期限（応募締切日時）';

-- opening_event_date カラムの追加
ALTER TABLE rfps
ADD COLUMN opening_event_date TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN rfps.opening_event_date IS 'KKJ API: 開札日時（入札結果公開日時）';

-- item_code カラムの追加
ALTER TABLE rfps
ADD COLUMN item_code TEXT;

COMMENT ON COLUMN rfps.item_code IS 'KKJ API: 品目分類コード（統一資格審査の品目分類）';

-- lg_code カラムの追加
ALTER TABLE rfps
ADD COLUMN lg_code TEXT;

COMMENT ON COLUMN rfps.lg_code IS 'KKJ API: 都道府県コード（2桁、JIS X 0401に準拠）';

-- city_code カラムの追加
ALTER TABLE rfps
ADD COLUMN city_code TEXT;

COMMENT ON COLUMN rfps.city_code IS 'KKJ API: 市区町村コード（JIS X 0402に準拠）';

-- certification カラムの追加
ALTER TABLE rfps
ADD COLUMN certification TEXT;

COMMENT ON COLUMN rfps.certification IS 'KKJ API: 資格要件（応募に必要な認定・資格情報）';

-- ============================================================================
-- 2. インデックス作成
-- ============================================================================

-- idx_rfps_category: カテゴリ別検索用（部分インデックス）
CREATE INDEX idx_rfps_category
ON rfps(category)
WHERE category IS NOT NULL;

-- idx_rfps_procedure_type: 入札方式別検索用（部分インデックス）
CREATE INDEX idx_rfps_procedure_type
ON rfps(procedure_type)
WHERE procedure_type IS NOT NULL;

-- idx_rfps_cft_issue_date: 公告日ソート用（DESC、部分インデックス）
CREATE INDEX idx_rfps_cft_issue_date
ON rfps(cft_issue_date DESC)
WHERE cft_issue_date IS NOT NULL;

-- idx_rfps_tender_deadline: 入札締切検索用（部分インデックス）
CREATE INDEX idx_rfps_tender_deadline
ON rfps(tender_deadline)
WHERE tender_deadline IS NOT NULL;

-- idx_rfps_opening_event_date: 開札日検索用（部分インデックス）
CREATE INDEX idx_rfps_opening_event_date
ON rfps(opening_event_date)
WHERE opening_event_date IS NOT NULL;

-- idx_rfps_item_code: 品目分類検索用（部分インデックス）
CREATE INDEX idx_rfps_item_code
ON rfps(item_code)
WHERE item_code IS NOT NULL;

-- idx_rfps_lg_code: 都道府県コード検索用（部分インデックス）
CREATE INDEX idx_rfps_lg_code
ON rfps(lg_code)
WHERE lg_code IS NOT NULL;

-- idx_rfps_city_code: 市区町村コード検索用（部分インデックス）
CREATE INDEX idx_rfps_city_code
ON rfps(city_code)
WHERE city_code IS NOT NULL;

-- idx_rfps_lg_city_code: 都道府県+市区町村複合インデックス
CREATE INDEX idx_rfps_lg_city_code
ON rfps(lg_code, city_code)
WHERE lg_code IS NOT NULL AND city_code IS NOT NULL;

-- idx_rfps_category_tender_deadline: カテゴリ+締切日複合インデックス
-- 一般的なクエリパターン: SELECT * FROM rfps WHERE category = ? AND tender_deadline > ?
CREATE INDEX idx_rfps_category_tender_deadline
ON rfps(category, tender_deadline)
WHERE category IS NOT NULL AND tender_deadline IS NOT NULL;

-- idx_rfps_certification_fulltext: 資格要件全文検索用GINインデックス
-- Japanese言語対応のtsvector全文検索インデックス
CREATE INDEX idx_rfps_certification_fulltext
ON rfps
USING GIN(to_tsvector('japanese', certification))
WHERE certification IS NOT NULL;

-- ============================================================================
-- 3. スキーマバージョン更新
-- ============================================================================

-- schema_versionテーブルにマイグレーション情報を記録
INSERT INTO schema_version (version, description)
VALUES (2, 'KKJ API extended fields: category, procedure_type, cft_issue_date, tender_deadline, opening_event_date, item_code, lg_code, city_code, certification with 11 optimized indexes')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- マイグレーション完了メッセージ
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'KKJ API extension migration completed successfully';
    RAISE NOTICE 'Added 9 columns to rfps table';
    RAISE NOTICE 'Created 11 optimized indexes for KKJ API integration';
    RAISE NOTICE 'New columns support full KKJ API data model';
    RAISE NOTICE 'Partial indexes reduce storage overhead while improving query performance';
END $$;

COMMIT;

-- ============================================================================
-- KKJ API対応: rfpsテーブル拡張マイグレーション ロールバック
-- ============================================================================
-- このスクリプトは、20251108_kkj_api_extended_fields.sqlで追加された
-- カラムとインデックスをロールバック（削除）します。
--
-- 削除対象:
--   - 9個の新規カラム
--   - 11個のインデックス
--   - schema_versionのマイグレーション記録
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. インデックス削除
-- ============================================================================

-- 全文検索インデックス削除
DROP INDEX IF EXISTS idx_rfps_certification_fulltext;

-- 複合インデックス削除
DROP INDEX IF EXISTS idx_rfps_category_tender_deadline;
DROP INDEX IF EXISTS idx_rfps_lg_city_code;

-- 単一カラムインデックス削除
DROP INDEX IF EXISTS idx_rfps_city_code;
DROP INDEX IF EXISTS idx_rfps_lg_code;
DROP INDEX IF EXISTS idx_rfps_item_code;
DROP INDEX IF EXISTS idx_rfps_opening_event_date;
DROP INDEX IF EXISTS idx_rfps_tender_deadline;
DROP INDEX IF EXISTS idx_rfps_cft_issue_date;
DROP INDEX IF EXISTS idx_rfps_procedure_type;
DROP INDEX IF EXISTS idx_rfps_category;

-- ============================================================================
-- 2. カラム削除
-- ============================================================================

ALTER TABLE rfps
DROP COLUMN IF EXISTS certification;

ALTER TABLE rfps
DROP COLUMN IF EXISTS city_code;

ALTER TABLE rfps
DROP COLUMN IF EXISTS lg_code;

ALTER TABLE rfps
DROP COLUMN IF EXISTS item_code;

ALTER TABLE rfps
DROP COLUMN IF EXISTS opening_event_date;

ALTER TABLE rfps
DROP COLUMN IF EXISTS tender_deadline;

ALTER TABLE rfps
DROP COLUMN IF EXISTS cft_issue_date;

ALTER TABLE rfps
DROP COLUMN IF EXISTS procedure_type;

ALTER TABLE rfps
DROP COLUMN IF EXISTS category;

-- ============================================================================
-- 3. スキーマバージョン削除
-- ============================================================================

DELETE FROM schema_version WHERE version = 2;

-- ============================================================================
-- ロールバック完了メッセージ
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'KKJ API extension rollback completed successfully';
    RAISE NOTICE 'Deleted 9 columns from rfps table';
    RAISE NOTICE 'Dropped 11 indexes';
    RAISE NOTICE 'rfps table restored to pre-migration state';
END $$;

COMMIT;

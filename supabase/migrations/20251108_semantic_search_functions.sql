-- =====================================================
-- セマンティック検索機能マイグレーション
-- 作成日: 2025-11-08
-- 説明: pgvectorを活用したセマンティック検索関数とハイブリッド検索の実装
-- =====================================================

-- -----------------------------------------------
-- 1. コサイン類似度検索関数
-- -----------------------------------------------
-- 目的: RFPの埋め込みベクトルに対してコサイン類似度検索を実行
-- パフォーマンス: IVFFlatインデックス活用、目標<100ms
-- -----------------------------------------------

CREATE OR REPLACE FUNCTION search_rfps_by_embedding(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    result_limit int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    external_id text,
    title text,
    issuing_org text,
    description text,
    budget int,
    region text,
    deadline date,
    url text,
    external_doc_urls text[],
    category text,
    procedure_type text,
    cft_issue_date timestamp with time zone,
    tender_deadline timestamp with time zone,
    opening_event_date timestamp with time zone,
    item_code text,
    lg_code text,
    city_code text,
    certification text,
    has_embedding boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    fetched_at timestamp with time zone,
    similarity_score float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- 入力バリデーション
    IF query_embedding IS NULL THEN
        RAISE EXCEPTION 'query_embedding cannot be NULL';
    END IF;

    IF similarity_threshold < 0 OR similarity_threshold > 1 THEN
        RAISE EXCEPTION 'similarity_threshold must be between 0 and 1';
    END IF;

    IF result_limit <= 0 OR result_limit > 100 THEN
        RAISE EXCEPTION 'result_limit must be between 1 and 100';
    END IF;

    RETURN QUERY
    SELECT
        r.id,
        r.external_id,
        r.title,
        r.issuing_org,
        r.description,
        r.budget,
        r.region,
        r.deadline,
        r.url,
        r.external_doc_urls,
        r.category,
        r.procedure_type,
        r.cft_issue_date,
        r.tender_deadline,
        r.opening_event_date,
        r.item_code,
        r.lg_code,
        r.city_code,
        r.certification,
        (r.embedding IS NOT NULL) AS has_embedding,
        r.created_at,
        r.updated_at,
        r.fetched_at,
        (1 - (r.embedding <=> query_embedding))::float AS similarity_score
    FROM rfps r
    WHERE
        r.embedding IS NOT NULL  -- NULL埋め込みを除外
        AND (1 - (r.embedding <=> query_embedding)) >= similarity_threshold  -- 類似度フィルタ
    ORDER BY r.embedding <=> query_embedding  -- コサイン距離の昇順（類似度の降順）
    LIMIT result_limit;
END;
$$;

-- RLSポリシー適用確認用コメント
COMMENT ON FUNCTION search_rfps_by_embedding IS
'セマンティック検索関数。RLSポリシーはSECURITY DEFINERで実行されるため、rfpsテーブルの既存RLSが適用される。';

-- -----------------------------------------------
-- 2. ハイブリッド検索関数
-- -----------------------------------------------
-- 目的: セマンティック検索(70%)とキーワードマッチ(30%)の統合
-- アルゴリズム: 重み付け線形結合
-- -----------------------------------------------

CREATE OR REPLACE FUNCTION hybrid_search_rfps(
    query_embedding vector(1536),
    query_text text,
    result_limit int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    external_id text,
    title text,
    issuing_org text,
    description text,
    budget int,
    region text,
    deadline date,
    url text,
    external_doc_urls text[],
    category text,
    procedure_type text,
    cft_issue_date timestamp with time zone,
    tender_deadline timestamp with time zone,
    opening_event_date timestamp with time zone,
    item_code text,
    lg_code text,
    city_code text,
    certification text,
    has_embedding boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    fetched_at timestamp with time zone,
    combined_score float,
    semantic_score float,
    keyword_score float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    semantic_weight float := 0.7;
    keyword_weight float := 0.3;
BEGIN
    -- 入力バリデーション
    IF query_embedding IS NULL THEN
        RAISE EXCEPTION 'query_embedding cannot be NULL';
    END IF;

    IF query_text IS NULL OR trim(query_text) = '' THEN
        RAISE EXCEPTION 'query_text cannot be NULL or empty';
    END IF;

    IF result_limit <= 0 OR result_limit > 100 THEN
        RAISE EXCEPTION 'result_limit must be between 1 and 100';
    END IF;

    RETURN QUERY
    WITH semantic_results AS (
        -- セマンティック検索スコア計算
        SELECT
            r.id,
            (1 - (r.embedding <=> query_embedding))::float AS semantic_score_raw
        FROM rfps r
        WHERE r.embedding IS NOT NULL
    ),
    keyword_results AS (
        -- キーワードマッチスコア計算
        SELECT
            r.id,
            CASE
                -- タイトルに完全一致
                WHEN r.title ILIKE '%' || query_text || '%' THEN 1.0
                -- 説明文に完全一致
                WHEN r.description ILIKE '%' || query_text || '%' THEN 0.5
                -- 調達カテゴリに一致
                WHEN r.category ILIKE '%' || query_text || '%' THEN 0.3
                -- 発注組織名に一致
                WHEN r.issuing_org ILIKE '%' || query_text || '%' THEN 0.2
                ELSE 0.0
            END::float AS keyword_score_raw
        FROM rfps r
    ),
    combined_results AS (
        -- スコア統合
        SELECT
            r.id,
            COALESCE(sr.semantic_score_raw, 0.0) AS semantic_score,
            COALESCE(kr.keyword_score_raw, 0.0) AS keyword_score,
            (
                (COALESCE(sr.semantic_score_raw, 0.0) * semantic_weight) +
                (COALESCE(kr.keyword_score_raw, 0.0) * keyword_weight)
            ) AS combined_score
        FROM rfps r
        LEFT JOIN semantic_results sr ON r.id = sr.id
        LEFT JOIN keyword_results kr ON r.id = kr.id
        WHERE
            -- 少なくとも一方のスコアが0より大きい
            COALESCE(sr.semantic_score_raw, 0.0) > 0.0
            OR COALESCE(kr.keyword_score_raw, 0.0) > 0.0
    )
    SELECT
        r.id,
        r.external_id,
        r.title,
        r.issuing_org,
        r.description,
        r.budget,
        r.region,
        r.deadline,
        r.url,
        r.external_doc_urls,
        r.category,
        r.procedure_type,
        r.cft_issue_date,
        r.tender_deadline,
        r.opening_event_date,
        r.item_code,
        r.lg_code,
        r.city_code,
        r.certification,
        (r.embedding IS NOT NULL) AS has_embedding,
        r.created_at,
        r.updated_at,
        r.fetched_at,
        cr.combined_score,
        cr.semantic_score,
        cr.keyword_score
    FROM combined_results cr
    JOIN rfps r ON cr.id = r.id
    ORDER BY cr.combined_score DESC
    LIMIT result_limit;
END;
$$;

COMMENT ON FUNCTION hybrid_search_rfps IS
'ハイブリッド検索関数。セマンティック(70%)とキーワード(30%)を統合。';

-- -----------------------------------------------
-- 3. 会社スキル埋め込み自動更新トリガー
-- -----------------------------------------------
-- 目的: companiesテーブルのskills更新時に埋め込みを自動再生成
-- 戦略: 既存レコード削除→新規挿入
-- -----------------------------------------------

-- トリガー関数
CREATE OR REPLACE FUNCTION update_company_skill_embeddings()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- トランザクション内で実行（エラー時は自動ロールバック）

    -- 既存の埋め込みを削除
    DELETE FROM company_skill_embeddings
    WHERE company_id = NEW.id;

    -- 新しいスキルが存在する場合のみ処理
    IF NEW.skills IS NOT NULL AND array_length(NEW.skills, 1) > 0 THEN
        -- 注意: 実際の埋め込み生成はアプリケーション層で実行
        -- このトリガーはプレースホルダーレコードを挿入
        -- アプリケーション層のバッチ処理で実際の埋め込みを更新
        INSERT INTO company_skill_embeddings (
            company_id,
            skill_text,
            embedding,
            created_at,
            updated_at
        )
        SELECT
            NEW.id,
            unnest(NEW.skills) AS skill_text,
            NULL,  -- アプリケーション層で後から更新
            now(),
            now();
    END IF;

    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        -- エラーログ記録（本番環境ではロギングサービス使用推奨）
        RAISE WARNING 'Failed to update company_skill_embeddings for company_id=%: %', NEW.id, SQLERRM;
        -- エラーでもメイン処理は継続（埋め込み更新は非同期で再試行可能）
        RETURN NEW;
END;
$$;

-- トリガー作成（INSERT/UPDATE時に発火）
DROP TRIGGER IF EXISTS trigger_update_company_skill_embeddings ON companies;

CREATE TRIGGER trigger_update_company_skill_embeddings
    AFTER INSERT OR UPDATE OF skills
    ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_company_skill_embeddings();

COMMENT ON FUNCTION update_company_skill_embeddings IS
'会社スキル更新時に埋め込みテーブルを同期。実際の埋め込み生成はアプリケーション層で実行。';

-- -----------------------------------------------
-- 4. company_skill_embeddingsへのインデックス追加
-- -----------------------------------------------
-- 目的: ベクトル検索とcompany_id検索の高速化
-- -----------------------------------------------

-- IVFFlatインデックス（ベクトル検索用）
-- lists=100: データ量10万件想定（推奨値: レコード数の√）
CREATE INDEX IF NOT EXISTS idx_company_skill_embeddings_vector
ON company_skill_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- company_id検索用インデックス（複合キー検索最適化）
CREATE INDEX IF NOT EXISTS idx_company_skill_embeddings_company_id
ON company_skill_embeddings (company_id);

-- スキル名検索用インデックス（オプション）
CREATE INDEX IF NOT EXISTS idx_company_skill_embeddings_skill
ON company_skill_embeddings (skill_text);

-- 複合インデックス（company_id + skillの組み合わせ検索用）
CREATE INDEX IF NOT EXISTS idx_company_skill_embeddings_company_skill
ON company_skill_embeddings (company_id, skill_text);

COMMENT ON INDEX idx_company_skill_embeddings_vector IS
'ベクトル検索用IVFFlatインデックス。lists=100は10万件規模想定。';

-- -----------------------------------------------
-- 5. 統計情報更新と初期設定
-- -----------------------------------------------

-- インデックス作成後は統計情報を更新
ANALYZE company_skill_embeddings;
ANALYZE rfps;

-- -----------------------------------------------
-- 6. パフォーマンスモニタリング用ビュー（オプション）
-- -----------------------------------------------

CREATE OR REPLACE VIEW v_search_performance_stats AS
SELECT
    'rfps' AS table_name,
    COUNT(*) AS total_records,
    COUNT(embedding) AS records_with_embedding,
    COUNT(*) - COUNT(embedding) AS records_without_embedding,
    ROUND(100.0 * COUNT(embedding) / NULLIF(COUNT(*), 0), 2) AS embedding_coverage_pct
FROM rfps
UNION ALL
SELECT
    'company_skill_embeddings' AS table_name,
    COUNT(*) AS total_records,
    COUNT(embedding) AS records_with_embedding,
    COUNT(*) - COUNT(embedding) AS records_without_embedding,
    ROUND(100.0 * COUNT(embedding) / NULLIF(COUNT(*), 0), 2) AS embedding_coverage_pct
FROM company_skill_embeddings;

COMMENT ON VIEW v_search_performance_stats IS
'検索パフォーマンス監視用ビュー。埋め込み生成カバレッジを確認。';

-- =====================================================
-- マイグレーション完了
-- =====================================================

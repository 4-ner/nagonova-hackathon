-- ============================================================================
-- RFP Radar Database Schema (with pgvector support)
-- ============================================================================
-- このスキーマは、会社情報とスキルに基づいて官公需の入札案件をマッチングする
-- RFP Radarシステムのデータベース構造を定義します。
--
-- 要件:
-- - PostgreSQL 14+
-- - Supabase (auth.users テーブルが存在)
-- - pgvector拡張（セマンティック検索用）
-- - Row Level Security (RLS) による細かいアクセス制御
--
-- ベクトル検索:
-- - OpenAI text-embedding-3-small (1536次元) を使用
-- - RFP案件と会社スキルの埋め込みベクトルでハイブリッドマッチング
-- - IVFFlat インデックスによる高速近似検索
-- ============================================================================

-- ============================================================================
-- 拡張機能の有効化
-- ============================================================================

-- UUID生成機能を有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pgvector拡張を有効化（ベクトル類似検索用）
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 1. companies (会社プロフィール)
-- ============================================================================

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    regions TEXT[] DEFAULT '{}',
    budget_min INTEGER,
    budget_max INTEGER,
    skills TEXT[] DEFAULT '{}',
    ng_keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 1ユーザーにつき1会社のみ
    CONSTRAINT unique_user_company UNIQUE (user_id),

    -- 予算範囲のバリデーション
    CONSTRAINT valid_budget_range CHECK (
        (budget_min IS NULL AND budget_max IS NULL) OR
        (budget_min IS NOT NULL AND budget_max IS NOT NULL AND budget_min <= budget_max)
    )
);

-- インデックス
CREATE INDEX idx_companies_user_id ON companies(user_id);

-- RLS有効化
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - ユーザーは自分の会社のみ参照可能
CREATE POLICY "Users can view their own company"
    ON companies
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLSポリシー: INSERT - ユーザーは自分の会社のみ作成可能
CREATE POLICY "Users can create their own company"
    ON companies
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLSポリシー: UPDATE - ユーザーは自分の会社のみ更新可能
CREATE POLICY "Users can update their own company"
    ON companies
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- コメント
COMMENT ON TABLE companies IS '会社プロフィール情報を管理するテーブル';
COMMENT ON COLUMN companies.user_id IS 'Supabase認証ユーザーID';
COMMENT ON COLUMN companies.regions IS '対応可能な都道府県コード配列';
COMMENT ON COLUMN companies.budget_min IS '希望案件規模の最小値（円）';
COMMENT ON COLUMN companies.budget_max IS '希望案件規模の最大値（円）';
COMMENT ON COLUMN companies.skills IS '保有スキル配列';
COMMENT ON COLUMN companies.ng_keywords IS 'マッチングから除外するキーワード配列';

-- ============================================================================
-- 2. company_documents (会社ドキュメント)
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('url', 'pdf', 'word', 'ppt', 'image', 'text')),
    storage_path TEXT,
    url TEXT,
    size_bytes INTEGER,
    tags TEXT[] DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- URL種別の場合はurlが必須、それ以外はstorage_pathが必須
    CONSTRAINT valid_document_source CHECK (
        (kind = 'url' AND url IS NOT NULL AND storage_path IS NULL) OR
        (kind != 'url' AND storage_path IS NOT NULL AND url IS NULL)
    )
);

-- インデックス
CREATE INDEX idx_company_documents_company_id ON company_documents(company_id);
CREATE INDEX idx_company_documents_tags ON company_documents USING GIN(tags);
CREATE INDEX idx_company_documents_kind ON company_documents(kind);

-- RLS有効化
ALTER TABLE company_documents ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - 同一会社のユーザーのみ参照可能
CREATE POLICY "Users can view their company documents"
    ON company_documents
    FOR SELECT
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    );

-- RLSポリシー: INSERT - 同一会社のユーザーのみ作成可能
CREATE POLICY "Users can create their company documents"
    ON company_documents
    FOR INSERT
    WITH CHECK (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    );

-- RLSポリシー: UPDATE - 同一会社のユーザーのみ更新可能
CREATE POLICY "Users can update their company documents"
    ON company_documents
    FOR UPDATE
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    );

-- RLSポリシー: DELETE - 同一会社のユーザーのみ削除可能
CREATE POLICY "Users can delete their company documents"
    ON company_documents
    FOR DELETE
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    );

-- コメント
COMMENT ON TABLE company_documents IS '会社が保有する各種ドキュメント（実績、製品情報など）を管理するテーブル';
COMMENT ON COLUMN company_documents.kind IS 'ドキュメント種別: url, pdf, word, ppt, image, text';
COMMENT ON COLUMN company_documents.storage_path IS 'Supabase Storage内のファイルパス（URL以外）';
COMMENT ON COLUMN company_documents.url IS '外部URLリンク（kind=urlの場合のみ)';
COMMENT ON COLUMN company_documents.tags IS 'ドキュメント分類タグ(例: 実績, 製品, 財務, 品質, セキュリティ)';

-- ============================================================================
-- 3. rfps (RFP案件)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rfps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    issuing_org TEXT NOT NULL,
    description TEXT NOT NULL,
    budget INTEGER,
    region TEXT NOT NULL,
    deadline DATE NOT NULL,
    url TEXT,
    external_doc_urls TEXT[] DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 予算は正の値のみ
    CONSTRAINT valid_budget CHECK (budget IS NULL OR budget > 0)
);

-- インデックス
CREATE INDEX idx_rfps_external_id ON rfps(external_id);
CREATE INDEX idx_rfps_region ON rfps(region);
CREATE INDEX idx_rfps_deadline ON rfps(deadline);
CREATE INDEX idx_rfps_fetched_at ON rfps(fetched_at DESC);
CREATE INDEX idx_rfps_budget ON rfps(budget) WHERE budget IS NOT NULL;
-- ベクトル類似検索用インデックス（IVFFlat: 高速近似検索）
CREATE INDEX idx_rfps_embedding ON rfps USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS有効化
ALTER TABLE rfps ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - 全認証ユーザーが参照可能
CREATE POLICY "Authenticated users can view all RFPs"
    ON rfps
    FOR SELECT
    TO authenticated
    USING (true);

-- RLSポリシー: INSERT - Service Roleのみ可能
CREATE POLICY "Only service role can insert RFPs"
    ON rfps
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- RLSポリシー: UPDATE - Service Roleのみ可能
CREATE POLICY "Only service role can update RFPs"
    ON rfps
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- RLSポリシー: DELETE - Service Roleのみ可能
CREATE POLICY "Only service role can delete RFPs"
    ON rfps
    FOR DELETE
    TO service_role
    USING (true);

-- コメント
COMMENT ON TABLE rfps IS '官公需入札案件（RFP）情報を管理するテーブル';
COMMENT ON COLUMN rfps.external_id IS 'KKJ API由来の案件ID（外部システムのID）';
COMMENT ON COLUMN rfps.issuing_org IS '発注機関名';
COMMENT ON COLUMN rfps.budget IS '案件予算（円）、不明の場合はNULL';
COMMENT ON COLUMN rfps.region IS '都道府県コード';
COMMENT ON COLUMN rfps.deadline IS '応募締切日';
COMMENT ON COLUMN rfps.external_doc_urls IS '外部資料URLの配列';
COMMENT ON COLUMN rfps.embedding IS 'OpenAI text-embedding-3-small由来の1536次元埋め込みベクトル（セマンティック検索用）';
COMMENT ON COLUMN rfps.fetched_at IS '案件情報を取得した日時';

-- ============================================================================
-- 4. bookmarks (ブックマーク)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 同一ユーザー・同一RFPの重複ブックマーク防止
    CONSTRAINT unique_user_rfp_bookmark UNIQUE (user_id, rfp_id)
);

-- インデックス
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_rfp_id ON bookmarks(rfp_id);
CREATE INDEX idx_bookmarks_created_at ON bookmarks(created_at DESC);

-- RLS有効化
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - ユーザーは自分のブックマークのみ参照可能
CREATE POLICY "Users can view their own bookmarks"
    ON bookmarks
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLSポリシー: INSERT - ユーザーは自分のブックマークのみ作成可能
CREATE POLICY "Users can create their own bookmarks"
    ON bookmarks
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLSポリシー: DELETE - ユーザーは自分のブックマークのみ削除可能
CREATE POLICY "Users can delete their own bookmarks"
    ON bookmarks
    FOR DELETE
    USING (auth.uid() = user_id);

-- コメント
COMMENT ON TABLE bookmarks IS 'ユーザーがブックマークしたRFP案件を管理するテーブル';

-- ============================================================================
-- 5. match_snapshots (マッチング結果スナップショット)
-- ============================================================================

CREATE TABLE IF NOT EXISTS match_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    rfp_id UUID NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    must_ok BOOLEAN NOT NULL,
    budget_ok BOOLEAN NOT NULL,
    region_ok BOOLEAN NOT NULL,
    factors JSONB NOT NULL,
    summary_points TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- factorsの構造検証
    CONSTRAINT valid_factors CHECK (
        jsonb_typeof(factors) = 'object' AND
        factors ? 'skill' AND
        factors ? 'must' AND
        factors ? 'budget' AND
        factors ? 'deadline' AND
        factors ? 'region'
    )
);

-- インデックス
CREATE INDEX idx_match_snapshots_user_score ON match_snapshots(user_id, score DESC);
CREATE INDEX idx_match_snapshots_user_rfp ON match_snapshots(user_id, rfp_id);
CREATE INDEX idx_match_snapshots_created_at ON match_snapshots(created_at DESC);
CREATE INDEX idx_match_snapshots_factors ON match_snapshots USING GIN(factors);

-- RLS有効化
ALTER TABLE match_snapshots ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - ユーザーは自分のスナップショットのみ参照可能
CREATE POLICY "Users can view their own match snapshots"
    ON match_snapshots
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLSポリシー: INSERT - Service Roleのみ可能（マッチング処理はバックエンドで実行）
CREATE POLICY "Only service role can create match snapshots"
    ON match_snapshots
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- RLSポリシー: DELETE - Service Roleのみ可能
CREATE POLICY "Only service role can delete match snapshots"
    ON match_snapshots
    FOR DELETE
    TO service_role
    USING (true);

-- コメント
COMMENT ON TABLE match_snapshots IS '会社プロフィールとRFP案件のマッチング結果スナップショット';
COMMENT ON COLUMN match_snapshots.score IS 'マッチングスコア（0-100）';
COMMENT ON COLUMN match_snapshots.must_ok IS '必須要件を満たしているか';
COMMENT ON COLUMN match_snapshots.budget_ok IS '予算範囲内か';
COMMENT ON COLUMN match_snapshots.region_ok IS '対応地域に含まれるか';
COMMENT ON COLUMN match_snapshots.factors IS 'スコア寄与度の詳細 {skill, must, budget, deadline, region}';
COMMENT ON COLUMN match_snapshots.summary_points IS 'マッチング結果の要約（3点程度）';

-- ============================================================================
-- 6. company_skill_embeddings (会社スキル埋め込みベクトル)
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_skill_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    skill_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_company_skill_embeddings_company_id ON company_skill_embeddings(company_id);
-- ベクトル類似検索用インデックス（IVFFlat: 高速近似検索）
CREATE INDEX idx_company_skill_embeddings_embedding ON company_skill_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS有効化
ALTER TABLE company_skill_embeddings ENABLE ROW LEVEL SECURITY;

-- RLSポリシー: SELECT - 同一会社のユーザーのみ参照可能
CREATE POLICY "Users can view their company skill embeddings"
    ON company_skill_embeddings
    FOR SELECT
    USING (
        company_id IN (
            SELECT id FROM companies WHERE user_id = auth.uid()
        )
    );

-- RLSポリシー: INSERT/UPDATE/DELETE - Service Roleのみ可能（埋め込み生成はバックエンドで実行）
CREATE POLICY "Only service role can manage skill embeddings"
    ON company_skill_embeddings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- コメント
COMMENT ON TABLE company_skill_embeddings IS '会社スキルのベクトル埋め込みを管理するテーブル（セマンティック検索用）';
COMMENT ON COLUMN company_skill_embeddings.skill_text IS 'スキル説明文（companiesテーブルのskills配列とdescriptionから生成）';
COMMENT ON COLUMN company_skill_embeddings.embedding IS 'OpenAI text-embedding-3-small由来の1536次元埋め込みベクトル';

-- ============================================================================
-- updated_at自動更新用トリガー関数
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- companiesテーブルにトリガー適用
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- company_documentsテーブルにトリガー適用
CREATE TRIGGER update_company_documents_updated_at
    BEFORE UPDATE ON company_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- rfpsテーブルにトリガー適用
CREATE TRIGGER update_rfps_updated_at
    BEFORE UPDATE ON rfps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- company_skill_embeddingsテーブルにトリガー適用
CREATE TRIGGER update_company_skill_embeddings_updated_at
    BEFORE UPDATE ON company_skill_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Supabase Storage設定
-- ============================================================================

-- Note: Storage バケットとRLSポリシーはSupabase Dashboardまたはstorage APIで設定
--
-- バケット名: company-documents
-- public: false
--
-- RLSポリシー設定（参考SQL）:
--
-- 1. INSERT Policy - ユーザーは自分のフォルダにのみアップロード可能
-- CREATE POLICY "Users can upload to their own folder"
--     ON storage.objects
--     FOR INSERT
--     WITH CHECK (
--         bucket_id = 'company-documents' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );
--
-- 2. SELECT Policy - ユーザーは自分のフォルダのファイルのみ参照可能
-- CREATE POLICY "Users can view their own files"
--     ON storage.objects
--     FOR SELECT
--     USING (
--         bucket_id = 'company-documents' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );
--
-- 3. DELETE Policy - ユーザーは自分のフォルダのファイルのみ削除可能
-- CREATE POLICY "Users can delete their own files"
--     ON storage.objects
--     FOR DELETE
--     USING (
--         bucket_id = 'company-documents' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );
--
-- パス構造: {user_id}/{document_id}/{filename}

-- ============================================================================
-- 初期化完了
-- ============================================================================

-- スキーマバージョン情報（将来のマイグレーション管理用）
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema with pgvector: companies, documents, rfps, bookmarks, match_snapshots, company_skill_embeddings')
ON CONFLICT (version) DO NOTHING;

-- 完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'RFP Radar database schema initialized successfully';
    RAISE NOTICE 'Tables created: companies, company_documents, rfps, bookmarks, match_snapshots, company_skill_embeddings';
    RAISE NOTICE 'pgvector extension enabled for semantic search';
    RAISE NOTICE 'Vector indexes created on rfps.embedding and company_skill_embeddings.embedding';
    RAISE NOTICE 'RLS policies applied to all tables';
    RAISE NOTICE 'Storage bucket setup required: company-documents (see comments in SQL file)';
END $$;

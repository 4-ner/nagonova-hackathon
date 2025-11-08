"""
RFP Radar - FastAPI バックエンドメインファイル

会社情報とスキルに基づいて官公需の入札案件をマッチングするシステムのAPIサーバー
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import check_supabase_connection
from middleware.error_handler import register_exception_handlers

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理

    起動時にSupabase接続をチェックし、終了時にクリーンアップを行います。
    """
    # 起動時の処理
    logger.info("RFP Radar API サーバーを起動しています...")
    logger.info(f"環境: {settings.environment}")

    # Supabase接続チェック
    is_connected = await check_supabase_connection()
    if is_connected:
        logger.info("Supabase接続が確立されました")
    else:
        logger.warning("Supabase接続の確認に失敗しました")

    yield

    # 終了時の処理
    logger.info("RFP Radar API サーバーをシャットダウンしています...")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="RFP Radar API",
    description="""
## 概要

RFP Radarは、会社情報とスキルに基づいて官公需の入札案件（RFP: Request for Proposal）を
マッチングするシステムのバックエンドAPIです。

## 主な機能

- **会社プロフィール管理**: 会社情報、スキル、対応地域、予算範囲の登録・更新
- **ドキュメント管理**: 会社の実績書類や提案書のアップロード・管理
- **RFP案件管理**: 官公需入札案件の一覧表示、詳細確認、フィルタリング
- **マッチング機能**: セマンティック検索による案件とスキルのマッチングスコア計算
- **ブックマーク**: 気になる案件のブックマーク保存
- **提案ドラフト生成**: RFP案件に対する提案書のドラフト自動生成

## 認証

このAPIはSupabaseのJWT認証を使用しています。
リクエストには以下のヘッダーが必要です：

```
Authorization: Bearer <your_jwt_token>
```

JWTトークンは、Supabase Authのログインエンドポイントから取得できます。

## エンドポイント概要

- `/api/companies` - 会社プロフィール管理
- `/api/documents` - ドキュメント管理（アップロード、削除）
- `/api/rfps` - RFP案件一覧・詳細取得、提案ドラフト生成
- `/api/bookmarks` - ブックマーク管理
- `/api/matching` - マッチングスコア計算・取得

## セキュリティ

- Row Level Security (RLS): Supabaseデータベースレベルでのアクセス制御
- JWTトークン検証: すべての認証が必要なエンドポイントでトークンを検証
- CORS設定: フロントエンドからのアクセスのみ許可

## エラーレスポンス

APIはHTTP標準ステータスコードを使用します：

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエストが不正
- `401 Unauthorized`: 認証が必要
- `403 Forbidden`: アクセス権限なし
- `404 Not Found`: リソースが見つからない
- `500 Internal Server Error`: サーバーエラー
    """,
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "RFP Radar Team",
        "url": "https://github.com/4-ner/nagonova-hackathon",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# エラーハンドラー登録
register_exception_handlers(app)


@app.get(
    "/",
    tags=["Root"],
    summary="APIルート",
    description="API情報を返します"
)
async def root():
    """
    ルートエンドポイント

    Returns:
        dict: API基本情報
    """
    return {
        "message": "RFP Radar API",
        "version": "0.1.0",
        "description": "会社情報とスキルに基づいて官公需の入札案件をマッチングするシステム",
        "docs": "/docs" if settings.environment == "development" else "ドキュメントは本番環境では無効です",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="ヘルスチェック",
    description="APIサーバーとSupabase接続の状態を確認します"
)
async def health_check():
    """
    ヘルスチェックエンドポイント

    サーバーの稼働状態とSupabase接続状態を返します。

    Returns:
        dict: ステータス情報
    """
    supabase_connected = await check_supabase_connection()

    return {
        "status": "ok",
        "environment": settings.environment,
        "supabase_connected": supabase_connected,
    }


# ========================================
# ルーター登録
# ========================================

from routers import companies, rfps, matching, documents, bookmarks

app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(rfps.router, prefix="/api", tags=["rfps"])
app.include_router(matching.router, prefix="/api", tags=["matching"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(bookmarks.router, prefix="/api", tags=["bookmarks"])

# ========================================
# 将来の機能拡張用ルーター
# ========================================

# TODO: 以下のルーターを追加予定
# - /api/v1/skills - スキル管理
# - /api/v1/rfps - RFP案件管理
# - /api/v1/matching - マッチング機能
# - /api/v1/auth - 認証・認可

# app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
# app.include_router(rfps.router, prefix="/api/v1/rfps", tags=["rfps"])
# app.include_router(matching.router, prefix="/api/v1/matching", tags=["matching"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level="info"
    )

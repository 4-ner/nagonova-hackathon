"""
ドキュメント管理APIルーター

会社のドキュメント（URL/ファイル）のCRUD操作と署名付きURL生成を提供します。
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId
from schemas.document import (
    DocumentCreateUrl,
    DocumentCreateFile,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    DownloadUrlResponse,
)
from services.storage import StorageService, UPLOAD_URL_EXPIRES_IN, DOWNLOAD_URL_EXPIRES_IN

logger = logging.getLogger(__name__)

router = APIRouter()


def get_storage_service(
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> StorageService:
    """StorageServiceの依存性注入"""
    return StorageService(supabase)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="ドキュメント一覧を取得",
    description="認証されたユーザーの会社に紐づくドキュメント一覧を取得します。",
)
async def get_documents(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
) -> DocumentListResponse:
    """
    ドキュメント一覧取得

    Args:
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        page: ページ番号
        page_size: ページサイズ

    Returns:
        DocumentListResponse: ドキュメント一覧

    Raises:
        HTTPException: 取得エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # オフセット計算
        offset = (page - 1) * page_size

        # ドキュメント一覧取得
        query_builder = (
            supabase.table("company_documents")
            .select("*", count="exact")
            .eq("company_id", company_id)
        )

        # ページネーション
        query_builder = query_builder.range(offset, offset + page_size - 1).order(
            "created_at", desc=True
        )

        # クエリ実行
        response = query_builder.execute()

        items = [DocumentResponse(**doc) for doc in response.data]
        total = response.count if response.count is not None else 0

        logger.info(
            f"ドキュメント一覧を取得しました: user_id={user_id}, company_id={company_id}, total={total}"
        )

        return DocumentListResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ドキュメント一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメント一覧の取得に失敗しました",
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="ドキュメント詳細を取得",
    description="指定されたドキュメントの詳細情報を取得します。",
)
async def get_document(
    document_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> DocumentResponse:
    """
    ドキュメント詳細取得

    Args:
        document_id: ドキュメントID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        DocumentResponse: ドキュメント詳細

    Raises:
        HTTPException: ドキュメントが見つからない、または取得エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # ドキュメント取得（会社IDで絞り込み）
        response = (
            supabase.table("company_documents")
            .select("*")
            .eq("id", document_id)
            .eq("company_id", company_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ドキュメントが見つかりません",
            )

        logger.debug(f"ドキュメント詳細を取得しました: document_id={document_id}")

        return DocumentResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ドキュメント詳細取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメント詳細の取得に失敗しました",
        )


@router.post(
    "/documents/url",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="URL型ドキュメントを作成",
    description="外部URLを参照するドキュメントを作成します。",
)
async def create_url_document(
    document_data: DocumentCreateUrl,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> DocumentResponse:
    """
    URL型ドキュメント作成

    Args:
        document_data: ドキュメント作成データ
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        DocumentResponse: 作成されたドキュメント

    Raises:
        HTTPException: 作成エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # ドキュメント作成
        insert_data = {
            "company_id": company_id,
            "title": document_data.title,
            "description": document_data.description,
            "kind": document_data.kind,
            "url": str(document_data.url),
        }

        response = supabase.table("company_documents").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ドキュメントの作成に失敗しました",
            )

        logger.info(
            f"URL型ドキュメントを作成しました: user_id={user_id}, company_id={company_id}, "
            f"document_id={response.data[0]['id']}"
        )

        return DocumentResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL型ドキュメント作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメントの作成に失敗しました",
        )


@router.post(
    "/documents/upload-url",
    response_model=UploadUrlResponse,
    summary="アップロード用署名付きURLを生成",
    description="ファイルをアップロードするための署名付きURLを生成します。",
)
async def generate_upload_url(
    request_data: UploadUrlRequest,
    user_id: CurrentUserId,
    storage_service: Annotated[StorageService, Depends(get_storage_service)] = None,
) -> UploadUrlResponse:
    """
    アップロード用署名付きURL生成

    Args:
        request_data: アップロードURL生成リクエスト
        user_id: 認証ユーザーID
        storage_service: Storageサービス

    Returns:
        UploadUrlResponse: 署名付きURLとStorageパス

    Raises:
        HTTPException: URL生成エラー
    """
    try:
        upload_url, storage_path = storage_service.create_signed_upload_url(
            user_id, request_data.filename, request_data.file_size
        )

        logger.info(f"アップロード用署名付きURLを生成しました: user_id={user_id}, filename={request_data.filename}")

        return UploadUrlResponse(
            upload_url=upload_url,
            storage_path=storage_path,
            expires_in=UPLOAD_URL_EXPIRES_IN,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"アップロード用URL生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="署名付きURLの生成に失敗しました",
        )


@router.post(
    "/documents/file",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ファイル型ドキュメントを作成",
    description="アップロード済みファイルのドキュメントレコードを作成します。",
)
async def create_file_document(
    document_data: DocumentCreateFile,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> DocumentResponse:
    """
    ファイル型ドキュメント作成

    アップロード完了後、このエンドポイントを呼び出してドキュメントレコードを作成します。

    Args:
        document_data: ドキュメント作成データ
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        DocumentResponse: 作成されたドキュメント

    Raises:
        HTTPException: 作成エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # ドキュメント作成
        insert_data = {
            "company_id": company_id,
            "title": document_data.title,
            "description": document_data.description,
            "kind": document_data.kind,
            "storage_path": document_data.storage_path,
            "size_bytes": document_data.size_bytes,
        }

        response = supabase.table("company_documents").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ドキュメントの作成に失敗しました",
            )

        logger.info(
            f"ファイル型ドキュメントを作成しました: user_id={user_id}, company_id={company_id}, "
            f"document_id={response.data[0]['id']}"
        )

        return DocumentResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイル型ドキュメント作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメントの作成に失敗しました",
        )


@router.get(
    "/documents/{document_id}/download-url",
    response_model=DownloadUrlResponse,
    summary="ダウンロード用署名付きURLを生成",
    description="ファイルをダウンロードするための署名付きURLを生成します。",
)
async def generate_download_url(
    document_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)] = None,
) -> DownloadUrlResponse:
    """
    ダウンロード用署名付きURL生成

    Args:
        document_id: ドキュメントID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        storage_service: Storageサービス

    Returns:
        DownloadUrlResponse: 署名付きURL

    Raises:
        HTTPException: ドキュメントが見つからない、またはURL生成エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # ドキュメント取得
        response = (
            supabase.table("company_documents")
            .select("storage_path")
            .eq("id", document_id)
            .eq("company_id", company_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ドキュメントが見つかりません",
            )

        storage_path = response.data[0].get("storage_path")

        if not storage_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このドキュメントはファイル型ではありません",
            )

        # 署名付きダウンロードURL生成
        download_url = storage_service.create_signed_download_url(storage_path)

        logger.info(f"ダウンロード用署名付きURLを生成しました: document_id={document_id}")

        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=DOWNLOAD_URL_EXPIRES_IN,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ダウンロード用URL生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="署名付きURLの生成に失敗しました",
        )


@router.put(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="ドキュメント情報を更新",
    description="ドキュメントのタイトルや説明を更新します。",
)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> DocumentResponse:
    """
    ドキュメント更新

    Args:
        document_id: ドキュメントID
        document_data: ドキュメント更新データ
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        DocumentResponse: 更新されたドキュメント

    Raises:
        HTTPException: ドキュメントが見つからない、または更新エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # 更新データを構築
        update_data = {}
        if document_data.title is not None:
            update_data["title"] = document_data.title
        if document_data.description is not None:
            update_data["description"] = document_data.description

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新するデータがありません",
            )

        # ドキュメント更新
        response = (
            supabase.table("company_documents")
            .update(update_data)
            .eq("id", document_id)
            .eq("company_id", company_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ドキュメントが見つかりません",
            )

        logger.info(f"ドキュメントを更新しました: document_id={document_id}")

        return DocumentResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ドキュメント更新エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメントの更新に失敗しました",
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ドキュメントを削除",
    description="ドキュメントとStorageに保存されているファイルを削除します。",
)
async def delete_document(
    document_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)] = None,
) -> None:
    """
    ドキュメント削除

    Args:
        document_id: ドキュメントID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        storage_service: Storageサービス

    Raises:
        HTTPException: ドキュメントが見つからない、または削除エラー
    """
    try:
        # ユーザーの会社IDを取得
        user_response = supabase.table("users").select("company_id").eq("id", user_id).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

        company_id = user_response.data[0]["company_id"]

        # ドキュメント取得
        response = (
            supabase.table("company_documents")
            .select("storage_path")
            .eq("id", document_id)
            .eq("company_id", company_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ドキュメントが見つかりません",
            )

        storage_path = response.data[0].get("storage_path")

        # Storageからファイル削除（ファイル型の場合）
        if storage_path:
            try:
                storage_service.delete_file(storage_path)
            except Exception as e:
                logger.warning(f"Storageファイル削除エラー（続行します）: {e}")

        # ドキュメントレコード削除
        delete_response = (
            supabase.table("company_documents")
            .delete()
            .eq("id", document_id)
            .eq("company_id", company_id)
            .execute()
        )

        logger.info(f"ドキュメントを削除しました: document_id={document_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ドキュメント削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ドキュメントの削除に失敗しました",
        )

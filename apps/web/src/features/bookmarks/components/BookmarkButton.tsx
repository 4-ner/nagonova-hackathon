'use client';

import { useState } from 'react';
import { Bookmark, BookmarkPlus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  useIsBookmarked,
  useAddBookmark,
  useRemoveBookmark,
} from '../hooks/useBookmarks';

interface BookmarkButtonProps {
  /** RFP ID */
  rfpId: string;
  /** ボタンサイズ */
  size?: 'default' | 'sm' | 'lg' | 'icon';
  /** ボタンバリアント */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  /** アイコンのみ表示 */
  iconOnly?: boolean;
}

/**
 * ブックマークボタンコンポーネント
 *
 * RFP案件をブックマークに追加/削除するボタンです。
 * ブックマーク済みの場合は塗りつぶされたアイコン、未登録の場合は枠だけのアイコンを表示します。
 *
 * @example
 * ```tsx
 * <BookmarkButton rfpId="rfp-123" />
 * <BookmarkButton rfpId="rfp-123" iconOnly size="icon" variant="ghost" />
 * ```
 */
export function BookmarkButton({
  rfpId,
  size = 'default',
  variant = 'outline',
  iconOnly = false,
}: BookmarkButtonProps) {
  const { isBookmarked, isLoading: isCheckingBookmark } = useIsBookmarked(rfpId);
  const { trigger: addBookmark, isMutating: isAdding } = useAddBookmark();
  const { trigger: removeBookmark, isMutating: isRemoving } = useRemoveBookmark(rfpId);

  const [isProcessing, setIsProcessing] = useState(false);

  // ローディング状態
  const isLoading = isCheckingBookmark || isAdding || isRemoving || isProcessing;

  /**
   * ブックマークのトグル処理
   */
  const handleToggleBookmark = async (e: React.MouseEvent) => {
    e.preventDefault(); // リンクの遷移を防ぐ
    e.stopPropagation(); // 親要素のクリックイベントを防ぐ

    if (isLoading) return;

    setIsProcessing(true);

    try {
      if (isBookmarked) {
        // ブックマーク削除
        await removeBookmark();
        toast.success('ブックマークから削除しました', {
          description: 'この案件がブックマークから削除されました。',
        });
      } else {
        // ブックマーク追加
        await addBookmark({ rfp_id: rfpId });
        toast.success('ブックマークに追加しました', {
          description: 'この案件がブックマークに追加されました。',
        });
      }
    } catch (error) {
      console.error('Bookmark error:', error);
      toast.error('操作に失敗しました', {
        description:
          error instanceof Error
            ? error.message
            : 'ブックマーク操作中にエラーが発生しました。',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // アイコンの決定
  const Icon = isLoading ? Loader2 : isBookmarked ? Bookmark : BookmarkPlus;

  // アイコンのみ表示
  if (iconOnly) {
    return (
      <Button
        variant={variant}
        size={size}
        onClick={handleToggleBookmark}
        disabled={isLoading}
        aria-label={isBookmarked ? 'ブックマークから削除' : 'ブックマークに追加'}
        className="shrink-0"
      >
        <Icon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      </Button>
    );
  }

  // テキスト付きボタン
  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleToggleBookmark}
      disabled={isLoading}
      className="shrink-0"
    >
      <Icon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      {isBookmarked ? 'ブックマーク済み' : 'ブックマーク'}
    </Button>
  );
}

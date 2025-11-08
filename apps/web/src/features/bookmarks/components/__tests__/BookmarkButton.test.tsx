/**
 * BookmarkButtonコンポーネントのテスト
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { toast } from 'sonner';
import { BookmarkButton } from '../BookmarkButton';
import * as bookmarkHooks from '../../hooks/useBookmarks';
import { renderWithSWR } from '@/__tests__/utils/test-utils';

// モックの設定
jest.mock('../../hooks/useBookmarks');
jest.mock('sonner');

const mockedUseIsBookmarked = bookmarkHooks.useIsBookmarked as jest.MockedFunction<
  typeof bookmarkHooks.useIsBookmarked
>;
const mockedUseAddBookmark = bookmarkHooks.useAddBookmark as jest.MockedFunction<
  typeof bookmarkHooks.useAddBookmark
>;
const mockedUseRemoveBookmark = bookmarkHooks.useRemoveBookmark as jest.MockedFunction<
  typeof bookmarkHooks.useRemoveBookmark
>;
const mockedToast = toast as jest.Mocked<typeof toast>;

describe('BookmarkButton', () => {
  const mockRfpId = 'rfp-test-123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('レンダリング', () => {
    it('未ブックマーク状態でボタンが表示される', () => {
      // モックの設定
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンの存在確認
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('ブックマーク');
    });

    it('ブックマーク済み状態でボタンが表示される', () => {
      // モックの設定（ブックマーク済み）
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: true,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンの存在確認
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('ブックマーク済み');
    });

    it('アイコンのみモードで表示される', () => {
      // モックの設定
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング（アイコンのみ）
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} iconOnly />);

      // ボタンの存在確認
      const button = screen.getByRole('button', { name: /ブックマークに追加/ });
      expect(button).toBeInTheDocument();
      // テキストが表示されていないことを確認
      expect(button).not.toHaveTextContent('ブックマーク');
    });

    it('ローディング中はボタンが無効化される', () => {
      // モックの設定（ローディング中）
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: true,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンが無効化されていることを確認
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('ブックマーク追加', () => {
    it('未ブックマーク状態でクリックするとブックマーク追加される', async () => {
      const user = userEvent.setup();
      const mockAddTrigger = jest.fn().mockResolvedValue({});

      // モックの設定
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: mockAddTrigger,
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンをクリック
      const button = screen.getByRole('button');
      await user.click(button);

      // ブックマーク追加が呼ばれたことを確認
      await waitFor(() => {
        expect(mockAddTrigger).toHaveBeenCalledWith({ rfp_id: mockRfpId });
      });

      // 成功トーストが表示されたことを確認
      expect(mockedToast.success).toHaveBeenCalledWith(
        'ブックマークに追加しました',
        expect.any(Object)
      );
    });

    it('ブックマーク追加に失敗した場合エラートーストが表示される', async () => {
      const user = userEvent.setup();
      const error = new Error('Network error');
      const mockAddTrigger = jest.fn().mockRejectedValue(error);

      // モックの設定
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: mockAddTrigger,
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンをクリック
      const button = screen.getByRole('button');
      await user.click(button);

      // エラートーストが表示されたことを確認
      await waitFor(() => {
        expect(mockedToast.error).toHaveBeenCalledWith(
          '操作に失敗しました',
          expect.any(Object)
        );
      });
    });
  });

  describe('ブックマーク削除', () => {
    it('ブックマーク済み状態でクリックするとブックマーク削除される', async () => {
      const user = userEvent.setup();
      const mockRemoveTrigger = jest.fn().mockResolvedValue({});

      // モックの設定（ブックマーク済み）
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: true,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: mockRemoveTrigger,
        isMutating: false,
      } as any);

      // レンダリング
      renderWithSWR(<BookmarkButton rfpId={mockRfpId} />);

      // ボタンをクリック
      const button = screen.getByRole('button');
      await user.click(button);

      // ブックマーク削除が呼ばれたことを確認
      await waitFor(() => {
        expect(mockRemoveTrigger).toHaveBeenCalled();
      });

      // 成功トーストが表示されたことを確認
      expect(mockedToast.success).toHaveBeenCalledWith(
        'ブックマークから削除しました',
        expect.any(Object)
      );
    });
  });

  describe('イベントの伝播', () => {
    it('クリック時にイベントの伝播が停止される', async () => {
      const user = userEvent.setup();
      const mockAddTrigger = jest.fn().mockResolvedValue({});
      const mockParentClick = jest.fn();

      // モックの設定
      mockedUseIsBookmarked.mockReturnValue({
        isBookmarked: false,
        isLoading: false,
      });
      mockedUseAddBookmark.mockReturnValue({
        trigger: mockAddTrigger,
        isMutating: false,
      } as any);
      mockedUseRemoveBookmark.mockReturnValue({
        trigger: jest.fn(),
        isMutating: false,
      } as any);

      // 親要素でラップしてレンダリング
      const { container } = renderWithSWR(
        <div onClick={mockParentClick}>
          <BookmarkButton rfpId={mockRfpId} />
        </div>
      );

      // ボタンをクリック
      const button = screen.getByRole('button');
      await user.click(button);

      // ブックマーク追加が呼ばれたことを確認
      await waitFor(() => {
        expect(mockAddTrigger).toHaveBeenCalled();
      });

      // 親要素のクリックハンドラが呼ばれていないことを確認（イベント伝播停止）
      expect(mockParentClick).not.toHaveBeenCalled();
    });
  });
});

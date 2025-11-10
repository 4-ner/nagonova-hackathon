import { Header } from '@/components/layout/Header';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';

/**
 * ダッシュボードレイアウト
 *
 * 認証が必要なページ全体で共通のレイアウト
 * - グローバルヘッダーナビゲーション
 * - パンくずリスト
 */
export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ヘッダーナビゲーション */}
      <Header />

      {/* パンくずリスト */}
      <Breadcrumbs />

      {/* メインコンテンツ */}
      <main className="flex-1">{children}</main>

      {/* フッター（オプション） */}
      <footer className="border-t py-6 md:py-8">
        <div className="container text-center text-sm text-muted-foreground">
          <p>&copy; 2025 RFP Radar. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

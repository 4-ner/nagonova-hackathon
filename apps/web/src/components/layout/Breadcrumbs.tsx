'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

interface BreadcrumbConfig {
  label: string;
  href?: string;
}

/**
 * パンくずリスト設定
 *
 * パスに応じた表示ラベルとリンクを定義
 */
const breadcrumbConfig: Record<string, BreadcrumbConfig> = {
  rfps: { label: '案件一覧', href: '/rfps' },
  bookmarks: { label: 'ブックマーク', href: '/bookmarks' },
  documents: { label: 'ドキュメント', href: '/documents' },
  profile: { label: '会社プロフィール', href: '/profile/edit' },
  edit: { label: '編集' },
  setup: { label: '初期設定' },
  proposal: { label: '提案ドラフト' },
};

/**
 * パンくずリストコンポーネント
 *
 * 現在のパスに基づいてパンくずリストを自動生成します
 */
export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  // ホームページやログインページでは表示しない
  if (segments.length === 0 || pathname === '/login') {
    return null;
  }

  /**
   * パスセグメントからパンくず項目を生成
   */
  const generateBreadcrumbs = (): BreadcrumbConfig[] => {
    const breadcrumbs: BreadcrumbConfig[] = [];
    let currentPath = '';

    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;

      // UUIDやその他の動的IDをスキップ
      const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        segment
      );

      if (isUuid) {
        // 動的IDの場合は「詳細」として表示
        breadcrumbs.push({
          label: '詳細',
          href: index === segments.length - 1 ? undefined : currentPath,
        });
        return;
      }

      // 設定に基づいてラベルを取得
      const config = breadcrumbConfig[segment];
      if (config) {
        breadcrumbs.push({
          label: config.label,
          // 最後のセグメント以外はリンクを有効にする
          href: index === segments.length - 1 ? undefined : config.href || currentPath,
        });
      } else {
        // 設定がない場合はセグメント名をそのまま使用
        breadcrumbs.push({
          label: segment.charAt(0).toUpperCase() + segment.slice(1),
          href: index === segments.length - 1 ? undefined : currentPath,
        });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  // パンくずが1つもない場合は表示しない
  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <div className="border-b bg-muted/30">
      <div className="container py-3">
        <Breadcrumb>
          <BreadcrumbList>
            {/* ホームアイコン */}
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link href="/rfps" className="flex items-center gap-1">
                  <Home className="h-4 w-4" />
                  <span className="sr-only">ホーム</span>
                </Link>
              </BreadcrumbLink>
            </BreadcrumbItem>

            {/* 各パンくず項目 */}
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                <BreadcrumbSeparator>
                  <ChevronRight className="h-4 w-4" />
                </BreadcrumbSeparator>
                <BreadcrumbItem>
                  {crumb.href ? (
                    <BreadcrumbLink asChild>
                      <Link href={crumb.href}>{crumb.label}</Link>
                    </BreadcrumbLink>
                  ) : (
                    <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                  )}
                </BreadcrumbItem>
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </div>
  );
}

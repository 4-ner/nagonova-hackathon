'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FileText, Bookmark, Building2, LogOut, User, Radar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

/**
 * グローバルヘッダーナビゲーション
 *
 * アプリケーション全体で使用するヘッダーナビゲーションコンポーネント
 */
export function Header() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  const isActive = (path: string) => {
    if (path === '/rfps') {
      return pathname === path || pathname.startsWith('/rfps/');
    }
    return pathname === path || pathname.startsWith(path + '/');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* ロゴ */}
        <Link href="/rfps" className="flex items-center gap-2 font-bold text-xl">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Radar className="h-6 w-6 text-primary" />
          </div>
          <span className="hidden sm:inline-block">RFP Radar</span>
        </Link>

        {/* ナビゲーションメニュー */}
        <NavigationMenu className="hidden md:flex">
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink
                asChild
                className={cn(
                  navigationMenuTriggerStyle(),
                  isActive('/rfps') && 'bg-accent text-accent-foreground'
                )}
              >
                <Link href="/rfps">
                  <FileText className="h-4 w-4 mr-2" />
                  案件一覧
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>

            <NavigationMenuItem>
              <NavigationMenuLink
                asChild
                className={cn(
                  navigationMenuTriggerStyle(),
                  isActive('/bookmarks') && 'bg-accent text-accent-foreground'
                )}
              >
                <Link href="/bookmarks">
                  <Bookmark className="h-4 w-4 mr-2" />
                  ブックマーク
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>

            <NavigationMenuItem>
              <NavigationMenuLink
                asChild
                className={cn(
                  navigationMenuTriggerStyle(),
                  isActive('/documents') && 'bg-accent text-accent-foreground'
                )}
              >
                <Link href="/documents">
                  <FileText className="h-4 w-4 mr-2" />
                  ドキュメント
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>

            <NavigationMenuItem>
              <NavigationMenuLink
                asChild
                className={cn(
                  navigationMenuTriggerStyle(),
                  isActive('/profile') && 'bg-accent text-accent-foreground'
                )}
              >
                <Link href="/profile/edit">
                  <Building2 className="h-4 w-4 mr-2" />
                  会社プロフィール
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>

        {/* モバイルメニュー + ユーザーメニュー */}
        <div className="flex items-center gap-2">
          {/* ユーザーメニュー */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="bg-primary/10">
                    <User className="h-5 w-5" />
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">アカウント</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />

              {/* モバイル用メニュー項目 */}
              <div className="md:hidden">
                <Link href="/rfps">
                  <DropdownMenuItem className={cn(isActive('/rfps') && 'bg-accent')}>
                    <FileText className="h-4 w-4 mr-2" />
                    案件一覧
                  </DropdownMenuItem>
                </Link>
                <Link href="/bookmarks">
                  <DropdownMenuItem className={cn(isActive('/bookmarks') && 'bg-accent')}>
                    <Bookmark className="h-4 w-4 mr-2" />
                    ブックマーク
                  </DropdownMenuItem>
                </Link>
                <Link href="/documents">
                  <DropdownMenuItem className={cn(isActive('/documents') && 'bg-accent')}>
                    <FileText className="h-4 w-4 mr-2" />
                    ドキュメント
                  </DropdownMenuItem>
                </Link>
                <Link href="/profile/edit">
                  <DropdownMenuItem className={cn(isActive('/profile') && 'bg-accent')}>
                    <Building2 className="h-4 w-4 mr-2" />
                    会社プロフィール
                  </DropdownMenuItem>
                </Link>
                <DropdownMenuSeparator />
              </div>

              <DropdownMenuItem onClick={handleSignOut}>
                <LogOut className="h-4 w-4 mr-2" />
                ログアウト
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}

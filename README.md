# RFP Radar


## 構成
- apps/api … FastAPI 
- apps/web … Next.js + shadcn/ui
- packages/shared … 共有ユーティリティ
- supabase/sql … スキーマやポリシー
- infra … IaC / デプロイ用

## 環境変数
- ルート `.env` を `.env.example` から作成し、Supabase の鍵を設定

## 起動モード
- 開発（軽量）：uvx（API） + pnpm dev（Web）



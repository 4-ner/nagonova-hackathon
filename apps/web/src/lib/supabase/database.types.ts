/**
 * Supabaseデータベース型定義
 *
 * この型定義は、Supabase CLIで自動生成することを推奨します：
 * npx supabase gen types typescript --project-id <project-id> > src/lib/supabase/database.types.ts
 *
 * 現在はプレースホルダーとして空の型定義を使用しています。
 */
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

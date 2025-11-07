import { z } from 'zod';

/**
 * 会社プロフィールのバリデーションスキーマ
 */
export const companyProfileSchema = z.object({
  /** 会社名 */
  name: z
    .string()
    .min(1, '会社名は必須です')
    .max(200, '会社名は200文字以内で入力してください'),

  /** 会社説明 */
  description: z.string().optional(),

  /** 対応可能地域 */
  regions: z.array(z.string()).default([]),

  /** 希望案件規模 - 最小金額 */
  budget_min: z.coerce
    .number()
    .int('整数で入力してください')
    .min(0, '0以上の金額を入力してください')
    .optional()
    .or(z.literal('')),

  /** 希望案件規模 - 最大金額 */
  budget_max: z.coerce
    .number()
    .int('整数で入力してください')
    .min(0, '0以上の金額を入力してください')
    .optional()
    .or(z.literal('')),

  /** 保有スキル */
  skills: z
    .array(z.string())
    .min(1, '最低1つのスキルを入力してください')
    .default([]),

  /** NGキーワード */
  ng_keywords: z.array(z.string()).default([]),
}).refine(
  (data) => {
    // 最小・最大が両方存在する場合のみバリデーション
    if (
      data.budget_min !== undefined &&
      data.budget_min !== '' &&
      data.budget_max !== undefined &&
      data.budget_max !== ''
    ) {
      return Number(data.budget_min) <= Number(data.budget_max);
    }
    return true;
  },
  {
    message: '最小金額は最大金額以下にしてください',
    path: ['budget_min'],
  }
);

/**
 * 会社プロフィールフォームの型
 */
export type CompanyProfileFormData = z.infer<typeof companyProfileSchema>;

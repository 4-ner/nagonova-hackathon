'use client';

import { useState, KeyboardEvent } from 'react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { X } from 'lucide-react';

interface TagInputProps {
  /** タグのリスト */
  value: string[];
  /** タグの変更ハンドラ */
  onChange: (tags: string[]) => void;
  /** プレースホルダー */
  placeholder?: string;
  /** 無効化フラグ */
  disabled?: boolean;
}

/**
 * タグ入力コンポーネント
 *
 * Enterまたはカンマでタグを追加できます。
 */
export function TagInput({
  value,
  onChange,
  placeholder = 'タグを入力してEnterキーを押す',
  disabled = false,
}: TagInputProps) {
  const [inputValue, setInputValue] = useState('');

  /**
   * タグを追加
   */
  const addTag = (tag: string) => {
    const trimmedTag = tag.trim();
    if (trimmedTag && !value.includes(trimmedTag)) {
      onChange([...value, trimmedTag]);
    }
    setInputValue('');
  };

  /**
   * タグを削除
   */
  const removeTag = (tagToRemove: string) => {
    onChange(value.filter((tag) => tag !== tagToRemove));
  };

  /**
   * キーボードイベントハンドラ
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      // 入力が空の状態でBackspaceを押したら最後のタグを削除
      removeTag(value[value.length - 1]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {value.map((tag) => (
          <Badge key={tag} variant="secondary" className="gap-1">
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              disabled={disabled}
              className="ml-1 rounded-full hover:bg-muted"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>
      <Input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
      />
      <p className="text-xs text-muted-foreground">
        Enterキーまたはカンマで追加できます
      </p>
    </div>
  );
}

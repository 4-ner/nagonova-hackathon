import type { Config } from 'jest';

// Jestの設定
const config: Config = {
  // テスト環境
  testEnvironment: 'jest-environment-jsdom',

  // セットアップファイル
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],

  // テストファイルのパターン
  testMatch: [
    '**/__tests__/**/*.{ts,tsx}',
    '**/*.{spec,test}.{ts,tsx}',
  ],

  // カバレッジ収集対象
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/__tests__/**',
  ],

  // モジュールパス解決（tsconfig.jsonのpathsと一致させる）
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    // CSS/画像ファイルのモック
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
  },

  // トランスフォーム設定
  transform: {
    '^.+\\.(t|j)sx?$': ['@swc/jest', {
      jsc: {
        parser: {
          syntax: 'typescript',
          tsx: true,
          decorators: false,
        },
        transform: {
          react: {
            runtime: 'automatic',
          },
        },
      },
    }],
  },

  // カバレッジレポート設定
  coverageReporters: ['text', 'lcov', 'html'],

  // テストのタイムアウト
  testTimeout: 10000,

  // transformIgnorePatternsの設定（node_modulesを変換対象に）
  transformIgnorePatterns: [
    'node_modules/(?!(react-hook-form|swr)/)',
  ],
};

export default config;

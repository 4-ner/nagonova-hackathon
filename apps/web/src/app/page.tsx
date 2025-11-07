"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>("チェック中...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiBaseUrl =
          process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
        const response = await fetch(`${apiBaseUrl}/healthz`);
        const data = await response.json();
        setHealthStatus(`API Status: ${data.status}`);
      } catch (err) {
        setError(
          `API接続エラー: ${err instanceof Error ? err.message : "不明なエラー"}`
        );
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-center gap-8 py-32 px-16 bg-white dark:bg-black">
        <h1 className="text-4xl font-bold text-black dark:text-zinc-50">
          RFP Radar
        </h1>

        <div className="flex flex-col items-center gap-4 text-center">
          <h2 className="text-2xl font-semibold text-black dark:text-zinc-50">
            ヘルスチェック
          </h2>

          {error ? (
            <p className="text-lg text-red-600 dark:text-red-400">{error}</p>
          ) : (
            <p className="text-lg text-green-600 dark:text-green-400">
              {healthStatus}
            </p>
          )}
        </div>

        <div className="text-sm text-zinc-500 dark:text-zinc-400">
          <p>APIエンドポイント: /healthz</p>
          <p>
            API URL:{" "}
            {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}
          </p>
        </div>
      </main>
    </div>
  );
}

# {{ rfp.title }} への提案書

## 1. 概要

案件名: {{ rfp.title }}
発注機関: {{ rfp.issuing_org }}
予算: {{ rfp.budget | format_budget }}
締切日: {{ rfp.deadline | format_date }}

当社{{ company.name }}は、{{ company.description }}を通じて培った豊富な経験とスキルを活かし、本案件に最適なソリューションを提供いたします。

### マッチング評価
{% if match_score is not none -%}
- マッチングスコア: {{ match_score }}点
{% endif -%}
{% for point in summary_points -%}
- {{ point }}
{% endfor %}

## 2. 提案体制

### 企業概要
- 会社名: {{ company.name }}
{% if company.description -%}
- 企業説明: {{ company.description }}
{% endif -%}
- 対応地域: {{ company.regions | join(', ') }}

### 保有スキル
{% for skill in company.skills -%}
- {{ skill }}
{% endfor %}

## 3. 技術提案

### 活用予定技術
{% for skill in company.skills[:5] -%}
- **{{ skill }}**: 当社が保有する技術により、高品質なソリューションを提供可能です。
{% endfor %}

### 案件への適用方法
{{ rfp.description[:500] }}{% if rfp.description|length > 500 %}...{% endif %}

（以下、案件内容に基づいた具体的な技術提案をご記入ください）

## 4. リスクと対策

### 想定リスク
- スケジュールリスク: 締切（{{ rfp.deadline | format_date }}）に向けた計画的な進行
- 予算リスク: 見積額{{ rfp.budget | format_budget }}に基づく適切なリソース配分
- 品質リスク: 品質管理体制の徹底

### 対策
- プロジェクト管理手法の導入
- 定期的な進捗報告と課題管理
- 品質保証プロセスの確立

## 5. 参考URL

### 案件情報
{% if rfp.url -%}
- 元案件URL: {{ rfp.url }}
{% endif %}

### 外部資料
{% if rfp.external_doc_urls and rfp.external_doc_urls|length > 0 -%}
{% for url in rfp.external_doc_urls -%}
- {{ url }}
{% endfor -%}
{% else -%}
（外部資料なし）
{% endif -%}

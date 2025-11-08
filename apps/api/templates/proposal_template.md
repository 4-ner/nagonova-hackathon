# {{ rfp.title }} への提案書

## 1. 概要

案件名: {{ rfp.title }}
発注機関: {{ rfp.issuing_org }}
予算: {{ rfp.budget | format_budget }}
締切日: {{ rfp.deadline | format_date }}
{% if rfp.category -%}
案件カテゴリ: {{ rfp.category }}
{% endif -%}
{% if rfp.procedure_type -%}
入札手続き: {{ rfp.procedure_type }}
{% endif -%}
{% if rfp.item_code -%}
品目分類コード: {{ rfp.item_code }}
{% endif -%}

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

## 4. スケジュールと対応体制

### 主要スケジュール
- 応募締切: {{ rfp.deadline | format_date }}
{% if rfp.cft_issue_date -%}
- 仕様書発行日: {{ rfp.cft_issue_date | format_date }}
{% endif -%}
{% if rfp.tender_deadline -%}
- 入札締切: {{ rfp.tender_deadline | format_date }}
{% endif -%}
{% if rfp.opening_event_date -%}
- 開札予定日: {{ rfp.opening_event_date | format_date }}
{% endif -%}

### 参加資格
{% if rfp.certification -%}
{{ rfp.certification }}

当社は上記の参加資格を満たしており、適切な体制で本案件に対応可能です。
{% else -%}
（本案件の参加資格については、発注機関の要件を満たす体制を整えております）
{% endif -%}

{% if rfp.lg_code or rfp.city_code -%}
### 対応地域
{% if rfp.lg_code -%}
- 地方自治体コード: {{ rfp.lg_code }}
{% endif -%}
{% if rfp.city_code -%}
- 市区町村コード: {{ rfp.city_code }}
{% endif -%}

当社の対応地域（{{ company.regions | join(', ') }}）に含まれており、地域に密着したサポートを提供できます。
{% endif -%}

## 5. リスクと対策

### 想定リスク
- スケジュールリスク: 締切（{{ rfp.deadline | format_date }}）に向けた計画的な進行
- 予算リスク: 見積額{{ rfp.budget | format_budget }}に基づく適切なリソース配分
- 品質リスク: 品質管理体制の徹底

### 対策
- プロジェクト管理手法の導入
- 定期的な進捗報告と課題管理
- 品質保証プロセスの確立

## 6. 参考URL

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

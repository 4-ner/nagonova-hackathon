"""
KKJ API実データ取得・分析スクリプト

実際のKKJ APIからサンプルデータを取得して、DB設計との適合性を分析します。
"""

import json
import sys
from datetime import datetime
from services.kkj_api import KKJAPIClient

def analyze_kkj_data():
    """KKJ APIから実データを取得して分析"""
    
    print("=" * 80)
    print("KKJ API実データ取得・分析")
    print("=" * 80)
    
    # KKJ APIクライアント初期化
    client = KKJAPIClient()
    
    # 東京都（コード13）から5件取得
    try:
        print("\n[1] KKJ APIからデータを取得中...")
        print("   対象: 東京都（コード13）、取得件数: 5件")
        
        rfps = client.fetch_rfps(
            prefecture_code="13",
            count=5,
            query="*",
            ng_keywords=[]
        )
        
        print(f"   取得成功: {len(rfps)}件\n")
        
        # サンプルデータを保存
        with open('/tmp/kkj_sample_data.json', 'w', encoding='utf-8') as f:
            json.dump(rfps, f, ensure_ascii=False, indent=2)
        
        print("[2] APIレスポンス構造の詳細分析\n")
        
        if rfps:
            # 最初のレコードを詳細表示
            sample = rfps[0]
            print("◆ サンプルレコード #1:")
            print("-" * 80)
            
            for key, value in sample.items():
                value_type = type(value).__name__
                if isinstance(value, str):
                    display_value = value[:100] + "..." if len(value) > 100 else value
                elif isinstance(value, list):
                    display_value = f"list({len(value)} items)"
                else:
                    display_value = str(value)
                
                print(f"  {key:30s} | Type: {value_type:10s} | Value: {display_value}")
            
            print("\n[3] 全レコードのフィールド統計\n")
            
            # すべてのレコードでフィールドの出現状況を集計
            field_stats = {}
            for rfp in rfps:
                for key, value in rfp.items():
                    if key not in field_stats:
                        field_stats[key] = {
                            'count': 0,
                            'non_empty': 0,
                            'types': set(),
                            'sample_values': []
                        }
                    
                    field_stats[key]['count'] += 1
                    if value:
                        field_stats[key]['non_empty'] += 1
                    
                    field_stats[key]['types'].add(type(value).__name__)
                    
                    if len(field_stats[key]['sample_values']) < 2 and value:
                        sample_val = str(value)[:80] if not isinstance(value, list) else f"list[{len(value)}]"
                        field_stats[key]['sample_values'].append(sample_val)
            
            # フィールド統計を表示
            print(f"{'Field Name':30s} | {'出現率':8s} | {'非空':8s} | {'データ型':15s} | {'サンプル値'}")
            print("-" * 120)
            
            for key in sorted(field_stats.keys()):
                stats = field_stats[key]
                count = stats['count']
                non_empty = stats['non_empty']
                types = ', '.join(sorted(stats['types']))
                sample = stats['sample_values'][0] if stats['sample_values'] else "-"
                
                appear_rate = f"{count}/{len(rfps)}" if count == len(rfps) else f"{count}/{len(rfps)}"
                non_empty_rate = f"{non_empty}/{len(rfps)}"
                
                print(f"{key:30s} | {appear_rate:8s} | {non_empty_rate:8s} | {types:15s} | {sample}")
            
            print("\n[4] DB設計との比較\n")
            print("◆ DB (rfps テーブル)のカラム:")
            print("-" * 80)
            db_columns = {
                'id': '(UUID, 自動生成)',
                'external_id': '(TEXT, 必須, UNIQUE)',
                'title': '(TEXT, 必須)',
                'issuing_org': '(TEXT, 必須)',
                'description': '(TEXT, 必須)',
                'budget': '(INTEGER, オプション)',
                'region': '(TEXT, 必須)',
                'deadline': '(DATE, 必須)',
                'url': '(TEXT, オプション)',
                'external_doc_urls': '(TEXT[], オプション)',
                'embedding': '(vector(1536), オプション)',
                'created_at': '(TIMESTAMP, 自動)',
                'updated_at': '(TIMESTAMP, 自動)',
                'fetched_at': '(TIMESTAMP, 自動)',
            }
            
            for col, info in db_columns.items():
                print(f"  {col:30s} {info}")
            
            print("\n◆ KKJ APIのレスポンスフィールド:")
            print("-" * 80)
            for key in sorted(field_stats.keys()):
                stats = field_stats[key]
                types = ', '.join(sorted(stats['types']))
                non_empty = stats['non_empty']
                print(f"  {key:30s} (Type: {types:15s}, 非空: {non_empty}/{len(rfps)})")
            
            print("\n[5] マッピング候補\n")
            
            mapping = {
                'external_id': ('key', 'result_id', '必須'),
                'title': ('project_name', 'テキストフィールド'),
                'issuing_org': ('organization_name', 'テキストフィールド'),
                'description': ('project_description', 'テキストフィールド'),
                'region': ('prefecture_name', 'lg_codeから導出'),
                'deadline': ('cft_issue_date', 'tender_submission_deadline', '日付フィールド'),
                'url': ('external_document_uri', 'テキストフィールド'),
                'external_doc_urls': ('attachments[].uri', '配列フィールド'),
                'budget': ('予算情報', 'API未提供'),
            }
            
            print(f"{'DBカラム':30s} | {'KKJ APIフィールド':40s} | {'備考'}")
            print("-" * 120)
            for db_col, info in mapping.items():
                api_field = info[0] if isinstance(info, tuple) else info
                note = info[-1] if len(info) > 1 else ""
                print(f"{db_col:30s} | {api_field:40s} | {note}")
            
            print("\n[6] 潜在的な課題\n")
            
            # 実データから課題を検出
            issues = []
            
            # external_id の確認
            if 'key' in field_stats and field_stats['key']['non_empty'] < len(rfps):
                issues.append({
                    'level': 'クリティカル',
                    'field': 'external_id (key)',
                    'issue': f"キーフィールドが空のレコードが存在（{len(rfps) - field_stats['key']['non_empty']}件）",
                    'impact': 'external_id必須制約に違反'
                })
            
            # budgetの確認
            if 'budget' not in [key for key in field_stats.keys()]:
                issues.append({
                    'level': '高優先度',
                    'field': 'budget',
                    'issue': 'APIレスポンスに予算情報フィールドが存在しない',
                    'impact': 'すべてのレコードでbudgetがNULLになる'
                })
            
            # deadlineの確認
            if 'cft_issue_date' in field_stats and field_stats['cft_issue_date']['non_empty'] < len(rfps):
                issues.append({
                    'level': 'クリティカル',
                    'field': 'deadline (cft_issue_date)',
                    'issue': f"締切日が空のレコードが存在（{len(rfps) - field_stats['cft_issue_date']['non_empty']}件）",
                    'impact': 'deadline必須制約に違反'
                })
            
            # 地域情報の確認
            if 'lg_code' in field_stats and field_stats['lg_code']['non_empty'] < len(rfps):
                issues.append({
                    'level': 'クリティカル',
                    'field': 'region (lg_code)',
                    'issue': f"都道府県コードが空のレコードが存在（{len(rfps) - field_stats['lg_code']['non_empty']}件）",
                    'impact': 'region必須制約に違反'
                })
            
            # descriptionの確認
            if 'project_description' in field_stats and field_stats['project_description']['non_empty'] < len(rfps):
                issues.append({
                    'level': '中優先度',
                    'field': 'description (project_description)',
                    'issue': f"プロジェクト説明が空のレコードが存在（{len(rfps) - field_stats['project_description']['non_empty']}件）",
                    'impact': 'description必須制約に違反'
                })
            
            if not issues:
                print("  検出された主要な課題はありません（サンプルデータ内）")
            else:
                print(f"{'優先度':15s} | {'フィールド':30s} | {'課題':50s} | {'影響'}")
                print("-" * 130)
                for issue in issues:
                    print(f"{issue['level']:15s} | {issue['field']:30s} | {issue['issue']:50s} | {issue['impact']}")
            
            print("\n" + "=" * 80)
            print("分析完了")
            print("=" * 80)
            
            return rfps
        else:
            print("  データが取得できませんでした")
            return None
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    rfps = analyze_kkj_data()
    if rfps:
        sys.exit(0)
    else:
        sys.exit(1)

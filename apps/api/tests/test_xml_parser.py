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

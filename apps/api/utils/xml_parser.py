"""
KKJ API XMLパーサー

KKJ APIのXMLレスポンスから添付ファイルURLを抽出します。
"""

import xml.etree.ElementTree as ET
from typing import List


def extract_attachment_urls(xml_content: str) -> List[str]:
    """
    KKJ API XMLレスポンスから添付ファイルのURLを全て抽出します。

    XMLドキュメント内のAttachment要素を検索し、その中のURL要素のテキストを
    リストとして返します。XMLパースに失敗した場合は空リストを返します。

    Args:
        xml_content: KKJ APIから返されたXML文字列

    Returns:
        添付ファイルURLのリスト（見つからない場合は空リスト）

    Examples:
        >>> xml = '''
        ... <Document>
        ...   <Attachment>
        ...     <URL>https://example.com/file1.pdf</URL>
        ...   </Attachment>
        ...   <Attachment>
        ...     <URL>https://example.com/file2.pdf</URL>
        ...   </Attachment>
        ... </Document>
        ... '''
        >>> extract_attachment_urls(xml)
        ['https://example.com/file1.pdf', 'https://example.com/file2.pdf']

        >>> extract_attachment_urls("<Document></Document>")
        []

        >>> extract_attachment_urls("invalid xml")
        []

        >>> xml_with_multiple = '''
        ... <Root>
        ...   <Attachment>
        ...     <URL>https://example.com/doc1.docx</URL>
        ...     <Name>Document 1</Name>
        ...   </Attachment>
        ...   <Attachment>
        ...     <URL>https://example.com/doc2.xlsx</URL>
        ...     <Name>Document 2</Name>
        ...   </Attachment>
        ...   <OtherElement>
        ...     <URL>https://example.com/ignored.txt</URL>
        ...   </OtherElement>
        ... </Root>
        ... '''
        >>> extract_attachment_urls(xml_with_multiple)
        ['https://example.com/doc1.docx', 'https://example.com/doc2.xlsx']
    """
    try:
        # XML文字列をパース
        root = ET.fromstring(xml_content)

        # 全てのAttachment要素を検索
        urls: List[str] = []
        for attachment in root.iter("Attachment"):
            # Attachment要素内のURL要素を検索
            url_element = attachment.find("URL")
            if url_element is not None and url_element.text:
                urls.append(url_element.text.strip())

        return urls

    except ET.ParseError:
        # XMLパースエラーの場合は空リストを返す
        return []

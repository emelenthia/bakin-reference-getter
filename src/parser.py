"""
HTMLパースとデータ抽出モジュール
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

try:
    from src.signature_parser import SignatureParser
except ModuleNotFoundError:
    from signature_parser import SignatureParser

logger = logging.getLogger(__name__)


@dataclass
class ClassInfo:
    """クラス情報データクラス"""
    name: str              # 表示名（例: "Cast"）
    full_name: str         # 完全修飾名（例: "Yukar.Common.Rom.Cast"）
    url: str               # ドキュメントURL
    type: str              # 'class', 'interface', 'struct', 'enum'
    namespace: str         # 名前空間（例: "Yukar.Common.Rom"）
    description: str = ""  # 簡単な説明


@dataclass
class ClassDetail:
    """クラス詳細情報データクラス"""
    info: ClassInfo
    description_full: str = ""
    inherits_from: List[str] = None
    methods: List[Dict] = None
    properties: List[Dict] = None
    fields: List[Dict] = None

    def __post_init__(self):
        if self.inherits_from is None:
            self.inherits_from = []
        if self.methods is None:
            self.methods = []
        if self.properties is None:
            self.properties = []
        if self.fields is None:
            self.fields = []


class BakinParser:
    """Bakinドキュメント用HTMLパーサー"""

    def parse_annotated_page(self, soup: BeautifulSoup) -> List[ClassInfo]:
        """
        annotated.htmlから全クラスリストを抽出

        Args:
            soup: annotated.htmlのBeautifulSoup

        Returns:
            ClassInfoオブジェクトのリスト
        """
        classes = []

        # Doxygenのクラスリストは通常 <div class="directory"> 内にある
        directory_div = soup.find('div', class_='directory')
        if not directory_div:
            logger.warning("Could not find directory div in annotated page")
            return classes

        # すべてのリンクを探す
        for link in directory_div.find_all('a', href=True):
            href = link['href']

            # クラス/インターフェース/構造体のページのみ対象
            # Doxygenは class_, interface_, struct_ などで始まる
            if not any(href.startswith(prefix) for prefix in ['class_', 'struct_', 'interface_']):
                continue

            # テキストからクラス名を取得
            class_name = link.get_text(strip=True)

            # URLから完全修飾名を復元
            # Doxygenのエンコーディング: class_sharp_kmy_audio_1_1_sound.html
            # → SharpKmyAudio.Sound
            url_without_ext = href.replace('.html', '')

            # プレフィックスを除去（class_, struct_, interface_）
            for prefix in ['class_', 'struct_', 'interface_']:
                if url_without_ext.startswith(prefix):
                    url_without_ext = url_without_ext[len(prefix):]
                    break

            # _1_1 を . に変換
            full_name_from_url = url_without_ext.replace('_1_1', '.')

            # アンダースコアで始まる部分を大文字に変換（キャメルケースに戻す）
            # 例: sharp_kmy_audio → SharpKmyAudio
            parts = full_name_from_url.split('.')
            converted_parts = []
            for part in parts:
                # 各パートのアンダースコアを処理
                words = part.split('_')
                # 各単語の最初を大文字に
                camel_case = ''.join(word.capitalize() for word in words if word)
                converted_parts.append(camel_case)

            full_name = '.'.join(converted_parts)

            # 名前空間とクラス名を分離
            if '.' in full_name:
                namespace_parts = full_name.split('.')
                class_name = namespace_parts[-1]
                namespace = '.'.join(namespace_parts[:-1])
            else:
                namespace = ""

            # 型を推定（URLから）
            if href.startswith('class_'):
                class_type = 'class'
            elif href.startswith('struct_'):
                class_type = 'struct'
            elif href.startswith('interface_'):
                class_type = 'interface'
            else:
                class_type = 'unknown'

            # 説明を取得（あれば）
            description = ""
            # Doxygenは通常、リンクの後に説明が続く
            parent = link.parent
            if parent and parent.name == 'td':
                desc_td = parent.find_next_sibling('td')
                if desc_td:
                    description = desc_td.get_text(strip=True)

            class_info = ClassInfo(
                name=class_name,
                full_name=full_name,
                url=href,
                type=class_type,
                namespace=namespace,
                description=description
            )
            classes.append(class_info)
            logger.debug(f"Found {class_type}: {full_name}")

        logger.info(f"Extracted {len(classes)} classes from annotated page")
        return classes

    def parse_class_page(self, soup: BeautifulSoup, class_info: ClassInfo) -> ClassDetail:
        """
        個別クラスページから詳細情報を抽出

        Args:
            soup: クラスページのBeautifulSoup
            class_info: 基本クラス情報

        Returns:
            ClassDetailオブジェクト
        """
        detail = ClassDetail(info=class_info)

        # クラスの詳細説明を取得
        detail.description_full = self._extract_description(soup)

        # 継承関係を取得
        detail.inherits_from = self._extract_inheritance(soup)

        # メソッドを取得
        detail.methods = self._extract_methods(soup)

        # プロパティを取得
        detail.properties = self._extract_properties(soup)

        # フィールドを取得
        detail.fields = self._extract_fields(soup)

        return detail

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """クラスの説明を抽出"""
        # Doxygenの詳細説明は通常 <div class="textblock"> にある
        textblock = soup.find('div', class_='textblock')
        if textblock:
            return textblock.get_text(strip=True)
        return ""

    def _extract_inheritance(self, soup: BeautifulSoup) -> List[str]:
        """継承関係を抽出"""
        inherits = []

        # 継承図から抽出
        # Doxygenは <div class="inherit"> や継承リストを持つ
        inherit_list = soup.find('div', class_='inherit_header')
        if inherit_list:
            # 継承リストの処理
            for link in inherit_list.find_all('a'):
                inherits.append(link.get_text(strip=True))

        # 別の方法: "Inheritance diagram" セクションから
        inheritance_heading = soup.find('h2', string=re.compile('継承図|Inheritance'))
        if inheritance_heading:
            # 次の要素から継承情報を探す
            next_elem = inheritance_heading.find_next_sibling()
            if next_elem:
                for link in next_elem.find_all('a', class_='el'):
                    parent = link.get_text(strip=True)
                    if parent != soup.title.get_text(strip=True):  # 自分自身は除外
                        inherits.append(parent)

        return inherits

    def _extract_methods(self, soup: BeautifulSoup) -> List[Dict]:
        """メソッドを抽出"""
        methods = []

        # Doxygenのメソッドセクションを探す
        # id="pub-methods"（公開メンバ関数）と id="pub-static-methods"（静的公開メンバ関数）
        for section_id in ['pub-methods', 'pub-static-methods']:
            section_anchor = soup.find('a', {'id': section_id})
            if not section_anchor:
                continue

            # セクションヘッダーの親要素（<h2>）を取得
            section_heading = section_anchor.find_parent('h2')
            if not section_heading:
                continue

            # <h2>の親の<table>を取得（<h2>は<table>の中にある）
            table = section_heading.find_parent('table', class_='memberdecls')
            if not table:
                continue

            # 静的メソッドかどうかのフラグ
            is_static = (section_id == 'pub-static-methods')

            for row in table.find_all('tr', class_=re.compile(r'^memitem:')):
                method = self._parse_method_row(row, soup, is_static)
                if method:
                    methods.append(method)

        return methods

    def _parse_method_row(self, row: Tag, soup: BeautifulSoup, is_static: bool = False) -> Optional[Dict]:
        """メソッド行をパース"""
        method = {}

        # 戻り値の型
        return_type_cell = row.find('td', class_='memItemLeft')
        if return_type_cell:
            return_type = return_type_cell.get_text(strip=True)
            # 静的メソッドの場合、HTMLには既に'static'が含まれているので削除
            if is_static and return_type.startswith('static'):
                # 'static'とその後のスペースを削除（スペースが無い場合もあるので両方対応）
                return_type = return_type[6:].strip()  # 'static' は6文字
            method['return_type'] = return_type

        # メソッドシグネチャ
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        # メソッド全体のシグネチャを取得（タグ間にスペースを入れる）
        raw_signature = name_cell.get_text(separator=' ', strip=True)
        # 余分なスペースを削除
        raw_signature = ' '.join(raw_signature.split())
        method['signature'] = SignatureParser.format_signature(raw_signature)

        # メソッド名を抽出（リンク部分）
        method_link = name_cell.find('a', class_='el')
        if method_link:
            method['name'] = method_link.get_text(strip=True)
            # アンカーIDを取得（詳細説明へのリンク用）
            href = method_link.get('href', '')
            if href and '#' in href:
                method['anchor_id'] = href.split('#')[1]

        # 静的メソッドかどうか
        method['is_static'] = is_static

        # 詳細説明（アンカーから辿る）
        if 'anchor_id' in method:
            detail_section = soup.find('a', {'id': method['anchor_id']})
            if detail_section:
                # 詳細説明を探す
                desc_div = detail_section.find_next('div', class_='memdoc')
                if desc_div:
                    # テキストブロックを抽出
                    textblocks = desc_div.find_all('p')
                    if textblocks:
                        method['description'] = ' '.join(p.get_text(strip=True) for p in textblocks)

        return method

    def _extract_properties(self, soup: BeautifulSoup) -> List[Dict]:
        """プロパティを抽出"""
        properties = []

        # Doxygenではプロパティは「プロパティ」セクションにある
        # id="properties" または "pub-properties" などを探す
        for section_id in ['properties', 'pub-properties', 'pub-static-properties']:
            section_anchor = soup.find('a', {'id': section_id})
            if not section_anchor:
                continue

            # セクションヘッダーの親要素（<h2>）を取得
            section_heading = section_anchor.find_parent('h2')
            if not section_heading:
                continue

            # <h2>の親の<table>を取得（<h2>は<table>の中にある）
            table = section_heading.find_parent('table', class_='memberdecls')
            if not table:
                continue

            is_static = ('static' in section_id)

            for row in table.find_all('tr', class_=re.compile(r'^memitem:')):
                prop = self._parse_property_row(row, is_static)
                if prop:
                    properties.append(prop)

        return properties

    def _parse_property_row(self, row: Tag, is_static: bool = False) -> Optional[Dict]:
        """プロパティ行をパース"""
        prop = {}

        # 型
        type_cell = row.find('td', class_='memItemLeft')
        if type_cell:
            prop_type = type_cell.get_text(strip=True)
            # 静的プロパティの場合、HTMLには既に'static'が含まれているので削除
            if is_static and prop_type.startswith('static'):
                prop_type = prop_type[6:].strip()  # 'static' は6文字
            prop['type'] = prop_type

        # プロパティ名
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        # プロパティ宣言を取得（タグ間にスペースを入れる）
        prop_text = name_cell.get_text(separator=' ', strip=True)
        # 余分なスペースを削除
        prop_text = ' '.join(prop_text.split())
        prop['declaration'] = prop_text

        # プロパティ名を抽出（リンク部分）
        prop_link = name_cell.find('a', class_='el')
        if prop_link:
            prop['name'] = prop_link.get_text(strip=True)
        else:
            # リンクがない場合は全体のテキストから抽出
            # [get, set]などのアクセサが含まれる場合はそれを除外
            if '[' in prop_text:
                prop['name'] = prop_text[:prop_text.find('[')].strip()
            else:
                prop['name'] = prop_text

        # 静的プロパティかどうか
        prop['is_static'] = is_static

        # get/setの確認
        if '[get' in prop_text or '[set' in prop_text:
            start = prop_text.find('[')
            end = prop_text.find(']', start) + 1
            if end > start:
                prop['accessors'] = prop_text[start:end]

        return prop

    def _extract_fields(self, soup: BeautifulSoup) -> List[Dict]:
        """フィールド（公開変数）を抽出"""
        fields = []

        # 公開変数セクションを探す（id="pub-attribs"）
        section_anchor = soup.find('a', {'id': 'pub-attribs'})
        if not section_anchor:
            return fields

        # セクションヘッダーの親要素（<h2>）を取得
        section_heading = section_anchor.find_parent('h2')
        if not section_heading:
            return fields

        # <h2>の親の<table>を取得（<h2>は<table>の中にある）
        table = section_heading.find_parent('table', class_='memberdecls')
        if not table:
            return fields

        for row in table.find_all('tr', class_=re.compile(r'^memitem:')):
            field = self._parse_field_row(row)
            if field:
                fields.append(field)

        return fields

    def _parse_field_row(self, row: Tag) -> Optional[Dict]:
        """フィールド行をパース"""
        field = {}

        # 型
        type_cell = row.find('td', class_='memItemLeft')
        if type_cell:
            field['type'] = type_cell.get_text(strip=True)

        # フィールド名と初期値
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        # フィールド全体の宣言を保存（タグ間にスペースを入れる）
        declaration = name_cell.get_text(separator=' ', strip=True)
        # 余分なスペースを削除
        field['declaration'] = ' '.join(declaration.split())

        # フィールド名を抽出（リンク部分）
        field_link = name_cell.find('a', class_='el')
        if field_link:
            field['name'] = field_link.get_text(strip=True)
        else:
            # リンクがない場合は全体のテキストから抽出
            # 初期値がある場合は = の前まで
            full_text = name_cell.get_text(strip=True)
            if '=' in full_text:
                field['name'] = full_text.split('=')[0].strip()
            else:
                field['name'] = full_text

        return field

"""
HTMLパースとデータ抽出モジュール
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

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
        # 通常は <h2>Public メンバ関数</h2> などのセクション
        method_section = soup.find('h2', string=re.compile('メンバ関数|Member Functions'))
        if not method_section:
            return methods

        # メソッドテーブルを探す
        table = method_section.find_next('table', class_='memberdecls')
        if not table:
            return methods

        for row in table.find_all('tr', class_='memitem'):
            method = self._parse_method_row(row, soup)
            if method:
                methods.append(method)

        return methods

    def _parse_method_row(self, row: Tag, soup: BeautifulSoup) -> Optional[Dict]:
        """メソッド行をパース"""
        method = {}

        # メソッド名
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        method_link = name_cell.find('a')
        if method_link:
            method['name'] = method_link.get_text(strip=True)
            method['anchor'] = method_link.get('href', '')

        # 戻り値の型
        return_type_cell = row.find('td', class_='memItemLeft')
        if return_type_cell:
            method['return_type'] = return_type_cell.get_text(strip=True)

        # 詳細説明（アンカーから辿る）
        if 'anchor' in method:
            detail_section = soup.find('a', {'id': method['anchor'].replace('#', '')})
            if detail_section:
                # 詳細説明を探す
                desc_div = detail_section.find_next('div', class_='memitemdoc')
                if desc_div:
                    method['description'] = desc_div.get_text(strip=True)

        # 継承元の確認（行に「継承」や「inherited」が含まれるか）
        inherited_from = row.find('td', class_='inherit')
        if inherited_from:
            method['inherited_from'] = inherited_from.get_text(strip=True)

        return method

    def _extract_properties(self, soup: BeautifulSoup) -> List[Dict]:
        """プロパティを抽出"""
        properties = []

        # Doxygenではプロパティは「プロパティ」セクションにある
        prop_section = soup.find('h2', string=re.compile('プロパティ|Properties'))
        if not prop_section:
            return properties

        table = prop_section.find_next('table', class_='memberdecls')
        if not table:
            return properties

        for row in table.find_all('tr', class_='memitem'):
            prop = self._parse_property_row(row)
            if prop:
                properties.append(prop)

        return properties

    def _parse_property_row(self, row: Tag) -> Optional[Dict]:
        """プロパティ行をパース"""
        prop = {}

        # プロパティ名
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        prop_text = name_cell.get_text(strip=True)
        prop['name'] = prop_text

        # 型
        type_cell = row.find('td', class_='memItemLeft')
        if type_cell:
            prop['type'] = type_cell.get_text(strip=True)

        # get/setの確認
        if '[get' in prop_text or '[set' in prop_text:
            prop['accessors'] = prop_text[prop_text.find('['):prop_text.find(']')+1]

        # 継承元
        inherited_from = row.find('td', class_='inherit')
        if inherited_from:
            prop['inherited_from'] = inherited_from.get_text(strip=True)

        return prop

    def _extract_fields(self, soup: BeautifulSoup) -> List[Dict]:
        """フィールド（公開変数）を抽出"""
        fields = []

        # 公開変数セクションを探す
        field_section = soup.find('h2', string=re.compile('公開変数|Public Attributes'))
        if not field_section:
            return fields

        table = field_section.find_next('table', class_='memberdecls')
        if not table:
            return fields

        for row in table.find_all('tr', class_='memitem'):
            field = self._parse_field_row(row)
            if field:
                fields.append(field)

        return fields

    def _parse_field_row(self, row: Tag) -> Optional[Dict]:
        """フィールド行をパース"""
        field = {}

        # フィールド名
        name_cell = row.find('td', class_='memItemRight')
        if not name_cell:
            return None

        field['name'] = name_cell.get_text(strip=True)

        # 型
        type_cell = row.find('td', class_='memItemLeft')
        if type_cell:
            field['type'] = type_cell.get_text(strip=True)

        # 継承元
        inherited_from = row.find('td', class_='inherit')
        if inherited_from:
            field['inherited_from'] = inherited_from.get_text(strip=True)

        return field


if __name__ == '__main__':
    # テスト実行
    from scraper import BakinScraper

    print("Testing BakinParser...")
    scraper = BakinScraper()
    parser = BakinParser()

    print("Fetching annotated page...")
    soup = scraper.fetch_annotated_page()

    print("Parsing classes...")
    classes = parser.parse_annotated_page(soup)

    print(f"OK: Found {len(classes)} classes")
    print(f"Sample: {classes[0].full_name} (namespace: {classes[0].namespace})")
    print("Parser test passed!")

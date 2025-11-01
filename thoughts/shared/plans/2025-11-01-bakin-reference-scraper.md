# RPG Developer Bakin ドキュメントスクレイパー実装計画

## 概要

RPG Developer BakinのC#リファレンスドキュメント（https://rpgbakin.com/csreference/doc/ja/）を全自動でスクレイピングし、AIが参照しやすいMarkdown形式でローカルに保存するPythonツールを実装します。

## 現状分析

### 対象ドキュメントの特徴
- **形式**: Doxygen 1.9.4で生成されたHTML形式のC#リファレンス
- **構造**:
  - `annotated.html`: 全クラス/構造体/インターフェースの一覧（階層構造）
  - `class_[namespace]_1_1_[class].html`: 個別クラスの詳細ページ
  - `namespace_[namespace]_1_1_[name].html`: 名前空間ごとのまとめページ
- **主要名前空間**:
  - `Yukar.Common.Rom`: ゲームデータベース要素（150以上のクラス）
  - `SharpKmy*`: オーディオ、グラフィックス、ベース機能
  - `kmyPhysics`: 物理エンジン関連
- **言語**: 日本語

### 課題
- Web上にあるためAIが直接参照しにくい
- HTML形式でありコンテキスト理解に適さない
- 大量のクラス（推定200以上）を手動で処理するのは非現実的

## 目標とする最終状態

### 出力ディレクトリ構造
```
bakin-reference-getter/
├── src/
│   ├── __init__.py
│   ├── scraper.py              # HTMLスクレイピングロジック
│   ├── parser.py               # HTML→データ構造変換
│   ├── markdown_generator.py   # データ→Markdown変換
│   ├── progress_manager.py     # 進捗管理（CSV操作）
│   └── cli.py                  # コマンドラインインターフェース
├── output/
│   ├── progress.csv            # 進捗管理ファイル（自動生成）
│   ├── index.md                # 全体の索引（自動生成）
│   ├── namespaces/
│   │   ├── Yukar.Common.Rom.md
│   │   ├── SharpKmyAudio.md
│   │   └── ...
│   └── classes/
│       ├── Yukar.Common.Rom.Cast.md
│       ├── Yukar.Common.Rom.Monster.md
│       └── ...
├── requirements.txt            # 依存ライブラリ
├── config.yaml                 # 設定ファイル
├── main.py                     # エントリーポイント
└── README.md                   # 使い方説明
```

### 成功基準
- 全クラスのドキュメントがMarkdown形式で保存されている
- 各Markdownファイルに以下の情報が含まれる:
  - クラス名と完全修飾名
  - クラスの説明（日本語）
  - 継承関係（親クラス、継承元の明記）
  - すべてのパブリックメソッド（シグネチャ、パラメータ、戻り値、説明）
  - すべてのパブリックプロパティ（型、get/set、説明）
  - パブリック変数
  - 継承されたメンバーには継承元クラスを明記
- **継続モード機能**:
  - progress.csvで進捗を管理できる
  - `--limit N` で指定件数だけ処理できる
  - 中断後も続きから再開できる
  - 進捗状況を確認できる
- CLIで一括取得と個別取得の両方が可能
- エラーハンドリングとリトライ機構が実装されている

## スコープ外の項目

以下は今回の実装に含めません：
- ドキュメントの定期的な自動更新機能
- 差分検出と増分更新
- ドキュメントのバージョン管理
- 検索機能の実装
- WebUIの提供
- 英語版ドキュメントの取得（日本語版のみ）
- ファイル一覧ページ（files.html）のスクレイピング
- ソースコード例の実行可能性チェック

## 実装アプローチ

### 技術スタック
- **Python 3.10+**: メイン言語
- **requests**: HTTPリクエスト
- **BeautifulSoup4**: HTMLパース
- **PyYAML**: 設定ファイル読み込み
- **click**: CLIフレームワーク
- **tqdm**: 進捗バー表示
- **tenacity**: リトライ機構

### 処理フロー（継続モード）
```
1. progress.csvが存在するかチェック
2. 存在しない場合:
   a. annotated.htmlを取得
   b. 全クラスURLリストを抽出
   c. progress.csvを作成（全てcompleted=False）
3. progress.csvから未完了のクラスを取得
4. 指定された件数（--limit N）または全件を処理:
   a. クラスHTMLを取得
   b. クラス情報をパース
   c. Markdown生成
   d. ファイル保存
   e. progress.csvの該当行をcompleted=Trueに更新
5. 全て完了したら索引ファイルを生成
```

---

## フェーズ1: プロジェクト基盤のセットアップ

### 概要
Pythonプロジェクトの基本構造を作成し、依存関係を定義します。

### 変更内容

#### 1. プロジェクト構造の作成
**作成するディレクトリ・ファイル**:
```bash
mkdir -p src output/classes output/namespaces
touch src/__init__.py src/scraper.py src/parser.py src/markdown_generator.py src/progress_manager.py src/cli.py main.py
```

#### 2. requirements.txt
**ファイル**: `requirements.txt`
```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
PyYAML>=6.0
click>=8.1.0
tqdm>=4.66.0
tenacity>=8.2.0
```

#### 3. config.yaml
**ファイル**: `config.yaml`
```yaml
# RPG Developer Bakin ドキュメントスクレイパー設定

# ベースURL
base_url: "https://rpgbakin.com/csreference/doc/ja"

# スクレイピング設定
scraping:
  # リクエスト間のディレイ（秒）
  delay: 1.0
  # タイムアウト（秒）
  timeout: 30
  # リトライ回数
  max_retries: 3
  # User-Agent
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 出力設定
output:
  # 出力ディレクトリ
  base_dir: "./output"
  classes_dir: "./output/classes"
  namespaces_dir: "./output/namespaces"
  # クラスリストキャッシュ
  class_list_cache: "./output/class_list.json"
  # 進捗管理CSV
  progress_file: "./output/progress.csv"

# ページ設定
pages:
  # クラス一覧ページ
  annotated: "annotated.html"
  # 名前空間一覧ページ
  namespaces: "namespaces.html"
```

#### 4. README.md（基本版）
**ファイル**: `README.md`
```markdown
# RPG Developer Bakin ドキュメントスクレイパー

RPG Developer BakinのC#リファレンスドキュメントをスクレイピングし、AI参照用のMarkdown形式で保存するツールです。

## インストール

\```bash
pip install -r requirements.txt
\```

## 使用方法

### 継続モードで少しずつスクレイピング（推奨）
\```bash
# 最初の10件を取得
python main.py scrape --limit 10

# さらに10件を取得（続きから）
python main.py scrape --limit 10

# 残り全てを取得
python main.py scrape
\```

### 全クラスを一括取得（従来の方法）
\```bash
python main.py scrape-all
\```

### 特定のクラスのみ取得
\```bash
python main.py scrape-class "Yukar.Common.Rom.Cast"
\```

### 進捗状況の確認
\```bash
python main.py status
\```

### クラスリストのみ取得
\```bash
python main.py list-classes
\```

## 出力形式

- `output/classes/`: 各クラスのMarkdownファイル
- `output/namespaces/`: 名前空間ごとのまとめ
- `output/index.md`: 全体の索引

## 設定

`config.yaml`でスクレイピングの挙動をカスタマイズできます。
```

### 成功基準

#### 自動検証:
- [x] プロジェクト構造が作成されている: `ls -la src/ output/`
- [x] requirements.txtが存在し、正しい形式である: `cat requirements.txt`
- [x] config.yamlが存在し、YAMLとして有効である: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`

#### 手動検証:
- [ ] ディレクトリ構造が計画通りに作成されている
- [ ] 全ての必要なファイルが存在する

---

## フェーズ2: HTMLスクレイパー基盤の実装

### 概要
HTTPリクエストとHTML取得の基本機能、リトライ機構、設定読み込みを実装します。

### 変更内容

#### 1. src/scraper.py
**ファイル**: `src/scraper.py`
```python
"""
HTMLスクレイピング基盤モジュール
"""
import time
import logging
from typing import Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import yaml

logger = logging.getLogger(__name__)


class BakinScraper:
    """RPG Developer Bakinドキュメントスクレイパー"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.base_url = self.config['base_url']
        self.delay = self.config['scraping']['delay']
        self.timeout = self.config['scraping']['timeout']
        self.headers = {
            'User-Agent': self.config['scraping']['user_agent']
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        指定されたURLからHTMLを取得してBeautifulSoupオブジェクトを返す

        Args:
            url: 取得するURL（相対パスまたは絶対パス）

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        # 相対パスの場合はベースURLと結合
        if not url.startswith('http'):
            url = f"{self.base_url}/{url}"

        logger.info(f"Fetching: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # ディレイを入れる（サーバーに負荷をかけないため）
            time.sleep(self.delay)

            soup = BeautifulSoup(response.content, 'lxml')
            return soup

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def fetch_annotated_page(self) -> Optional[BeautifulSoup]:
        """クラス一覧ページ（annotated.html）を取得"""
        return self.fetch_page(self.config['pages']['annotated'])

    def fetch_class_page(self, class_url: str) -> Optional[BeautifulSoup]:
        """
        個別クラスページを取得

        Args:
            class_url: クラスページのURL（例: "class_yukar_1_1_common_1_1_rom_1_1_cast.html"）
        """
        return self.fetch_page(class_url)
```

#### 2. ロギング設定
**ファイル**: `src/__init__.py`
```python
"""
Bakinドキュメントスクレイパーパッケージ
"""
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 成功基準

#### 自動検証:
- [ ] Pythonファイルが構文エラーなくインポートできる: `python -c "from src.scraper import BakinScraper"`
- [ ] 設定ファイルが正しく読み込める: `python -c "from src.scraper import BakinScraper; s = BakinScraper(); print(s.base_url)"`
- [ ] annotated.htmlが取得できる: `python -c "from src.scraper import BakinScraper; s = BakinScraper(); soup = s.fetch_annotated_page(); print(soup.title.text if soup else 'Failed')"`

#### 手動検証:
- [ ] ネットワークエラー時に適切にリトライが行われる
- [ ] ログが正しく出力される

---

## フェーズ3: クラスリスト抽出パーサーの実装

### 概要
annotated.htmlから全クラス/インターフェース/構造体のリストとURLを抽出します。

### 変更内容

#### 1. src/parser.py
**ファイル**: `src/parser.py`
```python
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
            name = link.get_text(strip=True)

            # 名前空間とクラス名を分離
            # Doxygen形式: "Yukar.Common.Rom.Cast" のような形式
            full_name = name
            namespace = ""
            class_name = name

            if '.' in name:
                parts = name.split('.')
                class_name = parts[-1]
                namespace = '.'.join(parts[:-1])

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
```

### 成功基準

#### 自動検証:
- [ ] パーサーモジュールがインポートできる: `python -c "from src.parser import BakinParser, ClassInfo"`
- [ ] annotated.htmlからクラスリストが抽出できる:
```python
from src.scraper import BakinScraper
from src.parser import BakinParser

scraper = BakinScraper()
parser = BakinParser()
soup = scraper.fetch_annotated_page()
classes = parser.parse_annotated_page(soup)
print(f"Found {len(classes)} classes")
assert len(classes) > 100  # 少なくとも100クラス以上あるはず
```

#### 手動検証:
- [ ] 抽出されたクラスリストに主要な名前空間（Yukar, SharpKmy）が含まれる
- [ ] 各ClassInfoオブジェクトが正しい情報を持っている

---

## フェーズ4: Markdown生成機能の実装

### 概要
抽出したクラス情報をAI参照用のMarkdown形式に変換します。

### 変更内容

#### 1. src/markdown_generator.py
**ファイル**: `src/markdown_generator.py`
```python
"""
Markdown生成モジュール
"""
import logging
from typing import List
from pathlib import Path

from src.parser import ClassInfo, ClassDetail

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """クラス情報をMarkdownに変換"""

    def generate_class_markdown(self, detail: ClassDetail) -> str:
        """
        クラス詳細情報からMarkdownを生成

        Args:
            detail: ClassDetailオブジェクト

        Returns:
            Markdownテキスト
        """
        lines = []

        # ヘッダー
        lines.append(f"# {detail.info.full_name}")
        lines.append("")

        # メタ情報
        lines.append("## メタ情報")
        lines.append("")
        lines.append(f"- **型**: {detail.info.type}")
        lines.append(f"- **名前空間**: {detail.info.namespace}")
        lines.append(f"- **完全修飾名**: {detail.info.full_name}")
        if detail.info.url:
            lines.append(f"- **ドキュメントURL**: https://rpgbakin.com/csreference/doc/ja/{detail.info.url}")
        lines.append("")

        # 説明
        if detail.description_full:
            lines.append("## 説明")
            lines.append("")
            lines.append(detail.description_full)
            lines.append("")

        # 継承関係
        if detail.inherits_from:
            lines.append("## 継承関係")
            lines.append("")
            lines.append("このクラスは以下のクラスを継承しています：")
            lines.append("")
            for parent in detail.inherits_from:
                lines.append(f"- `{parent}`")
            lines.append("")

        # プロパティ
        if detail.properties:
            lines.append("## プロパティ")
            lines.append("")

            # 継承プロパティと独自プロパティを分離
            own_props = [p for p in detail.properties if 'inherited_from' not in p]
            inherited_props = [p for p in detail.properties if 'inherited_from' in p]

            if own_props:
                for prop in own_props:
                    lines.append(f"### {prop['name']}")
                    lines.append("")
                    lines.append(f"- **型**: `{prop.get('type', 'unknown')}`")
                    if 'accessors' in prop:
                        lines.append(f"- **アクセサ**: {prop['accessors']}")
                    if 'description' in prop:
                        lines.append(f"- **説明**: {prop['description']}")
                    lines.append("")

            if inherited_props:
                lines.append("### 継承されたプロパティ")
                lines.append("")
                for prop in inherited_props:
                    lines.append(f"- `{prop['name']}` (継承元: `{prop['inherited_from']}`)")
                lines.append("")

        # メソッド
        if detail.methods:
            lines.append("## メソッド")
            lines.append("")

            # 継承メソッドと独自メソッドを分離
            own_methods = [m for m in detail.methods if 'inherited_from' not in m]
            inherited_methods = [m for m in detail.methods if 'inherited_from' in m]

            if own_methods:
                for method in own_methods:
                    lines.append(f"### {method['name']}")
                    lines.append("")
                    if 'return_type' in method:
                        lines.append(f"**戻り値**: `{method['return_type']}`")
                        lines.append("")
                    if 'description' in method:
                        lines.append(method['description'])
                        lines.append("")
                    lines.append("---")
                    lines.append("")

            if inherited_methods:
                lines.append("### 継承されたメソッド")
                lines.append("")
                for method in inherited_methods:
                    lines.append(f"- `{method['name']}` (継承元: `{method['inherited_from']}`)")
                lines.append("")

        # フィールド
        if detail.fields:
            lines.append("## 公開フィールド")
            lines.append("")

            own_fields = [f for f in detail.fields if 'inherited_from' not in f]
            inherited_fields = [f for f in detail.fields if 'inherited_from' in f]

            if own_fields:
                for field in own_fields:
                    lines.append(f"- `{field.get('type', 'unknown')} {field['name']}`")
                lines.append("")

            if inherited_fields:
                lines.append("### 継承されたフィールド")
                lines.append("")
                for field in inherited_fields:
                    lines.append(f"- `{field['name']}` (継承元: `{field['inherited_from']}`)")
                lines.append("")

        return "\n".join(lines)

    def generate_index_markdown(self, classes: List[ClassInfo]) -> str:
        """
        全体の索引Markdownを生成

        Args:
            classes: ClassInfoオブジェクトのリスト

        Returns:
            索引Markdownテキスト
        """
        lines = []

        lines.append("# RPG Developer Bakin C# リファレンス索引")
        lines.append("")
        lines.append("このドキュメントは自動生成されたものです。")
        lines.append("")

        # 名前空間ごとにグループ化
        namespaces = {}
        for cls in classes:
            ns = cls.namespace or "グローバル"
            if ns not in namespaces:
                namespaces[ns] = []
            namespaces[ns].append(cls)

        # 名前空間ごとに出力
        for ns in sorted(namespaces.keys()):
            lines.append(f"## {ns}")
            lines.append("")

            # 型ごとにさらに分類
            ns_classes = namespaces[ns]
            classes_by_type = {
                'class': [],
                'interface': [],
                'struct': [],
                'enum': []
            }

            for cls in ns_classes:
                if cls.type in classes_by_type:
                    classes_by_type[cls.type].append(cls)

            # クラス
            if classes_by_type['class']:
                lines.append("### クラス")
                lines.append("")
                for cls in sorted(classes_by_type['class'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

            # インターフェース
            if classes_by_type['interface']:
                lines.append("### インターフェース")
                lines.append("")
                for cls in sorted(classes_by_type['interface'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

            # 構造体
            if classes_by_type['struct']:
                lines.append("### 構造体")
                lines.append("")
                for cls in sorted(classes_by_type['struct'], key=lambda x: x.name):
                    desc = f" - {cls.description}" if cls.description else ""
                    lines.append(f"- [{cls.full_name}](classes/{cls.full_name}.md){desc}")
                lines.append("")

        return "\n".join(lines)

    def save_markdown(self, content: str, filepath: Path):
        """
        Markdownファイルを保存

        Args:
            content: Markdownテキスト
            filepath: 保存先パス
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved markdown: {filepath}")
```

### 成功基準

#### 自動検証:
- [ ] Markdown生成モジュールがインポートできる: `python -c "from src.markdown_generator import MarkdownGenerator"`
- [ ] サンプルのClassDetailからMarkdownが生成できる:
```python
from src.parser import ClassInfo, ClassDetail
from src.markdown_generator import MarkdownGenerator

info = ClassInfo(
    name="Cast",
    full_name="Yukar.Common.Rom.Cast",
    url="class_yukar_1_1_common_1_1_rom_1_1_cast.html",
    type="class",
    namespace="Yukar.Common.Rom",
    description="テストクラス"
)
detail = ClassDetail(info=info)
gen = MarkdownGenerator()
md = gen.generate_class_markdown(detail)
print(md)
assert "# Yukar.Common.Rom.Cast" in md
```

#### 手動検証:
- [ ] 生成されたMarkdownが読みやすい
- [ ] 継承情報が正しく表示される
- [ ] セクションが適切に分かれている

---

## フェーズ5: 進捗管理機能の実装

### 概要
CSV形式で進捗を管理し、継続的なスクレイピングをサポートする機能を実装します。

### 変更内容

#### 1. src/progress_manager.py
**ファイル**: `src/progress_manager.py`
```python
"""
進捗管理モジュール - CSV形式で進捗を追跡
"""
import csv
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from src.parser import ClassInfo

logger = logging.getLogger(__name__)


@dataclass
class ProgressEntry:
    """進捗エントリー"""
    full_name: str
    name: str
    url: str
    type: str
    namespace: str
    description: str
    completed: bool
    last_updated: str  # ISO 8601形式


class ProgressManager:
    """進捗管理クラス"""

    CSV_HEADERS = [
        'full_name', 'name', 'url', 'type',
        'namespace', 'description', 'completed', 'last_updated'
    ]

    def __init__(self, progress_file: Path):
        """
        Args:
            progress_file: 進捗CSVファイルのパス
        """
        self.progress_file = progress_file

    def initialize_from_class_list(self, classes: List[ClassInfo]):
        """
        クラスリストから進捗CSVを初期化

        Args:
            classes: ClassInfoのリスト
        """
        logger.info(f"Initializing progress file: {self.progress_file}")

        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()

            for cls in classes:
                entry = ProgressEntry(
                    full_name=cls.full_name,
                    name=cls.name,
                    url=cls.url,
                    type=cls.type,
                    namespace=cls.namespace,
                    description=cls.description,
                    completed=False,
                    last_updated=""
                )
                writer.writerow(asdict(entry))

        logger.info(f"Progress file initialized with {len(classes)} entries")

    def load_progress(self) -> List[ProgressEntry]:
        """
        進捗CSVを読み込み

        Returns:
            ProgressEntryのリスト
        """
        if not self.progress_file.exists():
            return []

        entries = []
        with open(self.progress_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # completedをboolに変換
                row['completed'] = row['completed'].lower() in ('true', '1', 'yes')
                entries.append(ProgressEntry(**row))

        return entries

    def get_pending_entries(self, limit: Optional[int] = None) -> List[ProgressEntry]:
        """
        未完了のエントリーを取得

        Args:
            limit: 取得する最大件数（Noneの場合は全件）

        Returns:
            未完了のProgressEntryのリスト
        """
        all_entries = self.load_progress()
        pending = [e for e in all_entries if not e.completed]

        if limit is not None:
            return pending[:limit]
        return pending

    def mark_completed(self, full_name: str):
        """
        指定されたクラスを完了とマーク

        Args:
            full_name: クラスの完全修飾名
        """
        entries = self.load_progress()

        # 該当エントリーを更新
        updated = False
        for entry in entries:
            if entry.full_name == full_name:
                entry.completed = True
                entry.last_updated = datetime.now().isoformat()
                updated = True
                break

        if not updated:
            logger.warning(f"Entry not found in progress file: {full_name}")
            return

        # CSVを書き直し
        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(asdict(entry))

        logger.debug(f"Marked as completed: {full_name}")

    def get_statistics(self) -> dict:
        """
        進捗統計を取得

        Returns:
            統計情報の辞書
        """
        entries = self.load_progress()
        completed_count = sum(1 for e in entries if e.completed)
        total_count = len(entries)
        pending_count = total_count - completed_count

        return {
            'total': total_count,
            'completed': completed_count,
            'pending': pending_count,
            'progress_percentage': (completed_count / total_count * 100) if total_count > 0 else 0
        }

    def reset_progress(self):
        """全てのエントリーを未完了にリセット"""
        entries = self.load_progress()

        for entry in entries:
            entry.completed = False
            entry.last_updated = ""

        with open(self.progress_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(asdict(entry))

        logger.info("Progress reset: all entries marked as pending")

    def entry_to_class_info(self, entry: ProgressEntry) -> ClassInfo:
        """
        ProgressEntryをClassInfoに変換

        Args:
            entry: ProgressEntry

        Returns:
            ClassInfo
        """
        return ClassInfo(
            name=entry.name,
            full_name=entry.full_name,
            url=entry.url,
            type=entry.type,
            namespace=entry.namespace,
            description=entry.description
        )
```

### 成功基準

#### 自動検証:
- [ ] ProgressManagerがインポートできる: `python -c "from src.progress_manager import ProgressManager"`
- [ ] CSVファイルの初期化ができる
- [ ] 未完了エントリーの取得ができる
- [ ] 完了マークができる

#### 手動検証:
- [ ] progress.csvが正しいフォーマットで作成される
- [ ] Excelなどで開いて確認できる
- [ ] 進捗統計が正しく計算される

---

## フェーズ6: 継続モードCLIの実装

### 概要
進捗管理機能を統合した継続モードのCLIを実装します。

### 変更内容

#### 1. src/cli.pyに継続モード機能を追加

**ファイル**: `src/cli.py`に以下を追加

```python
# インポートに追加
from src.progress_manager import ProgressManager

# BakinDocumentationScraperクラスに追加
class BakinDocumentationScraper:
    def __init__(self, config_path: str = "config.yaml"):
        # ... 既存のコード ...

        # 進捗管理
        self.progress_file = Path(self.config['output']['progress_file'])
        self.progress_manager = ProgressManager(self.progress_file)

    def scrape_with_progress(self, limit: Optional[int] = None, force_init: bool = False):
        """
        進捗管理を使用してスクレイピング（継続モード）

        Args:
            limit: 処理する最大件数（Noneの場合は全未完了分）
            force_init: 進捗ファイルを強制的に再初期化
        """
        # 進捗ファイルの初期化チェック
        if not self.progress_file.exists() or force_init:
            logger.info("Progress file not found. Initializing...")
            classes = self.fetch_class_list()
            self.progress_manager.initialize_from_class_list(classes)

        # 統計表示
        stats = self.progress_manager.get_statistics()
        logger.info(f"Progress: {stats['completed']}/{stats['total']} completed ({stats['progress_percentage']:.1f}%)")
        logger.info(f"Pending: {stats['pending']} classes")

        # 未完了エントリーを取得
        pending_entries = self.progress_manager.get_pending_entries(limit=limit)

        if not pending_entries:
            logger.info("✓ All classes have been scraped!")
            # 索引ファイルを生成
            self._generate_index()
            return

        logger.info(f"Starting to scrape {len(pending_entries)} classes...")

        # スクレイピング実行
        failed_count = 0
        for entry in tqdm(pending_entries, desc="Scraping"):
            class_info = self.progress_manager.entry_to_class_info(entry)

            try:
                detail = self.scrape_class(class_info)
                self.save_class_markdown(detail)
                self.progress_manager.mark_completed(class_info.full_name)
            except KeyboardInterrupt:
                logger.warning("\nInterrupted by user. Progress has been saved.")
                break
            except Exception as e:
                logger.error(f"Failed to scrape {class_info.full_name}: {e}")
                failed_count += 1
                continue

        # 最終統計
        final_stats = self.progress_manager.get_statistics()
        logger.info("\n=== Scraping Session Summary ===")
        logger.info(f"Processed: {len(pending_entries) - failed_count} classes")
        logger.info(f"Failed: {failed_count} classes")
        logger.info(f"Overall progress: {final_stats['completed']}/{final_stats['total']} ({final_stats['progress_percentage']:.1f}%)")

        # 全て完了していれば索引生成
        if final_stats['pending'] == 0:
            logger.info("All classes completed! Generating index...")
            self._generate_index()

    def _generate_index(self):
        """索引ファイルを生成"""
        classes = self.fetch_class_list()
        index_md = self.generator.generate_index_markdown(classes)
        index_path = self.output_dir / "index.md"
        self.generator.save_markdown(index_md, index_path)
        logger.info(f"Index file generated: {index_path}")


# CLIコマンドに追加
@cli.command()
@click.option('--limit', type=int, default=None, help='処理する最大件数（未指定の場合は全て）')
@click.option('--reset', is_flag=True, help='進捗をリセットして最初から')
def scrape(limit, reset):
    """継続モードでスクレイピング（推奨）"""
    scraper = BakinDocumentationScraper()
    scraper.scrape_with_progress(limit=limit, force_init=reset)


@cli.command()
def status():
    """現在の進捗状況を表示"""
    scraper = BakinDocumentationScraper()

    if not scraper.progress_file.exists():
        click.echo("Progress file not found. Run 'scrape' to initialize.")
        return

    stats = scraper.progress_manager.get_statistics()

    click.echo("\n=== Scraping Progress ===")
    click.echo(f"Total classes: {stats['total']}")
    click.echo(f"Completed: {stats['completed']}")
    click.echo(f"Pending: {stats['pending']}")
    click.echo(f"Progress: {stats['progress_percentage']:.1f}%")
    click.echo()

    # プログレスバー表示
    bar_length = 50
    filled = int(bar_length * stats['completed'] / stats['total'])
    bar = '█' * filled + '░' * (bar_length - filled)
    click.echo(f"[{bar}] {stats['completed']}/{stats['total']}")
```

### 成功基準

#### 自動検証:
- [ ] scrapeコマンドが動作する: `python main.py scrape --limit 1`
- [ ] statusコマンドが動作する: `python main.py status`
- [ ] 進捗が正しく保存される

#### 手動検証:
- [ ] `--limit 5`で5件だけ処理できる
- [ ] 2回目の実行で続きから処理される
- [ ] Ctrl+Cで中断しても進捗が保存される
- [ ] 全件完了後に索引ファイルが生成される

---

## フェーズ7: 従来型CLIインターフェースの実装

### 概要
従来の一括処理コマンド（scrape-all等）を実装します。

### 変更内容

#### 1. src/cli.py
**ファイル**: `src/cli.py`
```python
"""
コマンドラインインターフェース
"""
import json
import logging
from pathlib import Path
from typing import List

import click
from tqdm import tqdm

from src.scraper import BakinScraper
from src.parser import BakinParser, ClassInfo, ClassDetail
from src.markdown_generator import MarkdownGenerator

logger = logging.getLogger(__name__)


class BakinDocumentationScraper:
    """メインスクレイパークラス"""

    def __init__(self, config_path: str = "config.yaml"):
        self.scraper = BakinScraper(config_path)
        self.parser = BakinParser()
        self.generator = MarkdownGenerator()
        self.config = self.scraper.config

        # 出力ディレクトリ
        self.output_dir = Path(self.config['output']['base_dir'])
        self.classes_dir = Path(self.config['output']['classes_dir'])
        self.namespaces_dir = Path(self.config['output']['namespaces_dir'])
        self.cache_file = Path(self.config['output']['class_list_cache'])

        # ディレクトリ作成
        self.output_dir.mkdir(exist_ok=True)
        self.classes_dir.mkdir(exist_ok=True)
        self.namespaces_dir.mkdir(exist_ok=True)

    def fetch_class_list(self, force: bool = False) -> List[ClassInfo]:
        """
        クラスリストを取得（キャッシュがあればそれを使用）

        Args:
            force: Trueの場合、キャッシュを無視して再取得

        Returns:
            ClassInfoのリスト
        """
        # キャッシュチェック
        if not force and self.cache_file.exists():
            logger.info(f"Loading class list from cache: {self.cache_file}")
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ClassInfo(**item) for item in data]

        # 新規取得
        logger.info("Fetching class list from annotated page...")
        soup = self.scraper.fetch_annotated_page()
        classes = self.parser.parse_annotated_page(soup)

        # キャッシュに保存
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump([vars(cls) for cls in classes], f, ensure_ascii=False, indent=2)

        logger.info(f"Saved class list to cache: {self.cache_file}")
        return classes

    def scrape_class(self, class_info: ClassInfo) -> ClassDetail:
        """
        個別クラスの情報をスクレイピング

        Args:
            class_info: 対象クラスの基本情報

        Returns:
            ClassDetail
        """
        soup = self.scraper.fetch_class_page(class_info.url)
        if not soup:
            raise Exception(f"Failed to fetch class page: {class_info.url}")

        detail = self.parser.parse_class_page(soup, class_info)
        return detail

    def save_class_markdown(self, detail: ClassDetail):
        """
        クラス情報をMarkdownとして保存

        Args:
            detail: ClassDetail
        """
        md_content = self.generator.generate_class_markdown(detail)
        filename = f"{detail.info.full_name}.md"
        filepath = self.classes_dir / filename

        self.generator.save_markdown(md_content, filepath)

    def scrape_all(self, force_refresh: bool = False):
        """
        すべてのクラスをスクレイピング

        Args:
            force_refresh: クラスリストを強制的に再取得
        """
        # クラスリストを取得
        classes = self.fetch_class_list(force=force_refresh)
        logger.info(f"Found {len(classes)} classes to scrape")

        # 各クラスをスクレイピング
        for class_info in tqdm(classes, desc="Scraping classes"):
            try:
                detail = self.scrape_class(class_info)
                self.save_class_markdown(detail)
            except Exception as e:
                logger.error(f"Failed to scrape {class_info.full_name}: {e}")
                continue

        # 索引ファイルを生成
        logger.info("Generating index file...")
        index_md = self.generator.generate_index_markdown(classes)
        index_path = self.output_dir / "index.md"
        self.generator.save_markdown(index_md, index_path)

        logger.info(f"✓ Scraping completed! Check {self.output_dir}")

    def scrape_by_name(self, class_name: str):
        """
        特定のクラス名でスクレイピング

        Args:
            class_name: クラスの完全修飾名
        """
        # クラスリストから検索
        classes = self.fetch_class_list()

        target = None
        for cls in classes:
            if cls.full_name == class_name or cls.name == class_name:
                target = cls
                break

        if not target:
            logger.error(f"Class not found: {class_name}")
            return

        logger.info(f"Scraping {target.full_name}...")
        detail = self.scrape_class(target)
        self.save_class_markdown(detail)
        logger.info(f"✓ Saved to {self.classes_dir / (target.full_name + '.md')}")


@click.group()
def cli():
    """RPG Developer Bakin ドキュメントスクレイパー"""
    pass


@cli.command()
@click.option('--force', is_flag=True, help='クラスリストを強制的に再取得')
def scrape_all(force):
    """すべてのクラスをスクレイピング"""
    scraper = BakinDocumentationScraper()
    scraper.scrape_all(force_refresh=force)


@cli.command()
@click.argument('class_name')
def scrape_class(class_name):
    """特定のクラスのみスクレイピング"""
    scraper = BakinDocumentationScraper()
    scraper.scrape_by_name(class_name)


@cli.command()
@click.option('--force', is_flag=True, help='キャッシュを無視して再取得')
def list_classes(force):
    """クラスリストを表示"""
    scraper = BakinDocumentationScraper()
    classes = scraper.fetch_class_list(force=force)

    # 名前空間ごとにグループ化
    namespaces = {}
    for cls in classes:
        ns = cls.namespace or "Global"
        if ns not in namespaces:
            namespaces[ns] = []
        namespaces[ns].append(cls)

    # 表示
    for ns in sorted(namespaces.keys()):
        click.echo(f"\n{ns}:")
        for cls in sorted(namespaces[ns], key=lambda x: x.name):
            click.echo(f"  - {cls.name} ({cls.type})")


if __name__ == '__main__':
    cli()
```

#### 2. main.py
**ファイル**: `main.py`
```python
"""
エントリーポイント
"""
from src.cli import cli

if __name__ == '__main__':
    cli()
```

### 成功基準

#### 自動検証:
- [ ] CLIが起動する: `python main.py --help`
- [ ] クラスリスト取得コマンドが動作する: `python main.py list-classes`
- [ ] 個別クラススクレイピングが動作する: `python main.py scrape-class "Yukar.Common.Rom.Cast"`

#### 手動検証:
- [ ] 進捗バーが表示される
- [ ] エラー時に適切なメッセージが表示される
- [ ] 生成されたMarkdownファイルが正しい場所に保存される
- [ ] 一括スクレイピングが完了する

**実装ノート**: このフェーズ完了後、手動で一括スクレイピングのテストを実行し、数クラス分のMarkdownが正しく生成されることを確認してから、全体のスクレイピングを実行してください。

---

## フェーズ8: エラーハンドリングとロバスト性の向上

### 概要
エラーハンドリング、ログ改善、リカバリー機能を追加します。

### 変更内容

#### 1. エラーハンドリングの追加
**ファイル**: `src/cli.py`（追加修正）

既存の`scrape_all`メソッドを以下のように改善：

```python
def scrape_all(self, force_refresh: bool = False, skip_existing: bool = True):
    """
    すべてのクラスをスクレイピング

    Args:
        force_refresh: クラスリストを強制的に再取得
        skip_existing: 既存のMarkdownファイルをスキップ
    """
    # クラスリストを取得
    classes = self.fetch_class_list(force=force_refresh)
    logger.info(f"Found {len(classes)} classes to scrape")

    # 失敗したクラスを記録
    failed_classes = []
    skipped_classes = []

    # 各クラスをスクレイピング
    for class_info in tqdm(classes, desc="Scraping classes"):
        # 既存ファイルチェック
        filepath = self.classes_dir / f"{class_info.full_name}.md"
        if skip_existing and filepath.exists():
            skipped_classes.append(class_info.full_name)
            continue

        try:
            detail = self.scrape_class(class_info)
            self.save_class_markdown(detail)
        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Failed to scrape {class_info.full_name}: {e}")
            failed_classes.append(class_info.full_name)
            continue

    # サマリー表示
    logger.info("\n=== Scraping Summary ===")
    logger.info(f"Total classes: {len(classes)}")
    logger.info(f"Skipped (already exists): {len(skipped_classes)}")
    logger.info(f"Failed: {len(failed_classes)}")
    logger.info(f"Successfully scraped: {len(classes) - len(skipped_classes) - len(failed_classes)}")

    if failed_classes:
        logger.warning(f"Failed classes:\n" + "\n".join(failed_classes))

        # 失敗リストを保存
        failed_list_path = self.output_dir / "failed_classes.txt"
        with open(failed_list_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(failed_classes))
        logger.info(f"Failed classes list saved to: {failed_list_path}")

    # 索引ファイルを生成
    logger.info("Generating index file...")
    index_md = self.generator.generate_index_markdown(classes)
    index_path = self.output_dir / "index.md"
    self.generator.save_markdown(index_md, index_path)

    logger.info(f"✓ Scraping completed! Check {self.output_dir}")
```

#### 2. リトライコマンドの追加
**ファイル**: `src/cli.py`（追加）

```python
@cli.command()
def retry_failed():
    """失敗したクラスを再スクレイピング"""
    scraper = BakinDocumentationScraper()

    failed_list_path = scraper.output_dir / "failed_classes.txt"
    if not failed_list_path.exists():
        click.echo("No failed classes found.")
        return

    with open(failed_list_path, 'r', encoding='utf-8') as f:
        failed_names = [line.strip() for line in f if line.strip()]

    click.echo(f"Retrying {len(failed_names)} failed classes...")

    all_classes = scraper.fetch_class_list()

    for class_name in tqdm(failed_names, desc="Retrying"):
        target = None
        for cls in all_classes:
            if cls.full_name == class_name:
                target = cls
                break

        if not target:
            logger.warning(f"Class not found in list: {class_name}")
            continue

        try:
            detail = scraper.scrape_class(target)
            scraper.save_class_markdown(detail)
        except Exception as e:
            logger.error(f"Still failing {class_name}: {e}")
```

#### 3. CLIオプションの追加
**ファイル**: `src/cli.py`（修正）

```python
@cli.command()
@click.option('--force', is_flag=True, help='クラスリストを強制的に再取得')
@click.option('--no-skip', is_flag=True, help='既存ファイルを上書き')
def scrape_all(force, no_skip):
    """すべてのクラスをスクレイピング"""
    scraper = BakinDocumentationScraper()
    scraper.scrape_all(force_refresh=force, skip_existing=not no_skip)
```

### 成功基準

#### 自動検証:
- [ ] 既存ファイルスキップ機能が動作する
- [ ] 失敗リストが正しく保存される
- [ ] リトライコマンドが動作する: `python main.py retry-failed`

#### 手動検証:
- [ ] ネットワークエラー時に適切にリトライされる
- [ ] Ctrl+Cで中断しても途中までの成果が保存されている
- [ ] サマリーが正しく表示される

---

## テスト戦略

### 単体テスト
各モジュールの主要機能に対して単体テストを作成します（オプション）：
- `test_scraper.py`: HTTP取得とリトライのテスト
- `test_parser.py`: HTMLパース機能のテスト
- `test_markdown_generator.py`: Markdown生成のテスト

### 統合テスト
1. **小規模テスト**: 1〜2クラスのみスクレイピングして全体の流れを確認
2. **中規模テスト**: 特定の名前空間（例：Yukar.Common.Rom）のみ取得
3. **全体テスト**: 全クラスのスクレイピング

### 手動検証
- 生成されたMarkdownをAI（Claude、GPTなど）に読み込ませて理解できるか確認
- 継承情報が正しく抽出されているか目視確認
- 主要クラス（Cast、Monster、Itemなど）のMarkdownが完全か確認

---

## パフォーマンス考慮事項

### スクレイピング速度
- **ディレイ設定**: デフォルト1秒（config.yaml で調整可能）
- **推定時間**: 200クラス × 1秒 = 約3〜4分（リトライ含む）
- **並列化**: 現状は逐次実行（将来的にはマルチスレッド化可能）

### ファイルサイズ
- **1クラスあたり**: 約5〜20KB（テキスト）
- **全体**: 約2〜5MB（200クラス想定）

### メモリ使用量
- BeautifulSoupが1ページあたり数MBを使用
- 逐次処理なので大きなメモリは不要（推定最大100MB程度）

---

## 使用例

### 基本的な使い方（継続モード - 推奨）

```bash
# 1. 依存関係のインストール
pip install -r requirements.txt

# 2. 初回実行：最初の10件を取得（progress.csvが自動生成される）
python main.py scrape --limit 10

# 3. 進捗確認
python main.py status

# 4. さらに10件を取得（続きから自動的に処理される）
python main.py scrape --limit 10

# 5. 残り全てを取得
python main.py scrape

# 6. 特定のクラスをテスト取得
python main.py scrape-class "Yukar.Common.Rom.Cast"
```

### 従来の一括取得方法

```bash
# 全クラスを一括取得（progress.csvを使わない）
python main.py scrape-all

# 既存ファイルも上書きして再取得
python main.py scrape-all --no-skip

# 失敗したクラスのリトライ
python main.py retry-failed
```

### 上級者向け

```bash
# 進捗をリセットして最初から
python main.py scrape --reset

# 進捗をリセットして最初の5件だけ
python main.py scrape --reset --limit 5

# クラスリストのみ表示
python main.py list-classes
```

---

## 継続モードの利点

継続モード（`scrape`コマンド）を使用することで、以下の利点があります：

1. **安全性**: 少しずつ動作確認しながら進められる
2. **中断可能**: いつでもCtrl+Cで中断し、後で続きから再開できる
3. **可視性**: progress.csvで進捗を確認できる（ExcelやLibreOfficeで開ける）
4. **柔軟性**: `--limit`で処理件数を調整できる
5. **失敗に強い**: 一部失敗しても続きから再開できる

### progress.csvの例

```csv
full_name,name,url,type,namespace,description,completed,last_updated
Yukar.Common.Rom.Cast,Cast,class_yukar_1_1_common_1_1_rom_1_1_cast.html,class,Yukar.Common.Rom,キャラクタ定義,True,2025-11-01T10:30:45
Yukar.Common.Rom.Monster,Monster,class_yukar_1_1_common_1_1_rom_1_1_monster.html,class,Yukar.Common.Rom,モンスター定義,False,
```

## 今後の拡張可能性

以下は将来的に追加できる機能です（今回のスコープ外）：
- 名前空間ごとのまとめページ生成
- 全文検索機能
- Markdownのベクトル化（RAG用）
- 定期的な更新スクリプト
- 並列ダウンロード（マルチスレッド化）
- GUI版ツール
- GitHub Actionsでの自動更新
- 失敗したクラスのみリトライする機能（progress.csvベース）

---

## 参照情報

- **対象ドキュメント**: https://rpgbakin.com/csreference/doc/ja/
- **Doxygen**: ドキュメント生成ツール（バージョン1.9.4）
- **BeautifulSoup**: https://www.crummy.com/software/BeautifulSoup/
- **Click**: https://click.palletsprojects.com/

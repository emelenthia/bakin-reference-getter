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

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        指定されたURLからHTMLを取得してBeautifulSoupオブジェクトを返す
        ローカルキャッシュがあればそこから読み込む

        Args:
            url: 取得するURL（相対パスまたは絶対パス）

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        # 相対パスの場合はベースURLと結合
        full_url = url if url.startswith('http') else f"{self.base_url}/{url}"

        # URLからファイル名を抽出
        filename = url.split('/')[-1] if '/' in url else url
        cache_dir = Path("html")
        cache_file = cache_dir / filename

        # キャッシュファイルが存在する場合はそこから読み込む
        if cache_file.exists():
            logger.info(f"Loading from cache: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
                return BeautifulSoup(content, 'html.parser')

        # キャッシュがない場合はWebから取得
        logger.info(f"Fetching from web: {full_url}")
        soup = self._fetch_from_web(full_url)

        # キャッシュディレクトリを作成
        cache_dir.mkdir(exist_ok=True)

        # キャッシュに保存
        if soup:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            logger.info(f"Saved to cache: {cache_file}")

        return soup

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def _fetch_from_web(self, url: str) -> Optional[BeautifulSoup]:
        """
        Webから直接HTMLを取得（リトライ機構付き）

        Args:
            url: 取得するURL（完全なURL）

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # ディレイを入れる（サーバーに負荷をかけないため）
            time.sleep(self.delay)

            soup = BeautifulSoup(response.content, 'html.parser')
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


if __name__ == '__main__':
    # テスト実行
    print("Testing BakinScraper...")
    scraper = BakinScraper()

    print(f"Base URL: {scraper.base_url}")

    print("Fetching annotated page...")
    soup = scraper.fetch_annotated_page()

    if soup and soup.title:
        print("OK: Scraper test passed!")
    else:
        print("FAIL: Failed to fetch page")

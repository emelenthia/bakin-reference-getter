"""
コマンドラインインターフェース
"""
import json
import logging
from pathlib import Path
from typing import List, Optional

import click
from tqdm import tqdm

from src.scraper import BakinScraper
from src.parser import BakinParser, ClassInfo, ClassDetail
from src.markdown_generator import MarkdownGenerator
from src.progress_manager import ProgressManager

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

        # 進捗管理
        self.progress_file = Path(self.config['output']['progress_file'])
        self.progress_manager = ProgressManager(self.progress_file)

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
            logger.info("All classes have been scraped!")
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


@click.group()
def cli():
    """RPG Developer Bakin ドキュメントスクレイパー"""
    pass


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
    if stats['total'] > 0:
        filled = int(bar_length * stats['completed'] / stats['total'])
        bar = '#' * filled + '-' * (bar_length - filled)
        click.echo(f"[{bar}] {stats['completed']}/{stats['total']}")


if __name__ == '__main__':
    cli()

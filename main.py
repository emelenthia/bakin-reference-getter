"""
エントリーポイント
"""
from pathlib import Path
import yaml
from src.scraper import BakinScraper
from src.parser import BakinParser
from src.markdown_generator import MarkdownGenerator
from src.progress_manager import ProgressManager

def main():
    print("Bakin Documentation Scraper")
    print("=" * 50)

    # 設定読み込み
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    scraper = BakinScraper()
    parser = BakinParser()
    generator = MarkdownGenerator()

    # annotated.htmlから全クラスリストを取得
    print("\n[1/3] Fetching class list...")
    soup = scraper.fetch_annotated_page()
    classes = parser.parse_annotated_page(soup)
    print(f"  Found {len(classes)} classes")

    # 索引ファイルを生成
    print("\n[2/3] Generating index...")
    index_md = generator.generate_index_markdown(classes)
    index_path = Path("output/index.md")
    generator.save_markdown(index_md, index_path)
    print(f"  Saved: {index_path}")

    # progress.csvを生成
    print("\n[3/3] Initializing progress.csv...")
    progress_file = Path(config['output']['progress_file'])
    pm = ProgressManager(progress_file)
    pm.initialize_from_class_list(classes)
    print(f"  Saved: {progress_file}")

    print("\nDone!")

if __name__ == '__main__':
    main()
